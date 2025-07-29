from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["formation_db"]
users = db["utilisateurs"]

print("=== UTILISATEURS DANS LA BASE ===")
for user in users.find():
    print(f"Username: {user['username']}, Role: {user.get('role', 'NO ROLE')}")