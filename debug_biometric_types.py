print("=== DEBUG TYPES BIOMÉTRIQUES ===")

from webauthn import generate_registration_options
import base64

# Test 1: Vérifier le type de challenge
print("\n--- Test 1: Types de données WebAuthn ---")
options = generate_registration_options(
    rp_id="localhost",
    rp_name="Test App",
    user_id="test_user",  # String, pas bytes
    user_name="test_user",
    user_display_name="Test User"
)

print(f"Type de options.challenge: {type(options.challenge)}")
print(f"Type de options.user.id: {type(options.user.id)}")

# Test 2: Encodage base64
print("\n--- Test 2: Encodage base64 ---")
if isinstance(options.challenge, bytes):
    challenge_b64 = base64.b64encode(options.challenge).decode('utf-8')
    print(f"✅ Challenge encodé: {challenge_b64[:20]}...")
else:
    print(f"❌ Challenge n'est pas en bytes: {type(options.challenge)}")

# Test 3: Test de la classe BiometricAuth
print("\n--- Test 3: BiometricAuth ---")
try:
    from pymongo import MongoClient
    from biometric_auth import BiometricAuth
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["formation_db"]
    auth = BiometricAuth(db)
    
    # Test avec string
    print("Test avec username string:")
    result1 = auth.register_start("test_user")
    print(f"Résultat: {result1.get('success', False)}")
    if not result1.get('success'):
        print(f"Erreur: {result1.get('error')}")
    
    # Test avec bytes
    print("Test avec username bytes:")
    result2 = auth.register_start(b"test_user")
    print(f"Résultat: {result2.get('success', False)}")
    if not result2.get('success'):
        print(f"Erreur: {result2.get('error')}")
    
except Exception as e:
    print(f"❌ Erreur BiometricAuth: {e}")
    import traceback
    print(traceback.format_exc())

print("\n=== FIN DEBUG ===")
