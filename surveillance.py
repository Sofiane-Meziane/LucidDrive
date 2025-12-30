import cv2
import mediapipe as mp
import math
import time
from logique_floue import SystemeFlouFatigue

# Initialisation du maillage facial MediaPipe (Face Mesh)
mp_maillage_visage = mp.solutions.face_mesh
maillage_visage = mp_maillage_visage.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    refine_landmarks=True
)

# Contrôleur Logique Floue
systeme_flou = SystemeFlouFatigue()

# Constantes
SEUIL_MAR_BAILLEMENT = 0.45  # MAR > 0.45 indique un bâillement
YAWN_COOLDOWN = 1.5           # Secondes de repos entre deux bâillements pour éviter le double comptage

def calculer_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def obtenir_ear(points_referes, indices, largeur_cadre, hauteur_cadre):
    """
    Calcule le Ratio d'Aspect de l'Oeil (EAR).
    EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
    """
    # indices: [gauche, haut1, haut2, droit, bas2, bas1] 
    
    # Coordonnées
    coords = []
    for idx in indices:
        lm = points_referes[idx]
        coords.append([lm.x * largeur_cadre, lm.y * hauteur_cadre])
    
    # Distances Verticales
    v1 = calculer_distance(coords[1], coords[5])
    v2 = calculer_distance(coords[2], coords[4])
    
    # Distance Horizontale
    h = calculer_distance(coords[0], coords[3])
    
    if h == 0: return 0.0
    ear = (v1 + v2) / (2.0 * h)
    return ear

def obtenir_mar(points_referes, indices, largeur_cadre, hauteur_cadre):
    """
    Calcule le Ratio d'Aspect de la Bouche (MAR).
    MAR = |haut-bas| / |gauche-droit|
    """
    # Indices fixes pour MediaPipe :
    # Haut: 13, Bas: 14, Gauche: 61, Droite: 291
    
    haut = points_referes[13]
    bas = points_referes[14]
    gauche = points_referes[61]
    droit = points_referes[291]
    
    pt_haut = [haut.x * largeur_cadre, haut.y * hauteur_cadre]
    pt_bas = [bas.x * largeur_cadre, bas.y * hauteur_cadre]
    pt_gauche = [gauche.x * largeur_cadre, gauche.y * hauteur_cadre]
    pt_droit = [droit.x * largeur_cadre, droit.y * hauteur_cadre]
    
    v = calculer_distance(pt_haut, pt_bas)
    h = calculer_distance(pt_gauche, pt_droit)
    
    if h == 0: return 0.0
    return v / h

# Indices des points de repère (Landmarks)
# Oeil Gauche (P1, P2, P3, P4, P5, P6)
OEIL_GAUCHE = [33, 160, 158, 133, 153, 144]
# Oeil Droit
OEIL_DROIT = [362, 385, 387, 263, 373, 380]

# Suivi du bâillement
compteur_baillement = 0
est_en_train_de_bailler = False
horodatage_baillements = []
dernier_baillement_fini = 0

# Suivi du clignement (yeux fermés > 0.3s)
est_yeux_fermes = False
debut_fermeture = 0
horodatage_clignements = []
SEUIL_EAR_FERME = 0.20 # Seuil officiel pour considérer l'oeil fermé
DUREE_MIN_CLIGNEMENT_LENT = 0.30 # Secondes

cap = cv2.VideoCapture(0)

print("Démarrage de la surveillance... Appuyez sur ECHAP pour quitter.")

# Variable de lissage (EMA) - Initialisation hors de la boucle
ancien_score = 100.0
alpha_lissage = 0.15

while cap.isOpened():
    succes, image = cap.read()
    if not succes:
        print("Trame de caméra vide ignorée.")
        continue

    # Miroir horizontal (Vue Selfie)
    image = cv2.flip(image, 1)

    # Pour améliorer les performances, marquer l'image comme non-inscriptible pour le passage par référence
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    resultats = maillage_visage.process(image)

    # Dessiner les annotations du maillage facial sur l'image
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    h_img, w_img, c_img = image.shape
    
    score_vigilance = 0
    etat = "CALIBRAGE"
    moyenne_ear = 0.0
    mar = 0.0
    baillements_par_min = 0
    clignements_par_min = 0

    if resultats.multi_face_landmarks:
        for points_visage in resultats.multi_face_landmarks:
            points_referes = points_visage.landmark
            
            # Calculer EAR
            ear_gauche = obtenir_ear(points_referes, OEIL_GAUCHE, w_img, h_img)
            ear_droit = obtenir_ear(points_referes, OEIL_DROIT, w_img, h_img)
            moyenne_ear = (ear_gauche + ear_droit) / 2.0
            
            # --- LOGIQUE DE CLIGNEMENT LENT ---
            if moyenne_ear < SEUIL_EAR_FERME:
                if not est_yeux_fermes:
                    est_yeux_fermes = True
                    debut_fermeture = time.time()
            else:
                if est_yeux_fermes:
                    est_yeux_fermes = False
                    duree = time.time() - debut_fermeture
                    if duree > DUREE_MIN_CLIGNEMENT_LENT:
                        # C'est un clignement lent (signe de fatigue)
                        horodatage_clignements.append(time.time())
            
            # Nettoyer vieux clignements
            temps_actuel = time.time()
            horodatage_clignements = [t for t in horodatage_clignements if temps_actuel - t <= 60.0]
            clignements_par_min = len(horodatage_clignements)
            
            
            # Calculer MAR
            mar = obtenir_mar(points_referes, None, w_img, h_img)
            
            # Logique de Détection de Bâillement (avec anti-rebond)
            if mar > SEUIL_MAR_BAILLEMENT:
                if not est_en_train_de_bailler:
                    # Ne déclencher que si assez de temps s'est écoulé depuis le dernier bâillement
                    if temps_actuel - dernier_baillement_fini > YAWN_COOLDOWN:
                        est_en_train_de_bailler = True
                        horodatage_baillements.append(temps_actuel)
            else:
                if est_en_train_de_bailler:
                    est_en_train_de_bailler = False
                    dernier_baillement_fini = temps_actuel
            
            # Nettoyer les vieux bâillements (> 60s)
            horodatage_baillements = [t for t in horodatage_baillements if temps_actuel - t <= 60.0]
            baillements_par_min = len(horodatage_baillements)
            
            # Inférence Floue (Avec Clignements maintenant)
            score_brut = systeme_flou.calculer(moyenne_ear, baillements_par_min, clignements_par_min)
            
            # LISSAGE EXPONENTIEL (EMA)
            score_vigilance = alpha_lissage * score_brut + (1.0 - alpha_lissage) * ancien_score
            ancien_score = score_vigilance
            
            etat, recommandation = systeme_flou.obtenir_etiquette_etat(score_vigilance)
            
            # Visuels - Couleur selon le niveau
            couleur = (0, 255, 0) # Vert (Conduite Normale)
            if "VIGILANCE" in etat: couleur = (0, 200, 255) # Jaune
            if "PAUSE" in etat: couleur = (0, 165, 255) # Orange
            if "ARRET" in etat: couleur = (0, 0, 255) # Rouge
            
            # Affichage à l'écran - Style Automobile
            cv2.putText(image, f"{etat} ({int(score_vigilance)}%)", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, couleur, 2)
            cv2.putText(image, recommandation, (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, couleur, 1)
            cv2.putText(image, f"Baillements: {baillements_par_min} | Clignements Lents: {clignements_par_min}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.putText(image, f"EAR: {moyenne_ear:.2f} | MAR: {mar:.2f}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    cv2.imshow('Surveillance Vigilance Conducteur', image)
    if cv2.waitKey(5) & 0xFF == 27: # 27 est la touche Echap
        break

cap.release()
cv2.destroyAllWindows()
