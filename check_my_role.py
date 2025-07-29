from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["formation_db"]
users = db["utilisateurs"]

# Vérifier tous les utilisateurs
print("=== UTILISATEURS ===")
for user in users.find():
    print(f"Username: {user['username']}, Role: {user.get('role')}")

# Vérifier les prédictions
predictions = db["employes"]
count = predictions.count_documents({})
print(f"\n=== PRÉDICTIONS ===")
print(f"Total: {count}")

if count > 0:
    sample = list(predictions.find({}, {"_id": 0}).limit(3))
    print("Échantillon:", sample)