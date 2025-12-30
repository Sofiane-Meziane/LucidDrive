# 🚗 Système de Surveillance de Vigilance Conducteur

Ce projet est un **système d'aide à la conduite** utilisant la logique floue pour évaluer en temps réel le niveau de vigilance d'un conducteur. Il analyse le visage via webcam et fournit des recommandations claires pour prévenir les accidents liés à la fatigue.

---

## 🏗️ Architecture du Système

### Fichiers Principaux
| Fichier | Rôle |
|---------|------|
| `surveillance.py` | Capture vidéo, détection faciale (MediaPipe), calcul des métriques |
| `logique_floue.py` | Moteur d'inférence floue (fuzzification, règles, défuzzification) |
| `requirements.txt`| Dépendances du projet |

---

## 🧠 Le Moteur Flou

Le système évalue la fatigue en combinant trois variables d'entrée :
1. **EAR (Eye Aspect Ratio)** : Ouverture des yeux.
2. **Fréquence de Bâillement** : Nombre de bâillements par minute.
3. **Clignements Lents** : Détection des micro-sommeils (fermeture prolongée > 0.3s).

### États et Recommandations
Le système calcule un score de vigilance (0-100%) et affiche un message adapté :

| Score | État | Message Conducteur |
|-------|------|--------------------|
| 70%+ | **CONDUITE NORMALE** | Vigilance correcte. |
| 50-70% | **VIGILANCE EN BAISSE** | Pensez à prendre un café ou aérer. |
| 30-50% | **PAUSE RECOMMANDÉE** | Faites une pause dès que possible. |
| <30% | **ARRÊT IMMÉDIAT** | Arrêtez-vous immédiatement dans un lieu sûr. |

---

## 🚀 Installation et Lancement

### 1. Pré-requis
*   **Python 3.11+**
*   Une webcam fonctionnelle.

### 2. Installation
1.  Double-cliquez sur le dossier ou clonez le dépôt.
2.  Ouvrez un terminal dans le dossier du projet.
3.  Créez un environnement virtuel :
    ```bash
    python -m venv venv
    ```
4.  Activez l'environnement :
    *   **Windows** : `.\venv\Scripts\activate`
    *   **Unix/macOS** : `source venv/bin/activate`
5.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

### 3. Lancer l'Application
```bash
python surveillance.py
```
*   **ECHAP** pour quitter.
*   **R** pour réinitialiser les compteurs (facultatif).

---

## 🛠️ Technologies
- **Python**
- **OpenCV** (Traitement d'image)
- **MediaPipe** (Points faciaux)
- **Logique Floue** (Implémentation personnalisée)

---
*Projet développé dans le cadre du cours de Logique Floue - M1*
