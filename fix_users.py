from pymongo import MongoClient
from utils import hash_password
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["formation_db"]
users = db["utilisateurs"]

# Supprimer tous les utilisateurs existants
users.delete_many({})
print("✅ Anciens utilisateurs supprimés")

# Créer un admin
admin_data = {
    "username": "admin",
    "password": hash_password("admin123"),
    "role": "admin",
    "created_at": datetime.now()
}
users.insert_one(admin_data)
print("✅ Admin créé: admin / admin123")

# Créer un user
user_data = {
    "username": "user",
    "password": hash_password("user123"),
    "role": "user", 
    "created_at": datetime.now()
}
users.insert_one(user_data)
print("✅ User créé: user / user123")

# Vérifier
print("\n=== VÉRIFICATION ===")
for user in users.find():
    print(f"Username: {user['username']}, Role: {user['role']}")