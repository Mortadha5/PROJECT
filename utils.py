import bcrypt
from datetime import datetime
from bson import ObjectId

def hash_password(password):
    """Hasher un mot de passe"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    """Vérifier un mot de passe"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def log_user_action(db, username, action, details):
    """Logger une action utilisateur"""
    db["user_logs"].insert_one({
        "username": username,
        "action": action,
        "details": details,
        "timestamp": datetime.now()
    })

def share_prediction(db, prediction_id, shared_by, shared_with, message=None):
    """Partager une prédiction avec un autre utilisateur"""
    db["shared_predictions"].insert_one({
        "prediction_id": prediction_id,
        "shared_by": shared_by,
        "shared_with": shared_with,
        "message": message,
        "shared_at": datetime.now(),
        "status": "pending"  # pending, accepted, declined
    })

def get_shared_predictions(db, username):
    """Récupérer les prédictions partagées avec un utilisateur"""
    return list(db["shared_predictions"].find({"shared_with": username}).sort("shared_at", -1))

def get_my_shares(db, username):
    """Récupérer les prédictions que j'ai partagées"""
    return list(db["shared_predictions"].find({"shared_by": username}).sort("shared_at", -1))

