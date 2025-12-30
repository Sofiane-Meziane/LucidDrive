
def simulate_subtractive_inhibition(act_danger, act_somnolence, act_alerte):
    # Inhibition de type soustraction
    act_somnolence = max(0.0, act_somnolence - act_danger)
    act_alerte = max(0.0, act_alerte - act_somnolence - act_danger)
    return act_danger, act_somnolence, act_alerte

def mock_centroid(d, s, a):
    # Mock simple du centroïde : 10 pour Danger, 50 pour Somnolence, 90 pour Alerte
    # Calibré à l'arrache pour voir la tendance
    num = (d * 10) + (s * 50) + (a * 90)
    den = d + s + a
    if den == 0: return 50
    return num / den

print("--- Mock Subtractive Inhibition ---")

# Cas 1: 4 Baillements (Danger 0.5, Somnolence 0)
d, s, a = simulate_subtractive_inhibition(0.5, 0.0, 0.5) # Alerte 0.5 car EAR ouvert
score1 = mock_centroid(d, s, a)
print(f"4 Baillements -> D:{d}, S:{s}, A:{a} -> Score: {score1}")

# Cas 2: 4 Baillements + 2 Clignements (Danger 0.5, Somnolence 0.5, Alerte 0.5)
# R8 donne Somnolence 0.5, R4/R9 donnent Danger 0.5
d2, s2, a2 = simulate_subtractive_inhibition(0.5, 0.5, 0.5)
score2 = mock_centroid(d2, s2, a2)
print(f"4 Baillements + 2 Clignements -> D:{d2}, S:{s2}, A:{a2} -> Score: {score2}")

if score2 <= score1:
    print("SUCCESS: Monotonicity preserved!")
else:
    print("FAILURE: Score increased!")
