from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd
import joblib
import numpy as np

# Charger le dataset
df = pd.read_csv("dataset_employes_formation_complet.csv")

# Extraire toutes les compétences individuelles
all_competences = set()
for row in df["competence"]:
    for c in row.split(","):
        all_competences.add(c.strip().lower())

all_competences = sorted(all_competences)
print(f"Compétences trouvées: {all_competences}")

# Créer le dictionnaire de compétences (pour one-hot encoding)
comp_dict = {c: i for i, c in enumerate(all_competences)}

# Encodage des formations
formations = df["formation_suggeree"].unique()
form_dict = {f: i for i, f in enumerate(formations)}
inv_form_dict = {v: k for k, v in form_dict.items()}

# Créer les features one-hot pour les compétences
def encode_competences(competence_str, comp_dict):
    """Encode les compétences en vecteur one-hot"""
    vector = [0] * len(comp_dict)
    for c in competence_str.split(","):
        c = c.strip().lower()
        if c in comp_dict:
            vector[comp_dict[c]] = 1
    return vector

# Construire les features
comp_columns = [f"comp_{c}" for c in all_competences]
comp_vectors = df["competence"].apply(lambda x: encode_competences(x, comp_dict))
comp_df = pd.DataFrame(comp_vectors.tolist(), columns=comp_columns)

# Features = age + experience + one-hot competences
X = pd.concat([df[["age", "experience"]], comp_df], axis=1)
y = df["formation_suggeree"].map(form_dict)

print(f"Features shape: {X.shape}")
print(f"Feature names: age, experience, {comp_columns}")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Modèle optimisé pour les probabilités
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight='balanced'
)

# Entraînement
model.fit(X_train, y_train)

# Évaluation
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nPrécision du modèle: {accuracy:.3f}")

# Validation croisée
cv_scores = cross_val_score(model, X, y, cv=5)
print(f"Score de validation croisée: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

# Sauvegarde
joblib.dump(model, "model.pkl")
joblib.dump(comp_dict, "comp_dict.pkl")
joblib.dump(form_dict, "form_dict.pkl")
joblib.dump(inv_form_dict, "inv_form_dict.pkl")
joblib.dump(all_competences, "all_competences.pkl")

print("\n✅ Modèle multi-compétences sauvegardé!")
print(f"   Compétences supportées: {len(all_competences)}")
print(f"   Formations: {len(formations)}")
print(f"   Features par prédiction: {X.shape[1]}")
