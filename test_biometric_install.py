print("=== TEST D'INSTALLATION BIOMÉTRIQUE ===")

try:
    from webauthn import generate_registration_options
    print("✅ Module webauthn importé avec succès")
    
    from webauthn.helpers.structs import AuthenticatorSelectionCriteria
    print("✅ Structures webauthn importées avec succès")
    
    import base64
    print("✅ Module base64 importé avec succès")
    
    # Tester la génération d'options
    options = generate_registration_options(
        rp_id="localhost",
        rp_name="Test App",
        user_id="test_user",  # String, pas bytes
        user_name="test_user",
        user_display_name="Test User"
    )
    print("✅ Options générées avec succès")
    print(f"✅ Challenge généré: {base64.b64encode(options.challenge)[:20]}...")
    
    # Tester la classe BiometricAuth
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017/")
    db = client["formation_db"]
    
    from biometric_auth import BiometricAuth
    auth = BiometricAuth(db)
    print("✅ Classe BiometricAuth instanciée avec succès")
    
    # Tester has_biometric
    has_bio = auth.has_biometric("admin")
    print(f"✅ L'admin a une empreinte: {has_bio}")
    
    print("\n✅ TOUS LES TESTS ONT RÉUSSI!")
    
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("Assurez-vous d'avoir installé: pip install webauthn==1.8.1 pydantic==1.10.12")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
