from logique_floue import SystemeFlouFatigue

def test_stability():
    sf = SystemeFlouFatigue()
    ear = 0.35
    
    print("--- Test de Stabilité et Récupération ---")
    
    # 1. État initial (Alert)
    s0 = sf.calculer(ear, 0, 0)
    print(f"Initial (0,0) -> Score: {s0:.2f}%")
    
    # 2. Bruit : Un seul clignement inquietant (Normalement Somnolence légère)
    s1 = sf.calculer(ear, 0, 2)
    print(f"Bruit (0,2) -> Score: {s1:.2f}%")
    
    # 3. Récupération : Retour à 0 clignements
    s2 = sf.calculer(ear, 0, 0)
    print(f"Récupération (0,0) -> Score: {s2:.2f}%")
    
    if s2 > s1:
        print("SUCCÈS : Le système a récupéré du bruit.")
    else:
        print("ÉCHEC : Le score est resté bloqué.")

    print("\n--- Test de Transition Fatigue ---")
    
    # 4. 4 Baillements (Danger)
    s_d1 = sf.calculer(ear, 4, 0)
    print(f"4 Baillements -> Score: {s_d1:.2f}%")
    
    # 5. 4 Baillements + 2 Clignements (Danger + Somnolence)
    # On veut que ça ne remonte pas par rapport à s_d1
    s_d2 = sf.calculer(ear, 4, 2)
    print(f"4 Baillements + 2 Clignements -> Score: {s_d2:.2f}%")
    
    if s_d2 <= s_d1 + 0.1: # Petite marge de précision float
        print("SUCCÈS : Le score n'a pas remonté malgré l'indicateur de somnolence.")
    else:
        print(f"ÉCHEC : Le score a remonté de {s_d2 - s_d1:.2f}% !")

if __name__ == "__main__":
    test_stability()
