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
    
    # EAR (Ratio d'Aspect de l'Oeil) - Chevauchement amélioré pour transitions fluides
    def mu_ear_ferme(self, x):
        # Yeux fermés : EAR < 0.20
        return self.appartenance_trapezoidale(x, [0.0, 0.0, 0.15, 0.22])

    def mu_ear_fatigue(self, x):
        # Yeux mi-clos/fatigués : EAR entre 0.18 et 0.30
        # Chevauchement étendu pour transitions fluides
        return self.appartenance_triangulaire(x, [0.18, 0.24, 0.32])

    def mu_ear_ouvert(self, x):
        # Yeux bien ouverts : EAR > 0.26
        # Plateau dès 0.30 pour qu'un EAR normal (0.30-0.35) donne 100% d'appartenance
        return self.appartenance_trapezoidale(x, [0.26, 0.30, 0.6, 0.6])

    # Fréquence de Bâillement - Chevauchement progressif
    def mu_baillement_nul(self, x):
        # "Nul" = 0 bâillement, décroît jusqu'à 2
        return self.appartenance_trapezoidale(x, [0, 0, 0.5, 2])
    
    def mu_baillement_rare(self, x):
        # "Rare" = 1-3 bâillements (pic à 2)
        return self.appartenance_triangulaire(x, [0.5, 2, 4])
    
    def mu_baillement_modere(self, x):
        # "Modéré" = 2-5 bâillements (pic à 3.5) - NOUVEL ENSEMBLE
        return self.appartenance_triangulaire(x, [2, 3.5, 5])
    
    def mu_baillement_frequent(self, x):
        # "Fréquent" = > 4 bâillements
        return self.appartenance_trapezoidale(x, [4, 6, 1000, 1000])

    # Fréquence de Clignement Lent - Chevauchement progressif
    def mu_clignement_normal(self, x):
        # Normal jusqu'à 2 clignements lents
        return self.appartenance_trapezoidale(x, [0, 0, 1, 3])
    
    def mu_clignement_leger(self, x):
        # Légèrement élevé : 1-4 clignements - NOUVEL ENSEMBLE
        return self.appartenance_triangulaire(x, [1, 2.5, 4])
    
    def mu_clignement_inquietant(self, x):
        # "Inquiétant" = 3-6 clignements (pic à 4)
        return self.appartenance_triangulaire(x, [3, 4.5, 6])
        
    def mu_clignement_critique(self, x):
        # "Critique" >= 5 clignements
        return self.appartenance_trapezoidale(x, [5, 7, 1000, 1000])

    # --- DÉFINITIONS D'APPARTENANCE DES CONSÉQUENTS (Vigilance) ---
    # 4 ENSEMBLES pour correspondre aux 4 états du tableau
    
    def mu_vigilance_danger(self, x):
        # ARRÊT IMMÉDIAT : Score 0-30
        # Plateau de 0 à 10 pour garantir un centroïde proche de 0
        return self.appartenance_trapezoidale(x, [0, 0, 10, 30])
    
    def mu_vigilance_fatigue_forte(self, x):
        # PAUSE RECOMMANDÉE : Score 30-50, centroïde ~40
        return self.appartenance_triangulaire(x, [20, 40, 55])
    
    def mu_vigilance_fatigue_legere(self, x):
        # VIGILANCE EN BAISSE : Score 50-70, centroïde ~60
        return self.appartenance_triangulaire(x, [45, 60, 75])
    
    def mu_vigilance_alerte(self, x):
        # CONDUITE NORMALE : Score 70-100
        # Plateau de 90 à 100 pour garantir un centroïde proche de 100
        return self.appartenance_trapezoidale(x, [65, 90, 100, 100])

    def calculer(self, valeur_ear, valeur_baillement, valeur_clignement=0):
        """
        Calcule le score de vigilance avec transitions fluides.
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
        b_modere = self.mu_baillement_modere(valeur_baillement)
        b_frequent = self.mu_baillement_frequent(valeur_baillement)

        c_normal = self.mu_clignement_normal(valeur_clignement)
        c_leger = self.mu_clignement_leger(valeur_clignement)
        c_inquietant = self.mu_clignement_inquietant(valeur_clignement)
        c_critique = self.mu_clignement_critique(valeur_clignement)

        # 2. Application des Règles - SYSTÈME GRADUÉ pour transitions fluides
        # ==================================================================
        
        # === RÈGLES POUR ALERTE (CONDUITE NORMALE - 70-100%) ===
        # R1: Yeux ouverts + pas de bâillement + clignements normaux -> ALERTE
        r_alerte_1 = min(e_ouvert, b_nul, c_normal)
        # R2: Yeux ouverts + bâillements rares + clignements normaux -> ALERTE (légère baisse)
        r_alerte_2 = min(e_ouvert, b_rare, c_normal) * 0.8
        
        # === RÈGLES POUR FATIGUE LÉGÈRE (VIGILANCE EN BAISSE - 50-70%) ===
        # R3: Yeux ouverts + bâillements rares -> Fatigue légère
        r_fatigue_legere_1 = min(e_ouvert, b_rare)
        # R4: Yeux ouverts + clignements légers -> Fatigue légère
        r_fatigue_legere_2 = min(e_ouvert, c_leger)
        # R5: Yeux fatigués + pas de bâillement -> Fatigue légère
        r_fatigue_legere_3 = min(e_fatigue, b_nul)
        # R6: Bâillements modérés seuls -> Fatigue légère
        r_fatigue_legere_4 = b_modere * 0.7
        
        # === RÈGLES POUR FATIGUE FORTE (PAUSE RECOMMANDÉE - 30-50%) ===
        # R7: Yeux fatigués + bâillements rares/modérés -> Fatigue forte
        r_fatigue_forte_1 = min(e_fatigue, max(b_rare, b_modere))
        # R8: Yeux ouverts + bâillements modérés -> Fatigue forte
        r_fatigue_forte_2 = min(e_ouvert, b_modere)
        # R9: Clignements inquiétants seuls -> Fatigue forte
        r_fatigue_forte_3 = c_inquietant * 0.8
        # R10: Yeux fatigués + clignements légers -> Fatigue forte
        r_fatigue_forte_4 = min(e_fatigue, c_leger)
        
        # === RÈGLES POUR DANGER (ARRÊT IMMÉDIAT - 0-30%) ===
        # R11: Yeux fermés -> DANGER
        r_danger_1 = e_ferme
        # R12: Yeux fatigués + bâillements fréquents -> DANGER
        r_danger_2 = min(e_fatigue, b_frequent)
        # R13: Yeux ouverts + bâillements fréquents -> DANGER
        r_danger_3 = min(e_ouvert, b_frequent)
        # R14: Clignements critiques -> DANGER
        r_danger_4 = c_critique
        # R15: Yeux fatigués + clignements inquiétants -> DANGER
        r_danger_5 = min(e_fatigue, c_inquietant)
        # R16: Bâillements fréquents + clignements inquiétants -> DANGER
        r_danger_6 = min(b_frequent, c_inquietant)
        
        # 3. Agrégation des niveaux d'activation (sans inhibition agressive)
        act_alerte = max(r_alerte_1, r_alerte_2)
        act_fatigue_legere = max(r_fatigue_legere_1, r_fatigue_legere_2, 
                                  r_fatigue_legere_3, r_fatigue_legere_4)
        act_fatigue_forte = max(r_fatigue_forte_1, r_fatigue_forte_2,
                                 r_fatigue_forte_3, r_fatigue_forte_4)
        act_danger = max(r_danger_1, r_danger_2, r_danger_3, 
                         r_danger_4, r_danger_5, r_danger_6)
        
        # 4. Défuzzification (Centroïde) avec 4 ensembles
        numerateur = 0.0
        denominateur = 0.0
        
        for x_val in self.x_vigilance:
            # Calcul de l'appartenance dans chaque ensemble de sortie
            mu_d = self.mu_vigilance_danger(x_val)
            mu_ff = self.mu_vigilance_fatigue_forte(x_val)
            mu_fl = self.mu_vigilance_fatigue_legere(x_val)
            mu_a = self.mu_vigilance_alerte(x_val)
            
            # Écrêtage par le niveau d'activation
            c_d = min(mu_d, act_danger)
            c_ff = min(mu_ff, act_fatigue_forte)
            c_fl = min(mu_fl, act_fatigue_legere)
            c_a = min(mu_a, act_alerte)
            
            # Union (Max) de tous les ensembles
            mu_agrege = max(c_d, c_ff, c_fl, c_a)
            
            numerateur += x_val * mu_agrege
            denominateur += mu_agrege
            
        if denominateur == 0:
            return 100.0  # Valeur par défaut = Conduite normale (tout va bien)
        
        # Calcul du score brut (Centroïde)
        score_brut = numerateur / denominateur
        
        # CALIBRAGE : Le centroïde produit des valeurs entre ~10 et ~88
        # On mappe cette plage vers [0, 100] pour couvrir tous les états
        min_centroide = 10.0   # Centroïde minimal (danger maximal)
        max_centroide = 88.0   # Centroïde maximal (alerte maximale)
        
        # Mapping linéaire
        score = (score_brut - min_centroide) / (max_centroide - min_centroide) * 100.0
        
        # Bornage (Clamping) entre 0 et 100
        score = max(0.0, min(100.0, score))
        
        return score

    def obtenir_etiquette_etat(self, score):
        """
        Retourne un tuple (état, recommandation) adapté aux systèmes automobiles.
        Score (%)   | État                  | Recommandation
        70-100      | CONDUITE NORMALE      | Vigilance correcte
        50-70       | VIGILANCE EN BAISSE   | Pensez à un café ou aerez
        30-50       | PAUSE RECOMMANDEE     | Faites une pause des que possible
        0-30        | ARRET IMMEDIAT        | Arretez-vous immediatement
        """
        if score < 30:
            return ("ARRET IMMEDIAT", "Arretez-vous immediatement")
        elif score < 50:
            return ("PAUSE RECOMMANDEE", "Faites une pause des que possible")
        elif score < 70:
            return ("VIGILANCE EN BAISSE", "Pensez a un cafe ou aerez")
        else:
            return ("CONDUITE NORMALE", "Vigilance correcte")
