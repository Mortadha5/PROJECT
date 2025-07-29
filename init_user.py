from pymongo import MongoClient
from utils import hash_password
from datetime import datetime

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["formation_db"]
users = db["utilisateurs"]

# Supprimer l'ancien admin s'il existe
users.delete_one({"username": "admin"})

# Insérer un utilisateur admin avec mot de passe hashé
hashed_password = hash_password("admin123!")
users.insert_one({
    "username": "admin",
    "password": hashed_password,
    "role": "admin",
    "created_at": datetime.now()
})

print("✅ Utilisateur admin créé avec succès.")
print("   Username: admin")
print("   Password: admin123!")
