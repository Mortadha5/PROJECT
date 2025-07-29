import joblib
import numpy as np

# Charger le modèle
try:
    model = joblib.load("model.pkl")
    comp_dict = joblib.load("comp_dict.pkl")
    inv_form_dict = joblib.load("inv_form_dict.pkl")
    
    print("✅ Modèle chargé avec succès")
    print(f"Type de modèle: {type(model)}")
    
    # Test des probabilités
    test_features = np.array([[25, 3, 0]])  # age=25, exp=3, comp=0
    
    if hasattr(model, 'predict_proba'):
        probas = model.predict_proba(test_features)
        print(f"✅ Probabilités supportées: {probas[0]}")
        print(f"Classes: {model.classes_}")
    else:
        print("❌ Le modèle ne supporte pas les probabilités")
        print("Vous devez réentraîner le modèle avec RandomForestClassifier")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("Vous devez d'abord entraîner le modèle")