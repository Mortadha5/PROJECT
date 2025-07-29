from webauthn import generate_registration_options, verify_registration_response
from webauthn import generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttachment
)
import base64
import time
from datetime import datetime
import json

class BiometricAuth:
    def __init__(self, db):
        self.db = db
        self.credentials_collection = db["biometric_credentials"]
        self.rp_id = "localhost"  # Changer pour production
        self.rp_name = "Formation IA"
        self.origin = "http://localhost:5555"  # Changer pour production
    
    def register_start(self, username):
        """Démarrer l'enregistrement de l'empreinte"""
        try:
            # Convertir username en string si nécessaire
            if isinstance(username, bytes):
                username = username.decode('utf-8')
            
            # Générer les options d'enregistrement (user_id doit être string)
            options = generate_registration_options(
                rp_id=self.rp_id,
                rp_name=self.rp_name,
                user_id=username,  # String, pas bytes
                user_name=username,
                user_display_name=username,
                authenticator_selection=AuthenticatorSelectionCriteria(
                    authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                    user_verification=UserVerificationRequirement.REQUIRED
                )
            )
            
            # Stocker le challenge temporairement
            self.db["temp_challenges"].delete_many({"username": username})
            self.db["temp_challenges"].insert_one({
                "username": username,
                "challenge": base64.b64encode(options.challenge).decode('utf-8'),
                "timestamp": time.time()
            })
            
            # Créer un dictionnaire pour le client JavaScript
            client_options = {
                "challenge": base64.b64encode(options.challenge).decode('utf-8'),
                "rp": {"name": self.rp_name, "id": self.rp_id},
                "user": {
                    "id": base64.b64encode(options.user.id).decode('utf-8'),
                    "name": username,
                    "displayName": username
                },
                "pubKeyCredParams": [
                    {"type": "public-key", "alg": -7},  # ES256
                    {"type": "public-key", "alg": -257}  # RS256
                ],
                "authenticatorSelection": {
                    "authenticatorAttachment": "platform",
                    "userVerification": "required"
                },
                "timeout": 60000,
                "attestation": "direct"
            }
            
            return {"success": True, "options": client_options}
            
        except Exception as e:
            print(f"Erreur register_start: {e}")
            return {"success": False, "error": str(e)}
    
    def register_complete(self, username, credential_data):
        """Compléter l'enregistrement de l'empreinte"""
        try:
            # Récupérer le challenge temporaire
            challenge_doc = self.db["temp_challenges"].find_one({"username": username})
            if not challenge_doc:
                return {"success": False, "error": "Challenge expiré ou invalide"}
            
            challenge = base64.b64decode(challenge_doc["challenge"])
            
            # Créer un objet credential simple avec les attributs attendus
            class CredentialObject:
                def __init__(self, data):
                    self.id = data["id"]
                    self.raw_id = base64.b64decode(data["rawId"])
                    self.type = data["type"]
                    self.response = ResponseObject(data["response"])
            
            class ResponseObject:
                def __init__(self, data):
                    self.attestation_object = base64.b64decode(data["attestationObject"])
                    self.client_data_json = base64.b64decode(data["clientDataJSON"])
            
            credential = CredentialObject(credential_data)
            
            # Vérifier la réponse
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
                require_user_verification=True
            )
            
            # Dans les versions récentes, verification est directement l'objet VerifiedRegistration
            if verification:
                # Supprimer ancienne empreinte si existe
                self.credentials_collection.delete_many({"username": username})
                
                # Sauvegarder la nouvelle empreinte
                self.credentials_collection.insert_one({
                    "username": username,
                    "credential_id": base64.b64encode(verification.credential_id).decode('utf-8'),
                    "public_key": base64.b64encode(verification.credential_public_key).decode('utf-8'),
                    "sign_count": verification.sign_count,
                    "created_at": datetime.now(),
                    "last_used": None
                })
                
                # Nettoyer le challenge
                self.db["temp_challenges"].delete_one({"username": username})
                
                return {"success": True, "message": "Empreinte enregistrée avec succès"}
            else:
                return {"success": False, "error": "Vérification échouée"}
            
        except Exception as e:
            print(f"Erreur register_complete: {e}")
            return {"success": False, "error": str(e)}
    
    def login_start(self, username):
        """Démarrer la connexion par empreinte"""
        try:
            # Vérifier si l'utilisateur a une empreinte enregistrée
            credential = self.credentials_collection.find_one({"username": username})
            if not credential:
                return {"success": False, "error": "Aucune empreinte enregistrée"}
            
            # Décoder l'ID des credentials
            credential_id = base64.b64decode(credential["credential_id"])
            
            # Générer les options d'authentification
            options = generate_authentication_options(
                rp_id=self.rp_id,
                allow_credentials=[{
                    "type": "public-key",
                    "id": credential_id
                }],
                user_verification=UserVerificationRequirement.REQUIRED
            )
            
            # Stocker le challenge
            self.db["temp_challenges"].delete_many({"username": username})
            self.db["temp_challenges"].insert_one({
                "username": username,
                "challenge": base64.b64encode(options.challenge).decode('utf-8'),
                "timestamp": time.time()
            })
            
            # Créer un dictionnaire pour le client JavaScript
            client_options = {
                "challenge": base64.b64encode(options.challenge).decode('utf-8'),
                "timeout": 60000,
                "rpId": self.rp_id,
                "allowCredentials": [{
                    "type": "public-key",
                    "id": credential["credential_id"]
                }],
                "userVerification": "required"
            }
            
            return {"success": True, "options": client_options}
            
        except Exception as e:
            print(f"Erreur login_start: {e}")
            return {"success": False, "error": str(e)}
    
    def login_complete(self, username, assertion_data):
        """Compléter la connexion par empreinte"""
        try:
            # Récupérer le challenge temporaire
            challenge_doc = self.db["temp_challenges"].find_one({"username": username})
            if not challenge_doc:
                return {"success": False, "error": "Challenge expiré ou invalide"}
            
            challenge = base64.b64decode(challenge_doc["challenge"])
            
            # Récupérer les credentials de l'utilisateur
            credential_doc = self.credentials_collection.find_one({"username": username})
            if not credential_doc:
                return {"success": False, "error": "Aucune empreinte enregistrée"}
            
            # Décoder les données
            credential_id = base64.b64decode(credential_doc["credential_id"])
            public_key = base64.b64decode(credential_doc["public_key"])
            
            # Créer un objet assertion avec les attributs attendus
            class AssertionObject:
                def __init__(self, data):
                    self.id = data["id"]
                    self.raw_id = base64.b64decode(data["rawId"])
                    self.type = data["type"]
                    self.response = AssertionResponseObject(data["response"])
            
            class AssertionResponseObject:
                def __init__(self, data):
                    self.authenticator_data = base64.b64decode(data["authenticatorData"])
                    self.client_data_json = base64.b64decode(data["clientDataJSON"])
                    self.signature = base64.b64decode(data["signature"])
                    if data.get("userHandle"):
                        self.user_handle = base64.b64decode(data["userHandle"])
                    else:
                        self.user_handle = None
            
            assertion = AssertionObject(assertion_data)
            
            # Vérifier l'assertion
            verification = verify_authentication_response(
                credential=assertion,
                expected_challenge=challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
                credential_public_key=public_key,
                credential_current_sign_count=credential_doc.get("sign_count", 0),
                require_user_verification=True
            )
            
            # Dans les versions récentes, verification est directement l'objet VerifiedAuthentication
            # Si la vérification échoue, une exception est levée
            # Mettre à jour les informations
            self.credentials_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "sign_count": verification.new_sign_count,
                        "last_used": datetime.now()
                    }
                }
            )
            
            # Nettoyer le challenge
            self.db["temp_challenges"].delete_one({"username": username})
            
            return {"success": True, "message": "Connexion par empreinte réussie"}
            
        except Exception as e:
            print(f"Erreur login_complete: {e}")
            return {"success": False, "error": str(e)}
    
    def has_biometric(self, username):
        """Vérifier si un utilisateur a une empreinte enregistrée"""
        credential = self.credentials_collection.find_one({"username": username})
        return credential is not None










