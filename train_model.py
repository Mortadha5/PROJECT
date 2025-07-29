from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd
import joblib
import numpy as np

# Charger le dataset
df = pd.read_csv("dataset_employes_formation_complet.csv")

# Encodage amélioré
df["competence"] = df["competence"].str.lower()
competences = df["competence"].unique()
formations = df["formation_suggeree"].unique()

comp_dict = {c: i for i, c in enumerate(competences)}
form_dict = {f: i for i, f in enumerate(formations)}
inv_form_dict = {v: k for k, v in form_dict.items()}

df["comp_encoded"] = df["competence"].map(comp_dict)
df["form_encoded"] = df["formation_suggeree"].map(form_dict)

X = df[["age", "experience", "comp_encoded"]]
y = df["form_encoded"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Modèle optimisé pour les probabilités
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight='balanced'  # Important pour des probabilités équilibrées
)

# Entraînement
model.fit(X_train, y_train)

# Évaluation
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Précision du modèle: {accuracy:.3f}")

# Validation croisée
cv_scores = cross_val_score(model, X, y, cv=5)
print(f"Score de validation croisée: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

# Sauvegarde
joblib.dump(model, "model.pkl")
joblib.dump(comp_dict, "comp_dict.pkl")
joblib.dump(form_dict, "form_dict.pkl")
joblib.dump(inv_form_dict, "inv_form_dict.pkl")

print("Modèle sauvegardé avec support des probabilités!")
