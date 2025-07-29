from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["formation_db"]
users = db["utilisateurs"]

print("=== VÉRIFICATION DES UTILISATEURS ===")
for user in users.find():
    print(f"Username: '{user['username']}'")
    print(f"Role: '{user.get('role', 'AUCUN ROLE')}'")
    print(f"Type du role: {type(user.get('role'))}")
    print("---")

# Compter les rôles
admin_count = users.count_documents({"role": "admin"})
user_count = users.count_documents({"role": "user"})
no_role_count = users.count_documents({"role": {"$exists": False}})

print(f"\nSTATISTIQUES:")
print(f"Admins: {admin_count}")
print(f"Users: {user_count}")
print(f"Sans rôle: {no_role_count}")