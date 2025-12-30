import math

class SystemeFlouFatigue:
    def __init__(self):
        # 1. Définition des Univers (espace linéaire approximatif)
        # Utilisation de 100 étapes pour la résolution
        self.x_ear = [i * (0.6 / 100.0) for i in range(101)]       # EAR (Eye Aspect Ratio) : 0 à 0.6
        self.x_baillement = [i * (10.0 / 100.0) for i in range(101)] # Fréquence de bâillement : 0 à 10 par minute
        self.x_clignement = [i * (20.0 / 100.0) for i in range(101)] # Fréquence de clignement lent : 0 à 20 par minute
        self.x_vigilance = [i for i in range(101)] # Vigilance : 0 à 100%

    # --- Fonctions Mathématiques Utilitaires ---
    def interpolation(self, x, xp, fp):
        """Interpolation linéaire en Python pur, similaire à np.interp"""
        if x < xp[0]: return fp[0]
        if x > xp[-1]: return fp[-1]
        
        for i in range(len(xp) - 1):
            if xp[i] <= x <= xp[i+1]:
                ratio = (x - xp[i]) / (xp[i+1] - xp[i]) if (xp[i+1] - xp[i]) != 0 else 0
                return fp[i] + ratio * (fp[i+1] - fp[i])
        return fp[-1]

    def appartenance_triangulaire(self, x, abc):
        """Fonction d'appartenance triangulaire pour un scalaire x"""
        a, b, c = abc
        if x < a or x > c: return 0.0
        if a <= x <= b:
            return (x - a) / (b - a) if b != a else 1.0
        if b < x <= c:
            return (c - x) / (c - b) if c != b else 1.0
        return 0.0

    def appartenance_trapezoidale(self, x, abcd):
        """Fonction d'appartenance trapézoïdale pour un scalaire x"""
        a, b, c, d = abcd
        if x < a or x > d: return 0.0
        if a <= x <= b:
            # Montée
            return (x - a) / (b - a) if b != a else 1.0
        if b <= x <= c:
            # Plateau
            return 1.0
        if c < x <= d:
            # Descente
            return (d - x) / (d - c) if d != c else 1.0
        return 0.0

    # --- CALCULATEURS D'APPARTENANCE DES ANTÉCÉDENTS ---
    
    # EAR (Ratio d'Aspect de l'Oeil)
    def mu_ear_ferme(self, x):
        return self.appartenance_trapezoidale(x, [0.0, 0.0, 0.15, 0.19])

    def mu_ear_fatigue(self, x):
        # Réduction légère (0.35 -> 0.29) pour que à 0.30 on soit sûr d'être "Réveillé"
        # On garde quand même un chevauchement avec "Ouvert" (qui commence à 0.22)
        return self.appartenance_triangulaire(x, [0.17, 0.25, 0.29]) 

    def mu_ear_ouvert(self, x):
        # Elargissement vers la gauche (jusqu'à 0.22) pour ne pas couper "Alerte" trop vite
        # Plateau à partir de 0.24 (au lieu de 0.26) pour garantir le 100% encore plus vite
        return self.appartenance_trapezoidale(x, [0.22, 0.24, 0.6, 0.6])

    # Fréquence de Bâillement - Plus fin pour des pas de ~10%
    def mu_baillement_nul(self, x):
        # "Nul" = 0-1 bâillements
        return self.appartenance_trapezoidale(x, [0, 0, 1, 2])
    
    def mu_baillement_rare(self, x):
        # "Rare" = 1-4 bâillements (pic à 2)
        return self.appartenance_triangulaire(x, [1, 2, 4])
    
    def mu_baillement_frequent(self, x):
        # On réduit le chevauchement : "Fréquent" grimpe très vite après 3
        # On utilise une pente raide pour dominer l'univers
        return self.appartenance_trapezoidale(x, [3.5, 4.0, 1000, 1000])

    # Fréquence de Clignement Lent - Plus fin pour des pas de ~10%
    def mu_clignement_normal(self, x):
        # Ne reste "Normal" que jusqu'à 1 clignement
        return self.appartenance_trapezoidale(x, [0, 0, 0, 2])
    
    def mu_clignement_inquietant(self, x):
        # "Inquiétant" = 1-4 clignements (pic à 2)
        return self.appartenance_trapezoidale(x, [1, 2, 3, 5])
        
    def mu_clignement_critique(self, x):
        # "Critique" dès 4 clignements
        return self.appartenance_trapezoidale(x, [4, 6, 1000, 1000])

    # --- DÉFINITIONS D'APPARTENANCE DES CONSÉQUENTS (Vigilance) ---
    def mu_vigilance_danger(self, x):
        # On déplace le pic vers 0 pour que le centroïde soit très bas
        # Triangle [0, 0, 30]
        return self.appartenance_triangulaire(x, [0, 0, 30])
    
    def mu_vigilance_somnolence(self, x):
        # Triangle [20, 50, 70]
        return self.appartenance_triangulaire(x, [20, 50, 70])
    
    def mu_vigilance_alerte(self, x):
        # Triangle [60, 100, 100]
        return self.appartenance_triangulaire(x, [60, 100, 100])

    def calculer(self, valeur_ear, valeur_baillement, valeur_clignement=0):
        """
        Calcule le score de vigilance.
        EAR doit être approx 0.0 - 0.5
        Bâillement doit être approx 0 - 10
        Clignement doit être approx 0 - 20 (Clignements lents)
        Retourne la Vigilance (0-100)
        """
        
        # 1. Fuzzification des Entrées (Calcul de l'appartenance partielle)
        e_ferme = self.mu_ear_ferme(valeur_ear)
        e_fatigue = self.mu_ear_fatigue(valeur_ear)
        e_ouvert = self.mu_ear_ouvert(valeur_ear)
        
        b_nul = self.mu_baillement_nul(valeur_baillement)
        b_rare = self.mu_baillement_rare(valeur_baillement)
        b_frequent = self.mu_baillement_frequent(valeur_baillement)

        c_normal = self.mu_clignement_normal(valeur_clignement)
        c_inquietant = self.mu_clignement_inquietant(valeur_clignement)
        c_critique = self.mu_clignement_critique(valeur_clignement)

        # 2. Application des Règles (Calcul des niveaux d'activation)
        # R1: SI EAR="Fermé" -> Danger
        r1 = e_ferme 

        # R2: SI EAR="Fatigué" ET Bâillement="Fréquent" -> Danger
        r2 = min(e_fatigue, b_frequent)

        # R3: SI EAR="Fatigué" ET (Bâillement="Rare" OU Bâillement="Nul") -> Somnolence
        r3 = min(e_fatigue, max(b_rare, b_nul))

        # R4: SI EAR="Ouvert" ET Bâillement="Fréquent" -> Danger
        r4 = min(e_ouvert, b_frequent)

        # R5: SI EAR="Ouvert" ET Bâillement="Rare" -> Somnolence
        r5 = min(e_ouvert, b_rare)

        # R6: SI EAR="Ouvert" ET Bâillement="Nul" ET Clignement="Normal" -> Alerte
        # C'est la règle "Tout va bien". Elle requiert maintenant explicitement des clignements normaux.
        r6 = min(e_ouvert, b_nul, c_normal)
        
        # R7: SI Clignement Lent = Critique -> Danger
        r7 = c_critique
        
        # R8: SI Clignement Lent = Inquiétant -> SOMNOLENCE
        r8 = c_inquietant
        
        # R9 (Synergie): SI Clignement = Inquietant ET Bâillement = Fréquent -> DANGER
        # Seulement l'accumulation SEVERE des deux symptômes aggrave le diagnostic
        r9 = min(c_inquietant, b_frequent)

        # --- DANGER ---
        # Active si R1, R2, R4, R7, R9
        act_danger = max(r1, r2, r4, r7, r9)
        
        # --- SOMNOLENCE ---
        # INHIBITION RADICALE : La somnolence s'efface COMPLÈTEMENT dès que le danger est significatif
        # Cela empêche le centroïde de remonter
        brut_somnolence = max(r3, r5, r8)
        act_somnolence = brut_somnolence * (1.0 - act_danger)
        
        # --- ALERTE ---
        # INHIBITION RADICALE : L'alerte s'efface devant tout signe de fatigue
        act_alerte = r6 * (1.0 - act_somnolence) * (1.0 - act_danger)
        
        # 4. Défuzzification (Centroïde)
        numerateur = 0.0
        denominateur = 0.0
        
        for x_val in self.x_vigilance:
            # Calcul de l'appartenance dans chaque ensemble de sortie pour ce x_val
            mu_d = self.mu_vigilance_danger(x_val)
            mu_s = self.mu_vigilance_somnolence(x_val)
            mu_a = self.mu_vigilance_alerte(x_val)
            
            # Écrêtage par le niveau d'activation
            c_d = min(mu_d, act_danger)
            c_s = min(mu_s, act_somnolence)
            c_a = min(mu_a, act_alerte)
            
            # Union (Max)
            mu_agrege = max(c_d, max(c_s, c_a))
            
            numerateur += x_val * mu_agrege
            denominateur += mu_agrege
            
        if denominateur == 0:
            return 50.0 # Valeur par défaut si aucune règle n'est activée
        
        # Calcul du score brut (Centroïde)
        score_brut = numerateur / denominateur
        
        # CALIBRAGE (Mapping linéaire vers 0-100)
        # On mappe [14, 86] -> [0, 100] pour être sûr d'atteindre les extrêmes
        min_in = 14.0
        max_in = 86.0
        
        score_calibre = (score_brut - min_in) * (100.0 / (max_in - min_in))
        
        # Bornage (Clamping) entre 0 et 100
        score_calibre = max(0.0, min(100.0, score_calibre))
        
        return score_calibre

    def obtenir_etiquette_etat(self, score):
        """
        Retourne un tuple (état, recommandation) adapté aux systèmes automobiles.
        """
        if score < 30:
            return ("ARRET IMMEDIAT", "Arretez-vous immediatement dans un lieu sur.")
        elif score < 50:
            return ("PAUSE RECOMMANDEE", "Faites une pause des que possible.")
        elif score < 70:
            return ("VIGILANCE EN BAISSE", "Pensez a prendre un cafe ou aerer.")
        else:
            return ("CONDUITE NORMALE", "Vigilance correcte.")
