from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
from pymongo import MongoClient
import joblib
import numpy as np
import pandas as pd
import json
import bcrypt
from functools import wraps
from datetime import datetime, timedelta
import traceback  # Ajouter cet import
from bson import ObjectId
import os
from werkzeug.utils import secure_filename
from biometric_auth import BiometricAuth

# Descriptions détaillées des formations
FORMATION_DETAILS = {
    "Deep Learning & IA Appliquée": {
        "description": "Réseaux de neurones profonds, NLP, computer vision, IA générative",
        "duration": "8-12 mois",
        "difficulty": "Avancé",
        "salary_range": "55000-95000€",
        "job_opportunities": "Très élevées",
        "skills": ["Mathématiques", "Python", "Statistiques", "Algèbre linéaire"],
        "industries": ["Tech", "Finance", "Santé", "Recherche"],
        "required_competences": ["ia/ml", "python", "data science"],
        "related_competences": ["cloud", "docker", "kubernetes"]
    },
    "Administration Réseaux & Cisco": {
        "description": "Configuration réseau, routage, switching, sécurité réseau",
        "duration": "6-9 mois",
        "difficulty": "Intermédiaire",
        "salary_range": "40000-65000€",
        "job_opportunities": "Élevées",
        "skills": ["Réseaux", "TCP/IP", "Configuration", "Dépannage"],
        "industries": ["Télécoms", "ESN", "Infrastructure", "Gouvernement"],
        "required_competences": ["réseaux", "linux"],
        "related_competences": ["cybersécurité", "cloud computing"]
    },
    "Formation Flutter / React Native": {
        "description": "Développement d'applications mobiles cross-platform modernes",
        "duration": "4-6 mois",
        "difficulty": "Intermédiaire",
        "salary_range": "42000-70000€",
        "job_opportunities": "Très élevées",
        "skills": ["Dart/JS", "UI/UX", "API REST", "Mobile"],
        "industries": ["Mobile", "Startup", "E-commerce", "Médias"],
        "required_competences": ["développement mobile", "développement web"],
        "related_competences": ["docker", "cloud"]
    },
    "Sécurité Réseaux & Pentesting": {
        "description": "Tests de pénétration, audit sécurité, ethical hacking, OWASP",
        "duration": "9-12 mois",
        "difficulty": "Avancé",
        "salary_range": "55000-90000€",
        "job_opportunities": "Très élevées",
        "skills": ["Sécurité", "Réseaux", "Scripts", "Analyse forensique"],
        "industries": ["Sécurité", "Finance", "Gouvernement", "Défense"],
        "required_competences": ["cybersécurité", "réseaux", "linux"],
        "related_competences": ["python", "cloud computing"]
    },
    "SQL & NoSQL pour Développeurs": {
        "description": "Bases de données relationnelles et NoSQL, optimisation requêtes",
        "duration": "3-5 mois",
        "difficulty": "Intermédiaire",
        "salary_range": "40000-65000€",
        "job_opportunities": "Élevées",
        "skills": ["SQL", "MongoDB", "Modélisation", "Performance"],
        "industries": ["Tech", "Finance", "E-commerce", "Data"],
        "required_competences": ["base de données", "développement web"],
        "related_competences": ["python", "cloud"]
    },
    "Formation Développement Web Frontend": {
        "description": "React, Vue.js, HTML5/CSS3, responsive design, JAMstack",
        "duration": "4-6 mois",
        "difficulty": "Intermédiaire",
        "salary_range": "38000-65000€",
        "job_opportunities": "Très élevées",
        "skills": ["JavaScript", "CSS", "Frameworks", "UX"],
        "industries": ["Web", "E-commerce", "SaaS", "Médias"],
        "required_competences": ["développement web"],
        "related_competences": ["docker", "cloud"]
    },
    "CI/CD avec Docker & Jenkins": {
        "description": "Automatisation DevOps, conteneurisation, pipelines CI/CD",
        "duration": "6-9 mois",
        "difficulty": "Avancé",
        "salary_range": "50000-85000€",
        "job_opportunities": "Très élevées",
        "skills": ["Docker", "Jenkins", "Kubernetes", "Automation"],
        "industries": ["Tech", "Cloud", "Infrastructure", "SaaS"],
        "required_competences": ["devops", "docker", "kubernetes"],
        "related_competences": ["linux", "cloud computing", "python"]
    },
    "Certification AWS / Azure": {
        "description": "Architecture cloud, services managés, IaC, certification officielle",
        "duration": "6-8 mois",
        "difficulty": "Avancé",
        "salary_range": "50000-85000€",
        "job_opportunities": "Très élevées",
        "skills": ["Cloud", "Architecture", "Sécurité", "Networking"],
        "industries": ["Cloud", "Tech", "Finance", "Santé"],
        "required_competences": ["cloud computing", "cloud"],
        "related_competences": ["devops", "docker", "kubernetes", "linux"]
    },
    "Support IT & Gestion Incidents": {
        "description": "Helpdesk avancé, ITIL, gestion incidents, support niveau 2-3",
        "duration": "3-4 mois",
        "difficulty": "Débutant",
        "salary_range": "30000-45000€",
        "job_opportunities": "Élevées",
        "skills": ["Dépannage", "Communication", "ITIL", "Outils ticketing"],
        "industries": ["ESN", "Support", "Infrastructure", "Télécoms"],
        "required_competences": ["support technique"],
        "related_competences": ["réseaux", "linux"]
    },
    "Machine Learning avec Python": {
        "description": "Scikit-learn, feature engineering, modèles supervisés/non-supervisés",
        "duration": "6-9 mois",
        "difficulty": "Avancé",
        "salary_range": "50000-80000€",
        "job_opportunities": "Très élevées",
        "skills": ["Python", "Statistiques", "Algorithmes", "Data"],
        "industries": ["Tech", "Finance", "Santé", "Recherche"],
        "required_competences": ["python", "data science", "ia/ml"],
        "related_competences": ["docker", "cloud"]
    }
}

# Mapping compétences → compétences liées pour le skill gap
COMPETENCE_GRAPH = {
    "ia/ml": {"related": ["python", "data science", "cloud"], "level": "avancé"},
    "python": {"related": ["ia/ml", "data science", "devops"], "level": "intermédiaire"},
    "data science": {"related": ["python", "ia/ml", "base de données"], "level": "avancé"},
    "développement web": {"related": ["docker", "cloud", "base de données"], "level": "intermédiaire"},
    "développement mobile": {"related": ["développement web", "cloud", "docker"], "level": "intermédiaire"},
    "devops": {"related": ["docker", "kubernetes", "linux", "cloud computing"], "level": "avancé"},
    "docker": {"related": ["devops", "kubernetes", "linux"], "level": "intermédiaire"},
    "kubernetes": {"related": ["docker", "devops", "cloud computing"], "level": "avancé"},
    "cybersécurité": {"related": ["réseaux", "linux", "python"], "level": "avancé"},
    "réseaux": {"related": ["cybersécurité", "linux", "cloud computing"], "level": "intermédiaire"},
    "cloud computing": {"related": ["cloud", "devops", "docker", "kubernetes"], "level": "avancé"},
    "cloud": {"related": ["cloud computing", "devops", "docker"], "level": "intermédiaire"},
    "linux": {"related": ["devops", "réseaux", "docker"], "level": "intermédiaire"},
    "base de données": {"related": ["python", "développement web", "cloud"], "level": "intermédiaire"},
    "support technique": {"related": ["réseaux", "linux"], "level": "débutant"},
}

def analyze_user_profile(age, experience, competences_list):
    """Analyse le profil utilisateur pour des recommandations personnalisées"""
    analysis = {
        "career_stage": "",
        "learning_capacity": "",
        "time_availability": "",
        "risk_tolerance": "",
        "recommendations": [],
        "competence_count": len(competences_list),
        "profile_strength": ""
    }
    
    # Analyse de la carrière
    if age < 25:
        analysis["career_stage"] = "Débutant - Phase d'exploration"
        analysis["learning_capacity"] = "Très élevée"
        analysis["time_availability"] = "Élevée"
        analysis["risk_tolerance"] = "Élevée"
    elif age < 35:
        analysis["career_stage"] = "Professionnel junior - Spécialisation"
        analysis["learning_capacity"] = "Élevée"
        analysis["time_availability"] = "Modérée"
        analysis["risk_tolerance"] = "Modérée"
    elif age < 45:
        analysis["career_stage"] = "Professionnel expérimenté - Leadership"
        analysis["learning_capacity"] = "Modérée"
        analysis["time_availability"] = "Limitée"
        analysis["risk_tolerance"] = "Faible"
    else:
        analysis["career_stage"] = "Senior - Expertise/Management"
        analysis["learning_capacity"] = "Ciblée"
        analysis["time_availability"] = "Très limitée"
        analysis["risk_tolerance"] = "Très faible"
    
    # Force du profil basée sur le nombre de compétences
    if len(competences_list) >= 5:
        analysis["profile_strength"] = "Profil polyvalent très solide"
    elif len(competences_list) >= 3:
        analysis["profile_strength"] = "Profil diversifié"
    elif len(competences_list) >= 2:
        analysis["profile_strength"] = "Profil en développement"
    else:
        analysis["profile_strength"] = "Profil spécialisé"
    
    # Recommandations personnalisées
    if experience < 2:
        analysis["recommendations"].append("Privilégier les formations avec beaucoup de pratique")
        analysis["recommendations"].append("Commencer par des concepts fondamentaux")
    elif experience < 5:
        analysis["recommendations"].append("Se spécialiser dans un domaine précis")
        analysis["recommendations"].append("Développer des compétences avancées")
    else:
        analysis["recommendations"].append("Se concentrer sur le leadership technique")
        analysis["recommendations"].append("Acquérir des compétences de management")
    
    if len(competences_list) == 1:
        analysis["recommendations"].append("Diversifier vos compétences pour plus d'opportunités")
    
    return analysis

def perform_skill_gap_analysis(competences_list, top_formations):
    """Analyse les compétences acquises, manquantes et recommandées"""
    acquired = set(competences_list)
    recommended = set()
    missing = set()
    
    # Pour chaque formation recommandée, identifier les compétences requises
    for rec in top_formations[:3]:
        formation = rec["formation"]
        details = FORMATION_DETAILS.get(formation, {})
        required = set(details.get("required_competences", []))
        related = set(details.get("related_competences", []))
        
        # Compétences manquantes = requises mais pas acquises
        missing.update(required - acquired)
        # Compétences recommandées = liées mais pas acquises
        recommended.update(related - acquired)
    
    # Aussi utiliser le graphe de compétences
    for comp in competences_list:
        comp_info = COMPETENCE_GRAPH.get(comp, {})
        for related in comp_info.get("related", []):
            if related not in acquired:
                recommended.add(related)
    
    # Retirer les manquantes des recommandées (priorité aux manquantes)
    recommended -= missing
    
    return {
        "acquired": list(acquired),
        "missing": list(missing),
        "recommended": list(recommended - acquired),
        "coverage_score": round(len(acquired) / max(len(acquired) + len(missing), 1) * 100, 1)
    }

def calculate_recommendation_score(formation, age, experience, competences_list, base_probability):
    """Calcule un score personnalisé pour chaque recommandation"""
    details = FORMATION_DETAILS.get(formation, {})
    score = base_probability * 100
    
    # Bonus basé sur la correspondance des compétences requises
    required_comps = set(details.get("required_competences", []))
    user_comps = set(competences_list)
    if required_comps:
        match_ratio = len(required_comps & user_comps) / len(required_comps)
        score += match_ratio * 15  # Bonus jusqu'à +15 pour correspondance parfaite
    
    # Bonus pour compétences liées
    related_comps = set(details.get("related_competences", []))
    if related_comps:
        related_match = len(related_comps & user_comps) / len(related_comps)
        score += related_match * 5  # Bonus jusqu'à +5
    
    # Ajustements basés sur l'âge
    if age < 30:
        if details.get("difficulty") == "Avancé":
            score += 5
    elif age > 40:
        if details.get("difficulty") == "Intermédiaire":
            score += 3
    
    # Ajustements basés sur l'expérience
    if experience < 2:
        if details.get("difficulty") in ["Débutant", "Intermédiaire"]:
            score += 5
    elif experience > 5:
        if details.get("difficulty") == "Avancé":
            score += 8
    
    # Ajustements basés sur les opportunités d'emploi
    if details.get("job_opportunities") == "Très élevées":
        score += 10
    elif details.get("job_opportunities") == "Élevées":
        score += 5
    
    return min(score, 100)

def get_confidence_level(score):
    """Détermine le niveau de confiance basé sur le score"""
    if score >= 80:
        return {"level": "Très élevée", "color": "#28a745", "icon": "fas fa-check-circle"}
    elif score >= 65:
        return {"level": "Élevée", "color": "#17a2b8", "icon": "fas fa-thumbs-up"}
    elif score >= 50:
        return {"level": "Modérée", "color": "#ffc107", "icon": "fas fa-exclamation-triangle"}
    else:
        return {"level": "Faible", "color": "#dc3545", "icon": "fas fa-times-circle"}

# Créer l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "votre_cle_secrete_plus_complexe_123!")

# CORS pour le frontend React
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:5173"])

# Initialiser SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialiser CSRF Protection
# csrf = CSRFProtect(app)  # Commenté temporairement

# Configuration sécurisée des sessions
app.config.update(
    SESSION_COOKIE_SECURE=False,  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

# Connexion MongoDB
client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client["formation_db"]
collection = db["employes"]

# Charger le modèle
model = joblib.load("model.pkl")
comp_dict = joblib.load("comp_dict.pkl")
form_dict = joblib.load("form_dict.pkl")
inv_form_dict = {v: k for k, v in form_dict.items()}
competences = list(comp_dict.keys())

def encode_competences_vector(competences_list):
    """Encode une liste de compétences en vecteur one-hot"""
    vector = [0] * len(comp_dict)
    for c in competences_list:
        c = c.strip().lower()
        if c in comp_dict:
            vector[comp_dict[c]] = 1
    return vector

# Middleware login_required
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# Middleware admin_required avec plus de debug
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print(f"DEBUG admin_required: logged_in = {session.get('logged_in')}")
        print(f"DEBUG admin_required: username = {session.get('username')}")
        print(f"DEBUG admin_required: role = {session.get('role')}")
        print(f"DEBUG admin_required: session = {dict(session)}")
        
        if not session.get("logged_in"):
            print("DEBUG: User not logged in, redirecting to login")
            return redirect(url_for("login"))
        
        user_role = session.get("role")
        if user_role != "admin":
            print(f"DEBUG: Access DENIED - User role '{user_role}' is not admin")
            return render_template("access_denied.html"), 403
        
        print("DEBUG: Admin access GRANTED")
        return f(*args, **kwargs)
    return wrapper

@app.errorhandler(404)
def not_found_error(error):
    return "", 404

@app.errorhandler(500)
def internal_error(error):
    print(f"ERREUR 500: {error}")
    print(f"TRACEBACK: {traceback.format_exc()}")
    return f"<h1>Erreur 500</h1><pre>{traceback.format_exc()}</pre>", 500

@app.errorhandler(Exception)
def handle_exception(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    print(f"EXCEPTION NON GÉRÉE: {e}")
    print(f"TRACEBACK: {traceback.format_exc()}")
    return f"<h1>Erreur</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        
        # Vérifier dans la base de données
        users_collection = db["utilisateurs"]
        user = users_collection.find_one({"username": username})
        
        if user:
            # Vérifier si l'utilisateur est bloqué
            if user.get("blocked"):
                from utils import log_user_action
                log_user_action(db, username, "login_blocked", "Tentative de connexion - Compte bloqué")
                error = "Compte bloqué. Contactez l'administrateur."
                return render_template("login.html", error=error)
            
            from utils import check_password, log_user_action
            if check_password(password, user["password"]):
                session["logged_in"] = True
                session["username"] = username
                session["role"] = user.get("role", "user")
                
                # Gérer l'avatar (fichier ou icône)
                if user.get("avatar_type") == "file" and user.get("avatar_file"):
                    session["user_avatar"] = f"/static/uploads/avatars/{user['avatar_file']}"
                    session["avatar_type"] = "file"
                else:
                    session["user_avatar"] = user.get("avatar", "fas fa-user-circle")
                    session["avatar_type"] = "icon"
                
                session.permanent = True
                
                # Mettre à jour la dernière connexion
                users_collection.update_one(
                    {"username": username},
                    {"$set": {"last_login": datetime.now()}}
                )
                
                log_user_action(db, username, "login", "Connexion réussie")
                return redirect(url_for("index"))
            else:
                from utils import log_user_action
                log_user_action(db, username, "login_failed", "Mot de passe incorrect")
                error = "Mot de passe incorrect"
        else:
            from utils import log_user_action
            log_user_action(db, username, "login_failed", "Utilisateur non trouvé")
            error = "Utilisateur non trouvé"
            
    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    username = session.get("username")
    session.clear()
    
    # Logger la déconnexion
    if username:
        from utils import log_user_action
        log_user_action(db, username, "logout", "Déconnexion")
    
    return redirect(url_for("login"))

@app.route("/register")
def register():
    """Inscription publique désactivée - redirection vers login"""
    return redirect(url_for("login"))

# ═══════════════════════════════════════════════════════════════
# API JSON pour le frontend React
# ═══════════════════════════════════════════════════════════════

@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    users_collection = db["utilisateurs"]
    user = users_collection.find_one({"username": username})
    
    if not user:
        return jsonify({"success": False, "error": "Utilisateur non trouvé"}), 401
    
    if user.get("blocked"):
        return jsonify({"success": False, "error": "Compte bloqué. Contactez l'administrateur."}), 403
    
    from utils import check_password, log_user_action
    if check_password(password, user["password"]):
        session["logged_in"] = True
        session["username"] = username
        session["role"] = user.get("role", "user")
        session.permanent = True
        
        users_collection.update_one(
            {"username": username},
            {"$set": {"last_login": datetime.now()}}
        )
        log_user_action(db, username, "login", "Connexion réussie (React)")
        
        return jsonify({
            "success": True,
            "user": {
                "username": username,
                "role": user.get("role", "user"),
                "email": user.get("email", ""),
                "avatar": user.get("avatar", "")
            }
        })
    else:
        log_user_action(db, username, "login_failed", "Mot de passe incorrect")
        return jsonify({"success": False, "error": "Mot de passe incorrect"}), 401

@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    username = session.get("username")
    session.clear()
    if username:
        from utils import log_user_action
        log_user_action(db, username, "logout", "Déconnexion (React)")
    return jsonify({"success": True})

@app.route("/api/auth/session")
def api_auth_session():
    if session.get("logged_in"):
        return jsonify({
            "logged_in": True,
            "username": session.get("username"),
            "role": session.get("role", "user")
        })
    return jsonify({"logged_in": False})

@app.route("/api/profile")
@login_required
def api_profile():
    user = db["utilisateurs"].find_one({"username": session["username"]}, {"_id": 0, "password": 0})
    if user:
        user["created_at"] = str(user.get("created_at", ""))
        return jsonify(user)
    return jsonify({}), 404

@app.route("/api/profile", methods=["PUT"])
@login_required
def api_update_profile():
    data = request.get_json()
    update_fields = {}
    if "email" in data:
        update_fields["email"] = data["email"]
    if "bio" in data:
        update_fields["bio"] = data["bio"]
    if "full_name" in data:
        update_fields["full_name"] = data["full_name"]
    
    if update_fields:
        db["utilisateurs"].update_one(
            {"username": session["username"]},
            {"$set": update_fields}
        )
    return jsonify({"success": True})

@app.route("/api/change_password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json()
    current = data.get("current_password", "")
    new_pwd = data.get("new_password", "")
    
    user = db["utilisateurs"].find_one({"username": session["username"]})
    from utils import check_password, hash_password
    
    if not check_password(current, user["password"]):
        return jsonify({"success": False, "error": "Mot de passe actuel incorrect"}), 400
    
    db["utilisateurs"].update_one(
        {"username": session["username"]},
        {"$set": {"password": hash_password(new_pwd)}}
    )
    return jsonify({"success": True})

@app.route("/api/admin/users")
@admin_required
def api_admin_users():
    users = list(db["utilisateurs"].find({}, {"_id": 0, "password": 0}))
    for u in users:
        u["created_at"] = str(u.get("created_at", ""))
        u["last_login"] = str(u.get("last_login", ""))
    return jsonify({"users": users})

@app.route("/api/admin/users/create", methods=["POST"])
@admin_required
def api_admin_create_user():
    data = request.get_json()
    username = data.get("username", "").strip()
    
    if db["utilisateurs"].find_one({"username": username}):
        return jsonify({"success": False, "error": "Nom d'utilisateur déjà pris"}), 400
    
    from utils import hash_password
    db["utilisateurs"].insert_one({
        "full_name": data.get("full_name", ""),
        "username": username,
        "email": data.get("email", ""),
        "password": hash_password(data.get("password", "")),
        "role": data.get("role", "user"),
        "created_at": datetime.now(),
        "blocked": False
    })
    return jsonify({"success": True})

@app.route("/api/admin/users/<username>", methods=["PUT"])
@admin_required
def api_admin_edit_user(username):
    data = request.get_json()
    update_fields = {}
    if "role" in data:
        update_fields["role"] = data["role"]
    if "email" in data:
        update_fields["email"] = data["email"]
    if "full_name" in data:
        update_fields["full_name"] = data["full_name"]
    
    if update_fields:
        db["utilisateurs"].update_one({"username": username}, {"$set": update_fields})
    return jsonify({"success": True})

@app.route("/api/admin/users/<username>", methods=["DELETE"])
@admin_required
def api_admin_delete_user(username):
    if username == "admin":
        return jsonify({"success": False, "error": "Impossible de supprimer l'admin"}), 400
    db["utilisateurs"].delete_one({"username": username})
    return jsonify({"success": True})

@app.route("/api/admin/dashboard")
@admin_required
def api_admin_dashboard():
    users_count = db["utilisateurs"].count_documents({})
    predictions = list(collection.find({}, {"_id": 0}))
    total_predictions = len(predictions)
    
    avg_age = 0
    avg_exp = 0
    formation_dist = {}
    
    if predictions:
        ages = [p.get("age", 0) for p in predictions if p.get("age")]
        exps = [p.get("experience", 0) for p in predictions if p.get("experience")]
        avg_age = round(sum(ages) / len(ages), 1) if ages else 0
        avg_exp = round(sum(exps) / len(exps), 1) if exps else 0
        
        for p in predictions:
            f = p.get("formation", p.get("formation_suggeree", "Autre"))
            formation_dist[f] = formation_dist.get(f, 0) + 1
    
    return jsonify({
        "total_users": users_count,
        "total_predictions": total_predictions,
        "avg_age": avg_age,
        "avg_experience": avg_exp,
        "formation_distribution": formation_dist
    })

@app.route("/api/admin/historique")
@admin_required
def api_admin_historique():
    predictions = list(collection.find({}, {"_id": 0}).sort("created_at", -1).limit(200))
    for p in predictions:
        p["created_at"] = str(p.get("created_at", ""))
    return jsonify({"predictions": predictions})

@app.route("/api/admin/security")
@admin_required
def api_admin_security():
    logs = list(db["user_logs"].find({}, {"_id": 0}).sort("timestamp", -1).limit(100))
    for l in logs:
        l["timestamp"] = str(l.get("timestamp", ""))
    
    failed_logins = db["user_logs"].count_documents({"action": "login_failed"})
    blocked_users = db["utilisateurs"].count_documents({"blocked": True})
    
    suspicious = []
    pipeline = [
        {"$match": {"action": "login_failed"}},
        {"$group": {"_id": "$username", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 3}}},
        {"$sort": {"count": -1}}
    ]
    for s in db["user_logs"].aggregate(pipeline):
        user = db["utilisateurs"].find_one({"username": s["_id"]})
        suspicious.append({
            "username": s["_id"],
            "failed_attempts": s["count"],
            "blocked": user.get("blocked", False) if user else False
        })
    
    return jsonify({
        "recent_logs": logs,
        "failed_logins": failed_logins,
        "blocked_users": blocked_users,
        "active_sessions": 0,
        "suspicious_users": suspicious
    })

@app.route("/api/admin/roadmaps")
@admin_required
def api_admin_roadmaps():
    roadmaps = list(db["roadmaps"].find())
    for r in roadmaps:
        r["_id"] = str(r["_id"])
    total = len(roadmaps)
    completed = sum(1 for r in roadmaps if r.get("progress", 0) == 100)
    in_progress = total - completed
    avg_progress = round(sum(r.get("progress", 0) for r in roadmaps) / total, 1) if total > 0 else 0
    
    return jsonify({
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "avg_progress": avg_progress,
        "roadmaps": roadmaps
    })


@app.route("/api/admin/roadmaps/<roadmap_id>", methods=["DELETE"])
@admin_required
def api_delete_roadmap(roadmap_id):
    """Supprimer une roadmap par ID"""
    from bson import ObjectId
    result = db["roadmaps"].delete_one({"_id": ObjectId(roadmap_id)})
    if result.deleted_count:
        return jsonify({"success": True})
    return jsonify({"error": "Roadmap non trouvée"}), 404


# ═══════════════════════════════════════════════════════════════
# API Admin Predictions (review workflow)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/admin/predictions/pending")
@admin_required
def api_admin_predictions_pending():
    """Liste des prédictions en attente de review"""
    from bson import ObjectId
    status_filter = request.args.get("status", "pending")
    query = {}
    if status_filter != "all":
        query["status"] = status_filter
    
    predictions = list(db["prediction_requests"].find(query).sort("created_at", -1))
    for p in predictions:
        p["_id"] = str(p["_id"])
        if p.get("created_at"):
            p["created_at"] = p["created_at"].isoformat()
        if p.get("reviewed_at"):
            p["reviewed_at"] = p["reviewed_at"].isoformat()
        if p.get("sent_at"):
            p["sent_at"] = p["sent_at"].isoformat()
    
    return jsonify({"predictions": predictions})


@app.route("/api/admin/predictions/pending_count")
@admin_required
def api_admin_predictions_pending_count():
    """Nombre de prédictions en attente"""
    count = db["prediction_requests"].count_documents({"status": "pending"})
    return jsonify({"count": count})


@app.route("/api/admin/predictions/<prediction_id>")
@admin_required
def api_admin_prediction_detail(prediction_id):
    """Détail d'une prédiction"""
    from bson import ObjectId
    pred = db["prediction_requests"].find_one({"_id": ObjectId(prediction_id)})
    if not pred:
        return jsonify({"error": "Prédiction non trouvée"}), 404
    
    pred["_id"] = str(pred["_id"])
    if pred.get("created_at"):
        pred["created_at"] = pred["created_at"].isoformat()
    if pred.get("reviewed_at"):
        pred["reviewed_at"] = pred["reviewed_at"].isoformat()
    if pred.get("sent_at"):
        pred["sent_at"] = pred["sent_at"].isoformat()
    
    return jsonify({"prediction": pred})


@app.route("/api/admin/predictions/<prediction_id>/send", methods=["POST"])
@admin_required
def api_admin_prediction_send(prediction_id):
    """Envoyer le résultat au user"""
    from bson import ObjectId
    data = request.get_json() or {}
    comment = data.get("comment", "")
    
    pred = db["prediction_requests"].find_one({"_id": ObjectId(prediction_id)})
    if not pred:
        return jsonify({"error": "Prédiction non trouvée"}), 404
    
    update_data = {
        "status": "sent_to_user",
        "sent_at": datetime.now(),
    }
    if comment:
        update_data["admin_comment"] = comment
    
    db["prediction_requests"].update_one(
        {"_id": ObjectId(prediction_id)},
        {"$set": update_data}
    )
    
    # Notifier l'utilisateur
    formation = pred.get("prediction_result", {}).get("formation_suggeree", "")
    send_notification(
        pred["username"],
        "prediction",
        "Résultat de prédiction disponible",
        f"L'administrateur a validé votre prédiction. Formation recommandée : {formation}",
        link="/mes-resultats"
    )
    
    # Notifier l'admin (confirmation d'envoi)
    send_notification(
        session["username"],
        "success",
        "Résultat envoyé",
        f"Le résultat de prédiction a été envoyé à {pred['username']}.",
        link="/admin/predictions"
    )
    
    return jsonify({"success": True, "message": "Résultat envoyé à l'utilisateur"})


@app.route("/api/admin/predictions/<prediction_id>/comment", methods=["POST"])
@admin_required
def api_admin_prediction_comment(prediction_id):
    """Ajouter un commentaire admin"""
    from bson import ObjectId
    data = request.get_json()
    comment = data.get("comment", "")
    
    result = db["prediction_requests"].update_one(
        {"_id": ObjectId(prediction_id)},
        {"$set": {
            "admin_comment": comment,
            "status": "reviewed",
            "reviewed_at": datetime.now()
        }}
    )
    
    if result.modified_count:
        return jsonify({"success": True})
    return jsonify({"error": "Prédiction non trouvée"}), 404


@app.route("/api/mes_resultats")
@login_required
def api_mes_resultats():
    """Résultats envoyés à l'utilisateur"""
    predictions = list(db["prediction_requests"].find({
        "username": session["username"],
        "status": "sent_to_user"
    }).sort("sent_at", -1))
    
    for p in predictions:
        p["_id"] = str(p["_id"])
        if p.get("created_at"):
            p["created_at"] = p["created_at"].isoformat()
        if p.get("reviewed_at"):
            p["reviewed_at"] = p["reviewed_at"].isoformat()
        if p.get("sent_at"):
            p["sent_at"] = p["sent_at"].isoformat()
    
    return jsonify({"predictions": predictions})


@app.route("/api/mes_demandes")
@login_required
def api_mes_demandes():
    """Toutes les demandes de l'utilisateur (sans résultat si pending)"""
    predictions = list(db["prediction_requests"].find({
        "username": session["username"]
    }).sort("created_at", -1))
    
    result = []
    for p in predictions:
        item = {
            "_id": str(p["_id"]),
            "status": p["status"],
            "input_data": p.get("input_data", {}),
            "admin_comment": p.get("admin_comment", ""),
            "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
            "sent_at": p["sent_at"].isoformat() if p.get("sent_at") else None,
        }
        # Ne montrer le résultat que si envoyé
        if p["status"] == "sent_to_user":
            item["prediction_result"] = p.get("prediction_result", {})
        result.append(item)
    
    return jsonify({"predictions": result})


# ═══════════════════════════════════════════════════════════════
# Fin API React
# ═══════════════════════════════════════════════════════════════

@app.route("/admin/users/create", methods=["GET", "POST"])
@admin_required
def admin_create_user():
    error = None
    success = None
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        
        # Validation
        if not full_name or len(full_name) < 2:
            error = "Le nom complet doit contenir au moins 2 caractères"
        elif len(username) < 3:
            error = "Le nom d'utilisateur doit contenir au moins 3 caractères"
        elif not email or "@" not in email:
            error = "Veuillez saisir une adresse email valide"
        elif len(password) < 6:
            error = "Le mot de passe doit contenir au moins 6 caractères"
        elif role not in ["user", "admin"]:
            error = "Veuillez sélectionner un rôle valide"
        else:
            users_collection = db["utilisateurs"]
            if users_collection.find_one({"username": username}):
                error = "Ce nom d'utilisateur existe déjà"
            elif users_collection.find_one({"email": email}):
                error = "Cette adresse email est déjà utilisée"
            else:
                from utils import hash_password, log_user_action
                hashed_password = hash_password(password)
                
                users_collection.insert_one({
                    "full_name": full_name,
                    "username": username,
                    "email": email,
                    "password": hashed_password,
                    "created_at": datetime.now(),
                    "role": role,
                    "created_by": session["username"]
                })
                
                role_text = "Administrateur" if role == "admin" else "Utilisateur"
                log_user_action(db, session["username"], "user_create", f"Utilisateur {username} créé - Rôle: {role_text}")
                success = f"Compte {role_text} '{username}' créé avec succès !"

    return render_template("admin_create_user.html", error=error, success=success)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html", competences=competences, prediction=None)

@app.route("/historique")
@admin_required
def historique():
    # Récupérer les paramètres de filtre
    filter_type = request.args.get('type', 'all')
    filter_user = request.args.get('user', 'all')
    
    # Construire la requête MongoDB
    query = {}
    if filter_type != 'all':
        if filter_type == 'simple':
            query['prediction_type'] = {'$ne': 'advanced'}
        elif filter_type == 'advanced':
            query['prediction_type'] = 'advanced'
    
    if filter_user != 'all':
        query['created_by'] = filter_user
    
    # Récupérer les données filtrées
    docs = list(collection.find(query, {"_id": 0}).sort("created_at", -1))
    
    # Récupérer tous les utilisateurs qui ont fait des prédictions
    users = list(collection.distinct("created_by"))
    users = [user for user in users if user]  # Enlever les valeurs None
    
    return render_template("historique.html", 
                         data=docs, 
                         users=users,
                         current_type=filter_type,
                         current_user=filter_user)

@app.route("/debug_historique")
@admin_required
def debug_historique():
    try:
        # Compter les documents
        count = collection.count_documents({})
        
        # Récupérer quelques documents
        docs = list(collection.find({}, {"_id": 0}).limit(5))
        
        # Vérifier la connexion
        db_status = "OK" if client.admin.command('ping') else "FAILED"
        
        return f"""
        <h2>Debug Historique</h2>
        <p><strong>Statut DB:</strong> {db_status}</p>
        <p><strong>Nombre total de prédictions:</strong> {count}</p>
        <p><strong>Collection:</strong> {collection.name}</p>
        <p><strong>Database:</strong> {db.name}</p>
        <p><strong>Échantillon de données:</strong></p>
        <pre>{docs}</pre>
        <p><strong>Session:</strong> {dict(session)}</p>
        <a href="{url_for('historique')}">Essayer l'historique normal</a>
        """
    except Exception as e:
        return f"<h2>Erreur de debug:</h2><p>{str(e)}</p>"

# Route export_pdf supprimée

@app.route("/dashboard")
@admin_required
def dashboard():
    try:
        # Charger les données du CSV et de MongoDB
        df = pd.read_csv("dataset_employes_formation.csv")
        mongo_data = list(collection.find({}, {"_id": 0}))

        if mongo_data:
            mongo_df = pd.DataFrame(mongo_data)
            # Renommer la colonne pour correspondre au CSV
            if 'formation_suggeree' in mongo_df.columns:
                mongo_df = mongo_df.rename(columns={'formation_suggeree': 'formation_recommandee'})
            df = pd.concat([df, mongo_df], ignore_index=True)

        # Statistiques générales
        total_employees = len(df)
        avg_age = round(df['age'].mean(), 1)
        avg_experience = round(df['experience'].mean(), 1)

        # Vérifier le nom de la colonne formation
        formation_col = 'formation_recommandee' if 'formation_recommandee' in df.columns else 'formation_suggeree'
        
        # Distribution des formations
        formation_counts = df[formation_col].value_counts()
        formations = list(formation_counts.items())

        # Distribution par âge (groupes)
        age_ranges = ['18-25', '26-35', '36-45', '46-55', '55+']
        age_counts = [
            len(df[(df['age'] >= 18) & (df['age'] <= 25)]),
            len(df[(df['age'] >= 26) & (df['age'] <= 35)]),
            len(df[(df['age'] >= 36) & (df['age'] <= 45)]),
            len(df[(df['age'] >= 46) & (df['age'] <= 55)]),
            len(df[df['age'] > 55])
        ]
        
        ages = list(zip(age_ranges, age_counts))

        return render_template("dashboard.html",
                               formations=formations,
                               total_employees=total_employees,
                               avg_age=avg_age,
                               avg_experience=avg_experience,
                               ages=ages)
    except Exception as e:
        return f"<h2>Erreur dans le dashboard :</h2><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

# Configuration pour l'upload de fichiers
UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Créer le dossier d'upload s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    data = request.get_json()
    age = int(data.get("age", 0))
    experience = int(data.get("experience", 0))
    competences_input = data.get("competences", [])
    
    # Support ancien format (single competence)
    if not competences_input and data.get("competence"):
        competences_input = [data.get("competence")]
    
    competences_list = [c.strip().lower() for c in competences_input if c.strip().lower() in comp_dict]
    
    if not competences_list:
        return jsonify({"error": "Aucune compétence valide fournie"}), 400
    
    comp_vector = encode_competences_vector(competences_list)
    features = np.array([[age, experience] + comp_vector])
    pred = model.predict(features)[0]
    formation = inv_form_dict[pred]

    return jsonify({"formation_suggeree": formation, "competences_used": competences_list})

@app.route("/api/predict_advanced", methods=["POST"])
@login_required
def predict_advanced():
    try:
        data = request.get_json()
        age = int(data.get("age", 0))
        experience = int(data.get("experience", 0))
        competences_input = data.get("competences", [])
        
        # Support ancien format
        if not competences_input and data.get("competence"):
            competences_input = [data.get("competence")]
        
        # Validation et nettoyage
        competences_list = [c.strip().lower() for c in competences_input if c.strip().lower() in comp_dict]
        
        if not competences_list:
            return jsonify({"error": "Veuillez sélectionner au moins une compétence valide"}), 400
        
        # Prédiction avec probabilités (multi-compétences one-hot)
        comp_vector = encode_competences_vector(competences_list)
        features = np.array([[age, experience] + comp_vector])
        
        # Obtenir les probabilités pour toutes les classes
        probabilities = model.predict_proba(features)[0]
        classes = model.classes_
        
        # Créer les recommandations avec scores personnalisés
        recommendations = []
        for i, prob in enumerate(probabilities):
            if prob > 0.02:
                formation_encoded = classes[i]
                formation = inv_form_dict[formation_encoded]
                
                custom_score = calculate_recommendation_score(
                    formation, age, experience, competences_list, prob
                )
                
                confidence = get_confidence_level(custom_score)
                details = FORMATION_DETAILS.get(formation, {})
                
                recommendations.append({
                    "formation": formation,
                    "confidence_score": round(custom_score, 1),
                    "confidence_level": confidence,
                    "base_probability": round(prob * 100, 1),
                    "details": details,
                    "reasons": generate_recommendation_reasons(
                        formation, age, experience, competences_list, custom_score
                    )
                })
        
        # Trier par score de confiance
        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        # Top 5 recommandations
        top_recommendations = recommendations[:5]
        
        # Analyse du profil
        profile_analysis = analyze_user_profile(age, experience, competences_list)
        
        # Skill Gap Analysis
        skill_gap = perform_skill_gap_analysis(competences_list, top_recommendations)

        # Si admin: retourner directement le résultat (ancien workflow)
        if session.get("role") == "admin":
            prediction_data = {
                "nom": data.get("nom", ""),
                "prenom": data.get("prenom", ""),
                "age": age,
                "experience": experience,
                "competences": competences_list,
                "competences_count": len(competences_list),
                "formation_suggeree": top_recommendations[0]["formation"] if top_recommendations else "Aucune",
                "confidence_score": top_recommendations[0]["confidence_score"] if top_recommendations else 0,
                "all_recommendations": [r["formation"] for r in top_recommendations],
                "skill_gap": skill_gap,
                "created_by": session["username"],
                "created_at": datetime.now(),
                "prediction_type": "advanced_multi"
            }
            collection.insert_one(prediction_data)

            return jsonify({
                "success": True,
                "recommendations": top_recommendations,
                "profile_analysis": profile_analysis,
                "skill_gap": skill_gap,
                "total_analyzed": len(recommendations),
                "competences_used": competences_list
            })

        # Si user: sauvegarder en pending, ne pas retourner le résultat
        prediction_request = {
            "username": session["username"],
            "input_data": {
                "nom": data.get("nom", ""),
                "prenom": data.get("prenom", ""),
                "age": age,
                "experience": experience,
                "competences": competences_list,
                "competences_count": len(competences_list),
            },
            "prediction_result": {
                "recommendations": top_recommendations,
                "profile_analysis": profile_analysis,
                "skill_gap": skill_gap,
                "total_analyzed": len(recommendations),
                "competences_used": competences_list,
                "formation_suggeree": top_recommendations[0]["formation"] if top_recommendations else "Aucune",
                "confidence_score": top_recommendations[0]["confidence_score"] if top_recommendations else 0,
            },
            "status": "pending",
            "admin_comment": "",
            "created_at": datetime.now(),
            "reviewed_at": None,
            "sent_at": None
        }
        
        db["prediction_requests"].insert_one(prediction_request)
        
        # Notifier l'admin
        send_notification(
            "admin",
            "info",
            "Nouvelle prédiction en attente",
            f"{session['username']} a soumis une demande de prédiction",
            link="/admin/predictions"
        )
        
        # Notifier l'utilisateur (confirmation)
        send_notification(
            session["username"],
            "info",
            "Demande de prédiction envoyée",
            "Votre demande a été soumise. Vous serez notifié dès que l'administrateur aura validé votre résultat.",
            link="/mes-resultats"
        )
        
        return jsonify({
            "success": True,
            "pending": True,
            "message": "Votre demande a été envoyée à l'administrateur pour validation."
        })
        
    except Exception as e:
        print(f"Erreur prédiction avancée: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur lors de la prédiction: {str(e)}"}), 500

def generate_recommendation_reasons(formation, age, experience, competences_list, score):
    """Génère les raisons pour une recommandation"""
    reasons = []
    details = FORMATION_DETAILS.get(formation, {})
    
    # Correspondance compétences
    required = set(details.get("required_competences", []))
    user_comps = set(competences_list)
    matched = required & user_comps
    if matched:
        reasons.append(f"Correspond à vos compétences : {', '.join(matched)}")
    
    if score >= 80:
        reasons.append("Excellente correspondance avec votre profil")
    elif score >= 65:
        reasons.append("Bonne correspondance avec vos compétences")
    
    if age < 30:
        reasons.append("Âge optimal pour cette formation")
    
    if experience >= 3:
        reasons.append("Votre expérience est un atout")
    elif experience < 2:
        reasons.append("Formation adaptée aux débutants")
    
    if details.get("job_opportunities") == "Très élevées":
        reasons.append("Secteur en forte demande")
    
    return reasons[:4]

@app.route("/advanced_prediction")
@admin_required
def advanced_prediction_page():
    """Page pour les prédictions avancées - Admin seulement"""
    return render_template("advanced_prediction.html", competences=competences)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    error = None
    success = None
    
    if request.method == "POST":
        username = request.form["username"].strip()
        
        if not username:
            error = "Veuillez entrer votre nom d'utilisateur"
        else:
            users_collection = db["utilisateurs"]
            user = users_collection.find_one({"username": username})
            
            if user:
                # Générer un nouveau mot de passe temporaire
                import random
                import string
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Hasher le nouveau mot de passe
                from utils import hash_password, log_user_action
                hashed_password = hash_password(temp_password)
                
                # Mettre à jour dans la base de données
                users_collection.update_one(
                    {"username": username},
                    {"$set": {"password": hashed_password, "temp_password": True}}
                )
                
                # Logger l'action
                log_user_action(db, username, "password_reset", "Mot de passe réinitialisé")
                
                success = f"Nouveau mot de passe temporaire : {temp_password}. Connectez-vous et changez-le immédiatement."
            else:
                error = "Nom d'utilisateur non trouvé"
    
    return render_template("forgot_password.html", error=error, success=success)

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    error = None
    success = None
    
    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        
        if new_password != confirm_password:
            error = "Les nouveaux mots de passe ne correspondent pas"
        elif len(new_password) < 6:
            error = "Le nouveau mot de passe doit contenir au moins 6 caractères"
        else:
            users_collection = db["utilisateurs"]
            user = users_collection.find_one({"username": session["username"]})
            
            from utils import check_password, hash_password, log_user_action
            if check_password(current_password, user["password"]):
                hashed_password = hash_password(new_password)
                users_collection.update_one(
                    {"username": session["username"]},
                    {"$set": {"password": hashed_password}, "$unset": {"temp_password": ""}}
                )
                log_user_action(db, session["username"], "password_change", "Mot de passe changé")
                success = "Mot de passe changé avec succès !"
            else:
                error = "Mot de passe actuel incorrect"
    
    return render_template("change_password.html", error=error, success=success)

@app.route("/admin/users")
@admin_required
def admin_users():
    users_collection = db["utilisateurs"]
    users = list(users_collection.find({}, {"password": 0}))  # Exclure les mots de passe
    return render_template("admin_users.html", users=users)

@app.route("/debug_session")
@login_required
def debug_session():
    return f"""
    <h2>Debug Session</h2>
    <p>Logged in: {session.get('logged_in')}</p>
    <p>Username: {session.get('username')}</p>
    <p>Role: {session.get('role')}</p>
    <p>Session data: {dict(session)}</p>
    <a href="{url_for('index')}">Retour</a>
    """

@app.route("/mes_predictions")
@admin_required
def mes_predictions():
    # Afficher seulement les prédictions de l'utilisateur connecté
    user_predictions = list(collection.find(
        {"created_by": session["username"]}, 
        {"_id": 0}
    ).sort("created_at", -1))
    
    return render_template("mes_predictions.html", predictions=user_predictions)

@app.route("/mon_profil")
@login_required
def mon_profil():
    users_collection = db["utilisateurs"]
    user = users_collection.find_one({"username": session["username"]})
    
    # Calculer les statistiques utilisateur
    user_stats = {}
    
    # Nombre de prédictions
    predictions_count = collection.count_documents({"created_by": session["username"]})
    user_stats["predictions_count"] = predictions_count
    
    # Nombre de messages chatbot
    chatbot_collection = db["chatbot_conversations"]
    chatbot_messages = chatbot_collection.count_documents({"user": session["username"]})
    user_stats["chatbot_messages"] = chatbot_messages
    
    # Calculer le temps depuis la dernière connexion
    time_since_last_login = "Jamais"
    if user.get("last_login"):
        delta = datetime.now() - user["last_login"]
        if delta.days > 0:
            time_since_last_login = f"Il y a {delta.days} jour{'s' if delta.days > 1 else ''}"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            time_since_last_login = f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            time_since_last_login = f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            time_since_last_login = "À l'instant"
    
    # Calculer les jours depuis l'inscription
    days_member = 0
    if user.get("created_at"):
        days_member = (datetime.now() - user["created_at"]).days
    
    # Récupérer l'activité récente
    recent_activities = []
    
    # Prédictions récentes
    recent_predictions = list(collection.find(
        {"created_by": session["username"]}, 
        {"formation_suggeree": 1, "created_at": 1}
    ).sort("created_at", -1).limit(5))
    
    for pred in recent_predictions:
        recent_activities.append({
            "type": "prediction",
            "formation_suggeree": pred.get("formation_suggeree"),
            "created_at": pred.get("created_at")
        })
    
    # Messages chatbot récents
    recent_chatbot = list(chatbot_collection.find(
        {"user": session["username"]}, 
        {"timestamp": 1}
    ).sort("timestamp", -1).limit(3))
    
    for chat in recent_chatbot:
        recent_activities.append({
            "type": "chatbot",
            "created_at": chat.get("timestamp")
        })
    
    # Trier toutes les activités par date
    recent_activities.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    recent_activities = recent_activities[:10]  # Limiter aux 10 plus récentes
    
    return render_template(
        "mon_profil.html", 
        user=user, 
        user_stats=user_stats,
        time_since_last_login=time_since_last_login,
        recent_activities=recent_activities,
        days_member=days_member
    )

@app.route("/admin/users/edit/<username>", methods=["GET", "POST"])
@admin_required
def edit_user(username):
    users_collection = db["utilisateurs"]
    user = users_collection.find_one({"username": username})
    
    if not user:
        return redirect(url_for("admin_users"))
    
    error = None
    success = None
    
    if request.method == "POST":
        new_username = request.form["username"].strip()
        new_role = request.form["role"]
        
        # Validation
        if len(new_username) < 3:
            error = "Le nom d'utilisateur doit contenir au moins 3 caractères"
        elif new_role not in ["user", "admin"]:
            error = "Veuillez sélectionner un rôle valide"
        elif new_username != username and users_collection.find_one({"username": new_username}):
            error = "Ce nom d'utilisateur existe déjà"
        else:
            # Mettre à jour l'utilisateur
            users_collection.update_one(
                {"username": username},
                {"$set": {
                    "username": new_username,
                    "role": new_role,
                    "updated_at": datetime.now()
                }}
            )
            
            # Logger l'action
            from utils import log_user_action
            log_user_action(db, session["username"], "user_edit", f"Utilisateur {username} modifié")
            
            success = "Utilisateur modifié avec succès !"
            
            # Si on a changé le username, rediriger vers la nouvelle page
            if new_username != username:
                return redirect(url_for("edit_user", username=new_username))
    
    return render_template("edit_user.html", user=user, error=error, success=success)

@app.route("/admin/users/delete/<username>", methods=["POST"])
@admin_required
def delete_user(username):
    users_collection = db["utilisateurs"]
    
    # Empêcher l'admin de se supprimer lui-même
    if username == session["username"]:
        return jsonify({"error": "Vous ne pouvez pas supprimer votre propre compte"}), 400
    
    # Supprimer l'utilisateur
    result = users_collection.delete_one({"username": username})
    
    if result.deleted_count > 0:
        # Logger l'action
        from utils import log_user_action
        log_user_action(db, session["username"], "user_delete", f"Utilisateur {username} supprimé")
        return jsonify({"success": "Utilisateur supprimé avec succès"})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

@app.route("/admin/users/reset_password/<username>", methods=["POST"])
@admin_required
def reset_user_password(username):
    users_collection = db["utilisateurs"]
    user = users_collection.find_one({"username": username})
    
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    
    # Générer un nouveau mot de passe temporaire
    import random
    import string
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # Hasher le nouveau mot de passe
    from utils import hash_password, log_user_action
    hashed_password = hash_password(temp_password)
    
    # Mettre à jour dans la base de données
    users_collection.update_one(
        {"username": username},
        {"$set": {"password": hashed_password, "temp_password": True, "updated_at": datetime.now()}}
    )
    
    # Logger l'action
    log_user_action(db, session["username"], "password_reset", f"Mot de passe réinitialisé pour {username}")
    
    return jsonify({"success": f"Nouveau mot de passe: {temp_password}"})

@app.route("/debug_dashboard")
@admin_required
def debug_dashboard():
    try:
        df = pd.read_csv("dataset_employes_formation.csv")
        mongo_data = list(collection.find({}, {"_id": 0}))
        
        debug_info = f"""
        <h2>Debug Dashboard</h2>
        <p><strong>Colonnes CSV:</strong> {list(df.columns)}</p>
        <p><strong>Nombre lignes CSV:</strong> {len(df)}</p>
        <p><strong>Nombre docs MongoDB:</strong> {len(mongo_data)}</p>
        """
        
        if mongo_data:
            mongo_df = pd.DataFrame(mongo_data)
            debug_info += f"<p><strong>Colonnes MongoDB:</strong> {list(mongo_df.columns)}</p>"
            
            # Renommer si nécessaire
            if 'formation_suggeree' in mongo_df.columns:
                mongo_df = mongo_df.rename(columns={'formation_suggeree': 'formation_recommandee'})
            
            df = pd.concat([df, mongo_df], ignore_index=True)
        
        formation_col = 'formation_recommandee' if 'formation_recommandee' in df.columns else 'formation_suggeree'
        formation_counts = df[formation_col].value_counts()
        
        debug_info += f"""
        <p><strong>Colonne formation utilisée:</strong> {formation_col}</p>
        <p><strong>Formations trouvées:</strong> {list(formation_counts.items())}</p>
        <p><strong>Échantillon données:</strong></p>
        <pre>{df.head().to_string()}</pre>
        """
        
        return debug_info
        
    except Exception as e:
        return f"<h2>Erreur debug:</h2><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

# Fonction utility_processor supprimée

@app.route("/messages")
@login_required
def messages():
    messages_collection = db["messages"]
    
    if session.get("role") == "admin":
        # Admin voit tous les messages
        conversations = list(messages_collection.aggregate([
            {"$group": {
                "_id": "$from_user",
                "last_message": {"$last": "$$ROOT"},
                "unread_count": {"$sum": {"$cond": [{"$eq": ["$read", False]}, 1, 0]}}
            }},
            {"$sort": {"last_message.created_at": -1}}
        ]))
    else:
        # User voit seulement ses messages avec l'admin
        user_messages = list(messages_collection.find({
            "$or": [
                {"from_user": session["username"], "to_user": "admin"},
                {"from_user": "admin", "to_user": session["username"]}
            ]
        }).sort("created_at", 1))
        
        # Marquer comme lus les messages reçus
        messages_collection.update_many({
            "from_user": "admin",
            "to_user": session["username"],
            "read": False
        }, {"$set": {"read": True}})
        
        return render_template("user_messages.html", messages=user_messages)
    
    return render_template("admin_messages.html", conversations=conversations)

@app.route("/messages/<username>")
@admin_required
def conversation(username):
    messages_collection = db["messages"]
    
    # Récupérer la conversation avec cet utilisateur
    conversation_messages = list(messages_collection.find({
        "$or": [
            {"from_user": username, "to_user": "admin"},
            {"from_user": "admin", "to_user": username}
        ]
    }).sort("created_at", 1))
    
    # Marquer comme lus les messages de cet utilisateur
    messages_collection.update_many({
        "from_user": username,
        "to_user": "admin",
        "read": False
    }, {"$set": {"read": True}})
    
    return render_template("conversation.html", 
                         messages=conversation_messages, 
                         other_user=username)

@app.route("/send_message", methods=["POST"])
@login_required
def send_message():
    data = request.get_json()
    message_text = data.get("message", "").strip()
    to_user = data.get("to_user")
    
    if not message_text:
        return jsonify({"error": "Message vide"}), 400
    
    # Validation des destinataires
    if session.get("role") == "admin":
        # Admin peut envoyer à n'importe quel user
        if not to_user:
            return jsonify({"error": "Destinataire requis"}), 400
    else:
        # User peut seulement envoyer à l'admin
        to_user = "admin"
    
    messages_collection = db["messages"]
    message_data = {
        "from_user": session["username"],
        "to_user": to_user,
        "message": message_text,
        "created_at": datetime.now(),
        "read": False
    }
    
    messages_collection.insert_one(message_data)
    
    # Envoyer une notification en temps réel au destinataire
    send_notification(
        to_user,
        "info",
        "Nouveau message",
        f"Vous avez reçu un message de {session['username']}",
        link="/messages"
    )
    
    # Logger l'action
    from utils import log_user_action
    log_user_action(db, session["username"], "send_message", f"Message envoyé à {to_user}")
    
    return jsonify({"success": True})

@app.route("/api/unread_messages")
@login_required
def unread_messages():
    messages_collection = db["messages"]
    
    if session.get("role") == "admin":
        # Compter les messages non lus pour l'admin
        unread_count = messages_collection.count_documents({
            "to_user": "admin",
            "read": False
        })
        # Per-user breakdown
        pipeline = [
            {"$match": {"to_user": "admin", "read": False}},
            {"$group": {"_id": "$from_user", "count": {"$sum": 1}}}
        ]
        per_user = {doc["_id"]: doc["count"] for doc in messages_collection.aggregate(pipeline)}
        return jsonify({"unread_count": unread_count, "per_user": per_user})
    else:
        # Compter les messages non lus pour l'utilisateur
        unread_count = messages_collection.count_documents({
            "to_user": session["username"],
            "from_user": "admin",
            "read": False
        })
    
    return jsonify({"unread_count": unread_count})

@app.route("/api/get_messages")
@login_required
def get_messages():
    messages_collection = db["messages"]
    
    if session.get("role") == "admin":
        # Pour l'admin, récupérer les messages d'une conversation spécifique
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username requis"}), 400
            
        messages = list(messages_collection.find({
            "$or": [
                {"from_user": username, "to_user": "admin"},
                {"from_user": "admin", "to_user": username}
            ]
        }).sort("created_at", 1))
        
        # Marquer comme lus les messages reçus par l'admin
        messages_collection.update_many({
            "from_user": username,
            "to_user": "admin",
            "read": False
        }, {"$set": {"read": True}})
    else:
        # Pour l'utilisateur, récupérer ses messages avec l'admin
        messages = list(messages_collection.find({
            "$or": [
                {"from_user": session["username"], "to_user": "admin"},
                {"from_user": "admin", "to_user": session["username"]}
            ]
        }).sort("created_at", 1))
        
        # Marquer comme lus les messages reçus
        messages_collection.update_many({
            "from_user": "admin",
            "to_user": session["username"],
            "read": False
        }, {"$set": {"read": True}})
    
    # Convertir ObjectId en string pour JSON
    for message in messages:
        message['_id'] = str(message['_id'])
        message['created_at'] = message['created_at'].isoformat()
    
    return jsonify({"messages": messages})

@app.route("/chatbot")
@login_required
def chatbot_page():
    """Page du chatbot IA"""
    return render_template("chatbot.html")

@app.route("/api/chatbot", methods=["POST"])
@login_required
def chatbot_api():
    """API pour le chatbot IA"""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return jsonify({"error": "Message vide"}), 400
        
        # Générer une réponse du chatbot
        bot_response = generate_chatbot_response(user_message)
        
        # Sauvegarder la conversation
        chatbot_collection = db["chatbot_conversations"]
        chatbot_collection.insert_one({
            "user": session["username"],
            "user_message": user_message,
            "bot_response": bot_response,
            "timestamp": datetime.now()
        })
        
        return jsonify({
            "success": True,
            "response": bot_response
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_chatbot_response(message):
    """Génère une réponse intelligente du chatbot avec plus de contexte et de personnalisation"""
    message_lower = message.lower()
    user_name = session.get('username', 'utilisateur')
    
    # Analyse des intentions plus précise
    if any(word in message_lower for word in ["formation", "cours", "apprendre", "étudier", "programme"]):
        formations = list(FORMATION_DETAILS.keys())
        return f"Je peux vous aider avec nos {len(formations)} formations : {', '.join(formations)}. Dites-moi laquelle vous intéresse ou posez-moi une question spécifique sur l'une d'entre elles."
    
    # Réponses détaillées sur les formations spécifiques
    for formation, details in FORMATION_DETAILS.items():
        if formation.lower() in message_lower:
            response = f"La formation {formation} est excellente ! {details['description']}.\n\n"
            response += f"📊 Durée: {details['duration']}\n"
            response += f"💰 Salaire: {details['salary_range']}\n"
            response += f"🔍 Difficulté: {details['difficulty']}\n"
            response += f"💼 Opportunités: {details['job_opportunities']}\n\n"
            response += f"Compétences développées: {', '.join(details['skills'])}\n"
            response += f"Secteurs d'application: {', '.join(details['industries'])}\n\n"
            response += "Souhaitez-vous en savoir plus sur une autre formation ou avoir des conseils personnalisés?"
            return response
    
    # Comparaison de formations
    if any(word in message_lower for word in ["comparer", "différence", "versus", "vs", "ou", "meilleur"]):
        if "python" in message_lower and "javascript" in message_lower:
            return "Python vs JavaScript:\n\n" + \
                   "Python est idéal pour la data science et le backend (45-75k€), tandis que JavaScript domine le développement web frontend (40-70k€).\n\n" + \
                   "Python a une syntaxe plus simple et est excellent pour les débutants, alors que JavaScript est incontournable pour le web interactif.\n\n" + \
                   "Les deux sont très demandés sur le marché. Votre choix dépend de votre objectif: analyse de données (Python) ou interfaces web (JavaScript)."
        elif "data" in message_lower and "cyber" in message_lower:
            return "Data Science vs Cybersécurité:\n\n" + \
                   "La Data Science (55-95k€) se concentre sur l'analyse et la modélisation des données, tandis que la Cybersécurité (55-90k€) protège les systèmes contre les menaces.\n\n" + \
                   "La Data Science demande des compétences en statistiques et mathématiques, la Cybersécurité exige une connaissance approfondie des systèmes et des réseaux.\n\n" + \
                   "Les deux sont des domaines en forte croissance avec d'excellentes perspectives d'emploi."
    
    # Conseils personnalisés basés sur l'expérience
    if any(word in message_lower for word in ["débutant", "commencer", "débuter", "novice"]):
        return f"Pour un débutant, je recommande de commencer par Python ou HTML/CSS/JavaScript. Python a une syntaxe claire et intuitive, parfaite pour apprendre les concepts de programmation. Le développement web (HTML/CSS/JS) offre des résultats visuels rapides, ce qui est motivant. Quelle est votre expérience actuelle, {user_name}?"
    
    if any(word in message_lower for word in ["expérimenté", "expert", "avancé", "professionnel"]):
        return f"Pour quelqu'un avec de l'expérience, les formations en Data Science, DevOps ou Cybersécurité peuvent offrir d'excellentes opportunités de progression. Ces domaines sont très demandés et bien rémunérés. Quelle est votre spécialité actuelle, {user_name}?"
    
    # Réponses sur les salaires et le marché de l'emploi
    if any(word in message_lower for word in ["salaire", "paye", "rémunération", "gagner", "argent"]):
        return "Voici les fourchettes de salaires pour nos formations:\n\n" + \
               "💰 Python: 45 000 - 75 000€\n" + \
               "💰 JavaScript: 40 000 - 70 000€\n" + \
               "💰 Data Science: 55 000 - 95 000€\n" + \
               "💰 DevOps: 50 000 - 85 000€\n" + \
               "💰 Cybersécurité: 55 000 - 90 000€\n\n" + \
               "Ces chiffres varient selon l'expérience, la région et l'entreprise. Quelle formation vous intéresse particulièrement?"
    
    if any(word in message_lower for word in ["emploi", "travail", "job", "embauche", "recruter", "marché"]):
        return "Le marché de l'emploi en tech est très dynamique:\n\n" + \
               "🔥 Data Science: Demande croissante dans tous les secteurs\n" + \
               "🔥 Cybersécurité: Pénurie mondiale d'experts\n" + \
               "🔥 DevOps: Essentiel pour toutes les entreprises tech\n" + \
               "🔥 Développement Web: Toujours très recherché\n\n" + \
               "Toutes nos formations sont alignées avec les besoins actuels du marché. Avez-vous une préférence?"
    
    # Aide sur le processus de formation
    if any(word in message_lower for word in ["durée", "temps", "combien", "long"]):
        return "La durée des formations varie:\n\n" + \
               "⏱️ Python: 6-8 mois\n" + \
               "⏱️ JavaScript: 4-6 mois\n" + \
               "⏱️ Data Science: 8-10 mois\n" + \
               "⏱️ DevOps: 6-9 mois\n" + \
               "⏱️ Cybersécurité: 9-12 mois\n\n" + \
               "Ces durées sont indicatives et peuvent être adaptées selon votre rythme d'apprentissage et votre disponibilité."
    
    # Aide générale et orientation
    if any(word in message_lower for word in ["aide", "help", "conseil", "orienter", "choisir", "recommander", "suggestion"]):
        return f"Je peux vous aider à choisir la formation idéale, {user_name}! Voici quelques questions pour vous guider:\n\n" + \
               "1️⃣ Quel est votre niveau actuel en programmation?\n" + \
               "2️⃣ Avez-vous un domaine qui vous passionne (web, data, sécurité)?\n" + \
               "3️⃣ Combien de temps pouvez-vous consacrer à votre formation?\n" + \
               "4️⃣ Quels sont vos objectifs professionnels?\n\n" + \
               "Répondez à ces questions et je pourrai vous faire une recommandation personnalisée."
    
    # Salutations et remerciements
    if any(word in message_lower for word in ["bonjour", "salut", "hello", "bonsoir", "coucou"]):
        return f"Bonjour {user_name} ! 👋 Je suis votre assistant IA pour les formations. Je peux vous aider à choisir la meilleure formation selon vos besoins, répondre à vos questions sur les programmes, les salaires, ou les débouchés. Comment puis-je vous aider aujourd'hui?"
    
    if any(word in message_lower for word in ["merci", "thanks", "thx", "thank"]):
        return f"Avec plaisir, {user_name}! 😊 Je suis là pour vous aider. N'hésitez pas si vous avez d'autres questions sur nos formations."
    
    if any(word in message_lower for word in ["au revoir", "bye", "ciao", "adieu", "à plus"]):
        return f"Au revoir, {user_name}! N'hésitez pas à revenir si vous avez d'autres questions. Bonne journée! 👋"
    
    # Réponse par défaut améliorée
    return f"Je ne suis pas sûr de comprendre votre question, {user_name}. Vous pouvez me demander des informations sur:\n\n" + \
           "📚 Nos formations (Python, JavaScript, Data Science, DevOps, Cybersécurité)\n" + \
           "💰 Les salaires et débouchés\n" + \
           "⏱️ La durée des formations\n" + \
           "🔍 Des conseils personnalisés\n\n" + \
           "N'hésitez pas à être plus précis ou à utiliser les boutons rapides ci-dessous."

@app.route("/api/chatbot_feedback", methods=["POST"])
@login_required
def chatbot_feedback():
    """API pour enregistrer le feedback sur les réponses du chatbot"""
    try:
        data = request.get_json()
        message_id = data.get("message_id")
        feedback = data.get("feedback")  # "helpful" ou "not_helpful"
        user_comment = data.get("comment", "")
        
        if not message_id or not feedback:
            return jsonify({"error": "Données incomplètes"}), 400
        
        # Sauvegarder le feedback
        feedback_collection = db["chatbot_feedback"]
        feedback_collection.insert_one({
            "message_id": message_id,
            "user": session["username"],
            "feedback": feedback,
            "comment": user_comment,
            "timestamp": datetime.now()
        })
        
        # Mettre à jour les statistiques globales
        stats_collection = db["chatbot_stats"]
        stats_collection.update_one(
            {"_id": "global_stats"},
            {
                "$inc": {
                    f"feedback_{feedback}": 1,
                    "total_feedback": 1
                }
            },
            upsert=True
        )
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chatbot_stats")
@admin_required
def chatbot_stats():
    """Page de statistiques du chatbot pour les admins"""
    try:
        # Récupérer les statistiques globales
        stats_collection = db["chatbot_stats"]
        global_stats = stats_collection.find_one({"_id": "global_stats"}) or {}
        
        # Récupérer les conversations récentes
        chatbot_collection = db["chatbot_conversations"]
        recent_conversations = list(chatbot_collection.find().sort("timestamp", -1).limit(100))
        
        # Récupérer les feedbacks
        feedback_collection = db["chatbot_feedback"]
        recent_feedback = list(feedback_collection.find().sort("timestamp", -1).limit(50))
        
        # Analyser les sujets populaires
        all_messages = list(chatbot_collection.find({}, {"user_message": 1}))
        topics = {}
        keywords = ["python", "javascript", "data", "cyber", "salaire", "durée", "débutant", "avancé"]
        
        for msg in all_messages:
            user_msg = msg.get("user_message", "").lower()
            for keyword in keywords:
                if keyword in user_msg:
                    topics[keyword] = topics.get(keyword, 0) + 1
        
        # Trier les sujets par popularité
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        
        return render_template(
            "chatbot_stats.html",
            global_stats=global_stats,
            recent_conversations=recent_conversations,
            recent_feedback=recent_feedback,
            topics=sorted_topics
        )
        
    except Exception as e:
        return f"<h2>Erreur dans les statistiques du chatbot:</h2><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    users_collection = db["utilisateurs"]
    user = users_collection.find_one({"username": session["username"]})
    
    error = None
    success = None
    
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form.get("email", "").strip()
        bio = request.form.get("bio", "").strip()
        
        # Validation
        if len(username) < 3:
            error = "Le nom d'utilisateur doit contenir au moins 3 caractères"
        elif username != user["username"] and users_collection.find_one({"username": username}):
            error = "Ce nom d'utilisateur existe déjà"
        else:
            # Mettre à jour le profil
            update_data = {
                "username": username,
                "email": email if email else None,
                "bio": bio if bio else None,
                "updated_at": datetime.now()
            }
            
            users_collection.update_one(
                {"username": session["username"]},
                {"$set": update_data}
            )
            
            # Mettre à jour la session si le username a changé
            if username != session["username"]:
                session["username"] = username
            
            from utils import log_user_action
            log_user_action(db, session["username"], "profile_update", "Profil mis à jour")
            success = "Profil mis à jour avec succès !"
    
    return render_template("edit_profile.html", user=user, error=error, success=success)

@app.route("/api/upload_avatar", methods=["POST"])
@login_required
def upload_avatar():
    """Upload d'avatar - photo ou icône aléatoire"""
    try:
        # Vérifier s'il y a un fichier dans la requête
        if 'avatar' in request.files:
            file = request.files['avatar']
            
            if file and file.filename != '' and allowed_file(file.filename):
                # Sécuriser le nom de fichier
                filename = secure_filename(file.filename)
                # Créer un nom unique avec timestamp
                timestamp = str(int(datetime.now().timestamp()))
                file_extension = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{session['username']}_{timestamp}.{file_extension}"
                
                # Sauvegarder le fichier
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Supprimer l'ancien avatar s'il existe
                users_collection = db["utilisateurs"]
                user = users_collection.find_one({"username": session["username"]})
                if user.get("avatar_file"):
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], user["avatar_file"])
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # Mettre à jour la base de données
                users_collection.update_one(
                    {"username": session["username"]},
                    {"$set": {
                        "avatar_file": unique_filename,
                        "avatar_type": "file",
                        "updated_at": datetime.now()
                    }}
                )
                
                # Mettre à jour la session
                session["user_avatar"] = f"/static/uploads/avatars/{unique_filename}"
                session["avatar_type"] = "file"
                
                from utils import log_user_action
                log_user_action(db, session["username"], "avatar_upload", "Photo de profil uploadée")
                
                return jsonify({
                    "success": True,
                    "message": "Photo de profil mise à jour avec succès !",
                    "avatar": f"/static/uploads/avatars/{unique_filename}",
                    "type": "file"
                })
            else:
                return jsonify({"success": False, "error": "Fichier non valide"}), 400
        
        else:
            # Pas de fichier, générer un avatar aléatoire (comme avant)
            import random
            avatars = [
                "fas fa-user-astronaut",
                "fas fa-user-ninja", 
                "fas fa-user-tie",
                "fas fa-user-graduate",
                "fas fa-user-secret",
                "fas fa-user-md",
                "fas fa-user-robot",
                "fas fa-user-shield"
            ]
            
            new_avatar = random.choice(avatars)
            
            # Supprimer l'ancien fichier avatar s'il existe
            users_collection = db["utilisateurs"]
            user = users_collection.find_one({"username": session["username"]})
            if user.get("avatar_file"):
                old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], user["avatar_file"])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Sauvegarder dans la base de données
            users_collection.update_one(
                {"username": session["username"]},
                {"$set": {
                    "avatar": new_avatar,
                    "avatar_type": "icon",
                    "updated_at": datetime.now()
                }, "$unset": {"avatar_file": ""}}
            )
            
            # Mettre à jour la session
            session["user_avatar"] = new_avatar
            session["avatar_type"] = "icon"
            
            from utils import log_user_action
            log_user_action(db, session["username"], "avatar_change", "Avatar icône modifié")
            
            return jsonify({
                "success": True,
                "message": "Avatar mis à jour avec succès !",
                "avatar": new_avatar,
                "type": "icon"
            })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/security")
@admin_required
def admin_security():
    """Interface de sécurité pour les administrateurs"""
    try:
        # Statistiques de sécurité
        users_collection = db["utilisateurs"]
        logs_collection = db["user_logs"]
        
        # Compter les tentatives de connexion échouées récentes (24h)
        yesterday = datetime.now() - timedelta(days=1)
        failed_logins = logs_collection.count_documents({
            "action": "login_failed",
            "timestamp": {"$gte": yesterday}
        })
        
        # Sessions actives
        active_sessions = users_collection.count_documents({
            "last_login": {"$gte": yesterday}
        })
        
        # Utilisateurs créés récemment (7 jours)
        week_ago = datetime.now() - timedelta(days=7)
        new_users = users_collection.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        # Activités suspectes (tentatives multiples)
        suspicious_activities = list(logs_collection.aggregate([
            {"$match": {"action": "login_failed", "timestamp": {"$gte": yesterday}}},
            {"$group": {"_id": "$username", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 3}}},
            {"$sort": {"count": -1}}
        ]))
        
        # Logs récents
        recent_logs = list(logs_collection.find().sort("timestamp", -1).limit(50))
        
        security_stats = {
            "failed_logins": failed_logins,
            "active_sessions": active_sessions,
            "new_users": new_users,
            "suspicious_count": len(suspicious_activities)
        }
        
        return render_template("admin_security.html", 
                             security_stats=security_stats,
                             suspicious_activities=suspicious_activities,
                             recent_logs=recent_logs)
                             
    except Exception as e:
        return f"<h2>Erreur dans l'interface sécurité :</h2><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route("/admin/security/block_user", methods=["POST"])
@admin_required
def block_user():
    """Bloquer un utilisateur"""
    data = request.get_json()
    username = data.get("username")
    
    if not username or username == session["username"]:
        return jsonify({"error": "Action non autorisée"}), 400
    
    users_collection = db["utilisateurs"]
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"blocked": True, "blocked_at": datetime.now(), "blocked_by": session["username"]}}
    )
    
    if result.modified_count > 0:
        from utils import log_user_action
        log_user_action(db, session["username"], "user_blocked", f"Utilisateur {username} bloqué")
        return jsonify({"success": f"Utilisateur {username} bloqué avec succès"})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

@app.route("/admin/security/unblock_user", methods=["POST"])
@admin_required
def unblock_user():
    """Débloquer un utilisateur"""
    data = request.get_json()
    username = data.get("username")
    
    users_collection = db["utilisateurs"]
    result = users_collection.update_one(
        {"username": username},
        {"$unset": {"blocked": "", "blocked_at": "", "blocked_by": ""}}
    )
    
    if result.modified_count > 0:
        from utils import log_user_action
        log_user_action(db, session["username"], "user_unblocked", f"Utilisateur {username} débloqué")
        return jsonify({"success": f"Utilisateur {username} débloqué avec succès"})
    else:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

@app.route("/admin/security/clear_logs", methods=["POST"])
@admin_required
def clear_security_logs():
    """Nettoyer les anciens logs"""
    data = request.get_json()
    days = data.get("days", 30)
    
    cutoff_date = datetime.now() - timedelta(days=days)
    logs_collection = db["user_logs"]
    
    result = logs_collection.delete_many({"timestamp": {"$lt": cutoff_date}})
    
    from utils import log_user_action
    log_user_action(db, session["username"], "logs_cleared", f"Logs supprimés: {result.deleted_count} entrées")
    
    return jsonify({"success": f"{result.deleted_count} logs supprimés"})

# Initialiser l'authentification biométrique
biometric_auth = BiometricAuth(db)

@app.route("/api/biometric/register/start", methods=["POST"])
@login_required
def biometric_register_start():
    """Démarrer l'enregistrement biométrique"""
    try:
        username = session.get("username")
        if not username:
            return jsonify({"success": False, "error": "Non connecté"}), 401
        
        result = biometric_auth.register_start(username)
        return jsonify(result)
    except Exception as e:
        print(f"Erreur biometric_register_start: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/biometric/register/complete", methods=["POST"])
@login_required
def biometric_register_complete():
    """Compléter l'enregistrement biométrique"""
    try:
        print("=== DEBUG biometric_register_complete ===")
        data = request.get_json()
        print(f"Data reçue: {data}")
        
        username = session.get("username")
        credential = data.get("credential")
        
        print(f"Username: {username}")
        print(f"Credential keys: {credential.keys() if credential else 'None'}")
        
        if not username or not credential:
            return jsonify({"success": False, "error": "Données manquantes"}), 400
        
        result = biometric_auth.register_complete(username, credential)
        print(f"Résultat: {result}")
        
        if result["success"]:
            # Logger l'action
            from utils import log_user_action
            log_user_action(db, username, "biometric_setup", "Configuration empreinte réussie")
        
        return jsonify(result)
    except Exception as e:
        print(f"Erreur biometric_register_complete: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/biometric/login/start", methods=["POST"])
def biometric_login_start():
    """Démarrer l'authentification biométrique"""
    try:
        print("=== DEBUG biometric_login_start ===")
        data = request.get_json()
        username = data.get("username")
        
        print(f"Username reçu: {username}")
        
        if not username:
            return jsonify({"success": False, "error": "Nom d'utilisateur manquant"}), 400
        
        # Vérifier si l'utilisateur existe
        users_collection = db["utilisateurs"]
        user = users_collection.find_one({"username": username})
        
        if not user:
            return jsonify({"success": False, "error": "Utilisateur non trouvé"}), 404
        
        # Vérifier si l'utilisateur est bloqué
        if user.get("blocked"):
            return jsonify({"success": False, "error": "Compte bloqué"}), 403
        
        # Démarrer l'authentification biométrique
        result = biometric_auth.login_start(username)
        print(f"Résultat login_start: {result}")
        
        if result["success"]:
            # Stocker temporairement le username pour la complétion
            session["temp_biometric_username"] = username
        
        return jsonify(result)
    except Exception as e:
        print(f"Erreur biometric_login_start: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/biometric/login/complete", methods=["POST"])
def biometric_login_complete():
    """Compléter l'authentification biométrique"""
    try:
        print("=== DEBUG biometric_login_complete ===")
        data = request.get_json()
        
        # Récupérer le username temporaire
        username = data.get("username") or session.get("temp_biometric_username")
        assertion = data.get("assertion")
        
        print(f"Username: {username}")
        print(f"Assertion keys: {assertion.keys() if assertion else 'None'}")
        
        if not username or not assertion:
            return jsonify({"success": False, "error": "Données manquantes"}), 400
        
        # Vérifier l'assertion
        result = biometric_auth.login_complete(username, assertion)
        print(f"Résultat login_complete: {result}")
        
        if result["success"]:
            # Récupérer les infos utilisateur
            users_collection = db["utilisateurs"]
            user = users_collection.find_one({"username": username})
            
            if not user:
                return jsonify({"success": False, "error": "Utilisateur non trouvé"}), 404
            
            # Connecter l'utilisateur
            session["logged_in"] = True
            session["username"] = username
            session["role"] = user.get("role", "user")
            
            # Gérer l'avatar
            if user.get("avatar_type") == "file" and user.get("avatar_file"):
                session["user_avatar"] = f"/static/uploads/avatars/{user['avatar_file']}"
                session["avatar_type"] = "file"
            else:
                session["user_avatar"] = user.get("avatar", "fas fa-user-circle")
                session["avatar_type"] = "icon"
            
            session.permanent = True
            
            # Mettre à jour la dernière connexion
            users_collection.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.now()}}
            )
            
            # Logger l'action
            from utils import log_user_action
            log_user_action(db, username, "login_biometric", "Connexion par empreinte réussie")
            
            # Nettoyer la session temporaire
            if "temp_biometric_username" in session:
                session.pop("temp_biometric_username")
            
            return jsonify({
                "success": True, 
                "message": "Connexion réussie", 
                "redirect": url_for("index")
            })
        else:
            return jsonify(result)
        
    except Exception as e:
        print(f"Erreur biometric_login_complete: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/biometric/status")
@login_required
def biometric_status():
    username = session["username"]
    has_biometric = biometric_auth.has_biometric(username)
    return jsonify({"has_biometric": has_biometric})

# Page de configuration de l'empreinte
@app.route("/biometric_setup")
@login_required
def biometric_setup():
    return render_template("biometric_setup.html")

# ==================== SYSTÈME DE NOTIFICATIONS EN TEMPS RÉEL ====================

@socketio.on('connect')
def handle_connect():
    if session.get('logged_in'):
        username = session.get('username')
        join_room(username)
        print(f"[SocketIO] {username} connecté aux notifications")

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username', 'unknown')
    print(f"[SocketIO] {username} déconnecté")

def send_notification(recipient, notif_type, title, message, link=None):
    """Envoie une notification en temps réel et la sauvegarde en base"""
    notification = {
        "recipient": recipient,
        "type": notif_type,
        "title": title,
        "message": message,
        "link": link,
        "read": False,
        "created_at": datetime.now()
    }
    db["notifications"].insert_one(notification)
    # Émettre en temps réel vers l'utilisateur
    notification["_id"] = str(notification["_id"])
    notification["created_at"] = notification["created_at"].strftime("%d/%m/%Y %H:%M")
    socketio.emit('new_notification', notification, room=recipient)

@app.route("/notifications")
@admin_required
def notifications_page():
    username = session["username"]
    notifications = list(db["notifications"].find(
        {"recipient": username}
    ).sort("created_at", -1).limit(50))
    for n in notifications:
        n["_id"] = str(n["_id"])
    return render_template("notifications.html", notifications=notifications)

@app.route("/api/notifications")
@admin_required
def get_notifications():
    username = session["username"]
    notifications = list(db["notifications"].find(
        {"recipient": username}
    ).sort("created_at", -1).limit(20))
    for n in notifications:
        n["_id"] = str(n["_id"])
        n["created_at"] = n["created_at"].strftime("%d/%m/%Y %H:%M")
    return jsonify({"notifications": notifications})

@app.route("/api/notifications/unread_count")
@admin_required
def unread_count():
    username = session["username"]
    count = db["notifications"].count_documents({"recipient": username, "read": False})
    return jsonify({"count": count})

@app.route("/api/notifications/mark_read", methods=["POST"])
@admin_required
def mark_notification_read():
    notif_id = request.json.get("id")
    if notif_id:
        db["notifications"].update_one(
            {"_id": ObjectId(notif_id), "recipient": session["username"]},
            {"$set": {"read": True}}
        )
    return jsonify({"success": True})

@app.route("/api/notifications/mark_all_read", methods=["POST"])
@admin_required
def mark_all_read():
    username = session["username"]
    db["notifications"].update_many(
        {"recipient": username, "read": False},
        {"$set": {"read": True}}
    )
    return jsonify({"success": True})

@app.route("/api/notifications/send", methods=["POST"])
@admin_required
def admin_send_notification():
    """Permet à l'admin d'envoyer une notification à un utilisateur"""
    data = request.json
    recipient = data.get("recipient")
    title = data.get("title")
    message = data.get("message")
    
    if not all([recipient, title, message]):
        return jsonify({"success": False, "error": "Champs manquants"}), 400
    
    # Vérifier que l'utilisateur existe
    user = db["utilisateurs"].find_one({"username": recipient})
    if not user:
        return jsonify({"success": False, "error": "Utilisateur non trouvé"}), 404
    
    send_notification(recipient, "admin_message", title, message)
    return jsonify({"success": True})

@app.route("/api/notifications/broadcast", methods=["POST"])
@admin_required
def admin_broadcast_notification():
    """Envoie une notification à tous les utilisateurs"""
    data = request.json
    title = data.get("title")
    message = data.get("message")
    
    if not all([title, message]):
        return jsonify({"success": False, "error": "Champs manquants"}), 400
    
    users = db["utilisateurs"].find({}, {"username": 1})
    count = 0
    for user in users:
        send_notification(user["username"], "broadcast", title, message)
        count += 1
    
    return jsonify({"success": True, "sent_to": count})

@app.route("/api/notifications/delete", methods=["POST"])
@admin_required
def delete_notification():
    notif_id = request.json.get("id")
    if notif_id:
        db["notifications"].delete_one(
            {"_id": ObjectId(notif_id), "recipient": session["username"]}
        )
    return jsonify({"success": True})

# ==================== ROADMAP DE FORMATION PERSONNALISÉE ====================

FORMATION_ROADMAPS = {
    "Python": {
        "phases": [
            {
                "title": "Fondamentaux",
                "duration": "4-6 semaines",
                "icon": "fas fa-seedling",
                "color": "#28a745",
                "skills": [
                    {"name": "Syntaxe Python & types de données", "type": "théorie"},
                    {"name": "Structures de contrôle & fonctions", "type": "théorie"},
                    {"name": "POO : classes, héritage, polymorphisme", "type": "pratique"},
                    {"name": "Projet : CLI tool (gestionnaire de tâches)", "type": "projet"},
                ]
            },
            {
                "title": "Développement Web",
                "duration": "6-8 semaines",
                "icon": "fas fa-globe",
                "color": "#667eea",
                "skills": [
                    {"name": "Flask/Django : routes, templates, formulaires", "type": "théorie"},
                    {"name": "APIs REST : CRUD, authentification", "type": "pratique"},
                    {"name": "Bases de données : SQL & MongoDB", "type": "pratique"},
                    {"name": "Projet : Application web complète", "type": "projet"},
                ]
            },
            {
                "title": "Data & Automatisation",
                "duration": "6-8 semaines",
                "icon": "fas fa-chart-bar",
                "color": "#fd7e14",
                "skills": [
                    {"name": "Pandas, NumPy : manipulation de données", "type": "théorie"},
                    {"name": "Visualisation : Matplotlib, Seaborn", "type": "pratique"},
                    {"name": "Scripting & automatisation", "type": "pratique"},
                    {"name": "Projet : Dashboard d'analyse de données", "type": "projet"},
                ]
            },
            {
                "title": "Spécialisation & Portfolio",
                "duration": "4-6 semaines",
                "icon": "fas fa-trophy",
                "color": "#dc3545",
                "skills": [
                    {"name": "Tests unitaires & CI/CD", "type": "pratique"},
                    {"name": "Docker & déploiement cloud", "type": "pratique"},
                    {"name": "Contribution open source", "type": "pratique"},
                    {"name": "Projet final : Application déployée", "type": "projet"},
                ]
            }
        ],
        "resources": ["Real Python", "Python.org Docs", "Exercism", "LeetCode"],
        "certifications": ["PCEP", "PCAP", "AWS Cloud Practitioner"]
    },
    "JavaScript": {
        "phases": [
            {
                "title": "Bases du Langage",
                "duration": "3-4 semaines",
                "icon": "fas fa-seedling",
                "color": "#28a745",
                "skills": [
                    {"name": "Variables, types, fonctions, scope", "type": "théorie"},
                    {"name": "DOM manipulation & événements", "type": "pratique"},
                    {"name": "Asynchrone : Promises, async/await", "type": "théorie"},
                    {"name": "Projet : Page web interactive", "type": "projet"},
                ]
            },
            {
                "title": "Framework Front-end",
                "duration": "6-8 semaines",
                "icon": "fas fa-layer-group",
                "color": "#667eea",
                "skills": [
                    {"name": "React.js : composants, hooks, state", "type": "théorie"},
                    {"name": "Routing, context API, formulaires", "type": "pratique"},
                    {"name": "Tailwind CSS / Material UI", "type": "pratique"},
                    {"name": "Projet : Single Page Application", "type": "projet"},
                ]
            },
            {
                "title": "Back-end & Full-Stack",
                "duration": "5-6 semaines",
                "icon": "fas fa-server",
                "color": "#fd7e14",
                "skills": [
                    {"name": "Node.js & Express : API REST", "type": "théorie"},
                    {"name": "Base de données : MongoDB, PostgreSQL", "type": "pratique"},
                    {"name": "Authentification JWT & sécurité", "type": "pratique"},
                    {"name": "Projet : API back-end complète", "type": "projet"},
                ]
            },
            {
                "title": "Déploiement & Carrière",
                "duration": "3-4 semaines",
                "icon": "fas fa-trophy",
                "color": "#dc3545",
                "skills": [
                    {"name": "Testing : Jest, Cypress", "type": "pratique"},
                    {"name": "Déploiement : Vercel, Netlify, AWS", "type": "pratique"},
                    {"name": "TypeScript : typage avancé", "type": "théorie"},
                    {"name": "Projet final : App full-stack déployée", "type": "projet"},
                ]
            }
        ],
        "resources": ["MDN Web Docs", "JavaScript.info", "FreeCodeCamp", "Frontend Mentor"],
        "certifications": ["Meta Front-End Developer", "AWS Developer Associate"]
    },
    "Data Science": {
        "phases": [
            {
                "title": "Mathématiques & Stats",
                "duration": "4-6 semaines",
                "icon": "fas fa-calculator",
                "color": "#28a745",
                "skills": [
                    {"name": "Algèbre linéaire & calcul matriciel", "type": "théorie"},
                    {"name": "Statistiques descriptives & inférentielles", "type": "théorie"},
                    {"name": "Probabilités & distributions", "type": "théorie"},
                    {"name": "Projet : Analyse statistique d'un dataset", "type": "projet"},
                ]
            },
            {
                "title": "Manipulation de Données",
                "duration": "6-8 semaines",
                "icon": "fas fa-database",
                "color": "#667eea",
                "skills": [
                    {"name": "Python : Pandas, NumPy avancé", "type": "pratique"},
                    {"name": "Nettoyage & transformation de données", "type": "pratique"},
                    {"name": "Visualisation : Matplotlib, Plotly, Seaborn", "type": "pratique"},
                    {"name": "Projet : EDA complet sur dataset réel", "type": "projet"},
                ]
            },
            {
                "title": "Machine Learning",
                "duration": "8-10 semaines",
                "icon": "fas fa-brain",
                "color": "#fd7e14",
                "skills": [
                    {"name": "Régression, classification, clustering", "type": "théorie"},
                    {"name": "Scikit-learn : pipelines, validation croisée", "type": "pratique"},
                    {"name": "Deep Learning : TensorFlow/PyTorch intro", "type": "pratique"},
                    {"name": "Projet : Modèle ML déployé (API)", "type": "projet"},
                ]
            },
            {
                "title": "Spécialisation",
                "duration": "6-8 semaines",
                "icon": "fas fa-trophy",
                "color": "#dc3545",
                "skills": [
                    {"name": "NLP ou Computer Vision (au choix)", "type": "théorie"},
                    {"name": "MLOps : MLflow, Docker, CI/CD", "type": "pratique"},
                    {"name": "Big Data : Spark, cloud (GCP/AWS)", "type": "pratique"},
                    {"name": "Projet final : Pipeline ML end-to-end", "type": "projet"},
                ]
            }
        ],
        "resources": ["Kaggle", "Coursera (Andrew Ng)", "Towards Data Science", "Fast.ai"],
        "certifications": ["Google Data Analytics", "IBM Data Science", "TensorFlow Developer"]
    },
    "DevOps": {
        "phases": [
            {
                "title": "Fondamentaux Système",
                "duration": "4-5 semaines",
                "icon": "fas fa-terminal",
                "color": "#28a745",
                "skills": [
                    {"name": "Linux : commandes, shell scripting", "type": "théorie"},
                    {"name": "Réseau : TCP/IP, DNS, HTTP, ports", "type": "théorie"},
                    {"name": "Git avancé : branching, merge, rebase", "type": "pratique"},
                    {"name": "Projet : Scripts d'automatisation serveur", "type": "projet"},
                ]
            },
            {
                "title": "Conteneurisation & Orchestration",
                "duration": "6-8 semaines",
                "icon": "fas fa-docker",
                "color": "#667eea",
                "skills": [
                    {"name": "Docker : images, volumes, networks", "type": "théorie"},
                    {"name": "Docker Compose : multi-services", "type": "pratique"},
                    {"name": "Kubernetes : pods, services, deployments", "type": "pratique"},
                    {"name": "Projet : App multi-conteneurs orchestrée", "type": "projet"},
                ]
            },
            {
                "title": "CI/CD & Infrastructure",
                "duration": "6-8 semaines",
                "icon": "fas fa-infinity",
                "color": "#fd7e14",
                "skills": [
                    {"name": "GitHub Actions / GitLab CI / Jenkins", "type": "pratique"},
                    {"name": "Terraform / Ansible : IaC", "type": "pratique"},
                    {"name": "Cloud : AWS/GCP/Azure services essentiels", "type": "théorie"},
                    {"name": "Projet : Pipeline CI/CD complet", "type": "projet"},
                ]
            },
            {
                "title": "Monitoring & SRE",
                "duration": "4-6 semaines",
                "icon": "fas fa-trophy",
                "color": "#dc3545",
                "skills": [
                    {"name": "Monitoring : Prometheus, Grafana", "type": "pratique"},
                    {"name": "Logging : ELK Stack / Loki", "type": "pratique"},
                    {"name": "SRE : SLOs, incident response, chaos engineering", "type": "théorie"},
                    {"name": "Projet final : Infra monitorée complète", "type": "projet"},
                ]
            }
        ],
        "resources": ["KodeKloud", "Linux Academy", "Docker Docs", "Kubernetes.io"],
        "certifications": ["CKA (Kubernetes)", "AWS Solutions Architect", "Terraform Associate"]
    },
    "Cybersécurité": {
        "phases": [
            {
                "title": "Fondamentaux Sécurité",
                "duration": "5-6 semaines",
                "icon": "fas fa-shield-alt",
                "color": "#28a745",
                "skills": [
                    {"name": "Concepts : CIA, authentification, chiffrement", "type": "théorie"},
                    {"name": "Réseau : protocoles, pare-feu, VPN", "type": "théorie"},
                    {"name": "Linux sécurité : permissions, logs, hardening", "type": "pratique"},
                    {"name": "Projet : Audit de sécurité basique", "type": "projet"},
                ]
            },
            {
                "title": "Tests de Pénétration",
                "duration": "8-10 semaines",
                "icon": "fas fa-bug",
                "color": "#667eea",
                "skills": [
                    {"name": "OWASP Top 10 : vulnérabilités web", "type": "théorie"},
                    {"name": "Outils : Burp Suite, Nmap, Metasploit", "type": "pratique"},
                    {"name": "Pentest web : SQLi, XSS, CSRF", "type": "pratique"},
                    {"name": "Projet : Rapport de pentest (lab)", "type": "projet"},
                ]
            },
            {
                "title": "Défense & SOC",
                "duration": "6-8 semaines",
                "icon": "fas fa-eye",
                "color": "#fd7e14",
                "skills": [
                    {"name": "SIEM : Splunk, QRadar, Wazuh", "type": "pratique"},
                    {"name": "Analyse de malware & forensics", "type": "pratique"},
                    {"name": "Incident response & threat hunting", "type": "théorie"},
                    {"name": "Projet : Détection d'intrusion (lab)", "type": "projet"},
                ]
            },
            {
                "title": "Spécialisation & Certification",
                "duration": "6-8 semaines",
                "icon": "fas fa-trophy",
                "color": "#dc3545",
                "skills": [
                    {"name": "Cloud Security : AWS/Azure security", "type": "pratique"},
                    {"name": "DevSecOps : SAST, DAST, pipelines sécurisés", "type": "pratique"},
                    {"name": "GRC : conformité, RGPD, ISO 27001", "type": "théorie"},
                    {"name": "Projet final : Architecture sécurisée complète", "type": "projet"},
                ]
            }
        ],
        "resources": ["TryHackMe", "HackTheBox", "PortSwigger Academy", "SANS"],
        "certifications": ["CompTIA Security+", "CEH", "OSCP", "CISSP"]
    }
}


def generate_personalized_roadmap(formation, age, experience):
    """Génère une roadmap personnalisée basée sur le profil"""
    roadmap = FORMATION_ROADMAPS.get(formation)
    
    # Si pas trouvé exactement, chercher par correspondance partielle
    if not roadmap:
        formation_lower = formation.lower()
        for key, value in FORMATION_ROADMAPS.items():
            if key.lower() in formation_lower or formation_lower in key.lower():
                roadmap = value
                formation = key
                break
    
    # Si toujours pas trouvé, générer une roadmap générique
    if not roadmap:
        roadmap = {
            "phases": [
                {
                    "title": "Fondamentaux",
                    "duration": "4-6 semaines",
                    "icon": "fas fa-seedling",
                    "color": "#28a745",
                    "skills": [
                        {"name": f"Introduction à {formation}", "type": "théorie"},
                        {"name": "Concepts de base et terminologie", "type": "théorie"},
                        {"name": "Premiers exercices pratiques", "type": "pratique"},
                        {"name": "Projet : mise en pratique des fondamentaux", "type": "projet"},
                    ]
                },
                {
                    "title": "Approfondissement",
                    "duration": "4-8 semaines",
                    "icon": "fas fa-chart-line",
                    "color": "#667eea",
                    "skills": [
                        {"name": "Concepts intermédiaires", "type": "théorie"},
                        {"name": "Techniques avancées", "type": "pratique"},
                        {"name": "Étude de cas réels", "type": "pratique"},
                        {"name": "Projet : application complète", "type": "projet"},
                    ]
                },
                {
                    "title": "Maîtrise & Certification",
                    "duration": "4-6 semaines",
                    "icon": "fas fa-trophy",
                    "color": "#fd7e14",
                    "skills": [
                        {"name": "Sujets avancés et spécialisation", "type": "théorie"},
                        {"name": "Projet final professionnel", "type": "projet"},
                        {"name": "Préparation certification", "type": "pratique"},
                        {"name": "Portfolio et mise en production", "type": "projet"},
                    ]
                }
            ],
            "resources": [
                {"name": f"Documentation officielle {formation}", "type": "documentation"},
                {"name": "Tutoriels en ligne", "type": "cours"},
                {"name": "Communauté et forums", "type": "communauté"},
            ],
            "certifications": [f"Certification {formation}"]
        }

    # Personnalisation selon le profil
    tips = []
    pace = "normal"

    if experience < 2:
        tips.append("Prenez votre temps sur les fondamentaux, ils sont essentiels")
        tips.append("Pratiquez chaque jour, même 30 minutes")
        pace = "progressif"
    elif experience >= 5:
        tips.append("Vous pouvez accélérer les phases 1 et 2")
        tips.append("Concentrez-vous sur les projets avancés")
        pace = "accéléré"

    if age < 25:
        tips.append("Profitez de votre flexibilité pour faire des stages/alternances")
        tips.append("Participez à des hackathons et meetups")
    elif age > 40:
        tips.append("Valorisez votre expérience professionnelle dans vos projets")
        tips.append("Privilégiez les formations certifiantes reconnues")

    total_weeks = 0
    for phase in roadmap["phases"]:
        duration = phase["duration"]
        weeks = int(duration.split("-")[1].split(" ")[0])
        total_weeks += weeks

    return {
        "formation": formation,
        "phases": roadmap["phases"],
        "resources": roadmap["resources"],
        "certifications": roadmap["certifications"],
        "tips": tips,
        "pace": pace,
        "total_duration": f"{total_weeks // 4}-{(total_weeks + 4) // 4} mois"
    }


@app.route("/roadmap")
@login_required
def roadmap_page():
    """Page de roadmap personnalisée"""
    formation = request.args.get("formation")
    age = request.args.get("age", type=int, default=25)
    experience = request.args.get("experience", type=int, default=0)

    # Si pas de formation spécifiée, récupérer la dernière prédiction de l'utilisateur
    if not formation:
        last_pred = collection.find_one(
            {"created_by": session["username"]},
            sort=[("created_at", -1)]
        )
        if last_pred:
            formation = last_pred.get("formation_suggeree", "Python")
            age = last_pred.get("age", 25)
            experience = last_pred.get("experience", 0)
        else:
            formation = "Python"

    roadmap = generate_personalized_roadmap(formation, age, experience)
    all_formations = list(FORMATION_ROADMAPS.keys())

    return render_template("roadmap.html",
                           roadmap=roadmap,
                           all_formations=all_formations,
                           selected_formation=formation,
                           age=age,
                           experience=experience)


@app.route("/api/roadmap", methods=["POST"])
@login_required
def api_roadmap():
    """API pour générer une roadmap"""
    data = request.get_json()
    formation = data.get("formation")
    age = data.get("age", 25)
    experience = data.get("experience", 0)

    if not formation:
        return jsonify({"error": "Formation requise"}), 400

    roadmap = generate_personalized_roadmap(formation, age, experience)

    return jsonify({"success": True, "roadmap": roadmap})


@app.route("/api/roadmap/formations")
@login_required
def api_roadmap_formations():
    """Retourne la liste des formations disponibles pour les roadmaps"""
    formations = list(FORMATION_ROADMAPS.keys())
    return jsonify({"success": True, "formations": formations})


@app.route("/api/roadmap/start", methods=["POST"])
@login_required
def start_roadmap():
    """Démarrer une roadmap - sauvegarder dans MongoDB"""
    data = request.get_json()
    formation = data.get("formation")
    age = data.get("age", 25)
    experience = data.get("experience", 0)

    if formation not in FORMATION_ROADMAPS:
        return jsonify({"error": "Formation non trouvée"}), 404

    username = session["username"]

    # Vérifier si l'utilisateur a déjà une roadmap pour cette formation
    existing = db["roadmaps"].find_one({"username": username, "formation": formation})
    if existing:
        return jsonify({"success": True, "roadmap_id": str(existing["_id"]), "message": "Roadmap existante"})

    roadmap_data = {
        "username": username,
        "formation": formation,
        "age": age,
        "experience": experience,
        "started_at": datetime.now(),
        "completed_steps": [],
        "progress": 0,
        "status": "in_progress"
    }
    result = db["roadmaps"].insert_one(roadmap_data)

    send_notification(username, "info", "Roadmap démarrée",
                      f"Votre parcours {formation} a commencé !", link="/roadmap")

    return jsonify({"success": True, "roadmap_id": str(result.inserted_id)})


@app.route("/api/roadmap/progress", methods=["POST"])
@login_required
def update_roadmap_progress():
    """Marquer une étape comme terminée"""
    data = request.get_json()
    formation = data.get("formation")
    phase_index = data.get("phase_index")
    skill_index = data.get("skill_index")

    username = session["username"]
    step_key = f"{phase_index}_{skill_index}"

    roadmap_doc = db["roadmaps"].find_one({"username": username, "formation": formation})

    if not roadmap_doc:
        # Créer la roadmap si elle n'existe pas
        roadmap_doc = {
            "username": username,
            "formation": formation,
            "started_at": datetime.now(),
            "completed_steps": [],
            "progress": 0,
            "status": "in_progress"
        }
        db["roadmaps"].insert_one(roadmap_doc)

    completed = roadmap_doc.get("completed_steps", [])

    if step_key in completed:
        # Dé-cocher
        completed.remove(step_key)
    else:
        # Cocher
        completed.append(step_key)

    # Calculer la progression
    roadmap_def = FORMATION_ROADMAPS.get(formation)
    if roadmap_def:
        total_steps = sum(len(phase.get("skills", phase.get("steps", []))) for phase in roadmap_def["phases"])
    else:
        total_steps = max(len(completed), 1)
    progress = round((len(completed) / total_steps) * 100) if total_steps > 0 else 0

    status = "completed" if progress == 100 else "in_progress"

    db["roadmaps"].update_one(
        {"username": username, "formation": formation},
        {"$set": {"completed_steps": completed, "progress": progress, "status": status,
                  "updated_at": datetime.now()}}
    )

    if progress == 100:
        send_notification(username, "success", "Roadmap terminée !",
                          f"Félicitations ! Vous avez terminé le parcours {formation} !",
                          link="/roadmap")

    return jsonify({"success": True, "progress": progress, "completed_steps": completed, "status": status})


@app.route("/api/roadmap/user_progress")
@login_required
def get_user_roadmap_progress():
    """Récupérer la progression de l'utilisateur"""
    username = session["username"]
    formation = request.args.get("formation")

    if formation:
        doc = db["roadmaps"].find_one({"username": username, "formation": formation}, {"_id": 0})
        return jsonify({"success": True, "roadmap": doc})
    else:
        docs = list(db["roadmaps"].find({"username": username}, {"_id": 0}))
        return jsonify({"success": True, "roadmaps": docs})


@app.route("/admin/roadmaps")
@admin_required
def admin_roadmaps():
    """Page admin : vue d'ensemble des roadmaps"""
    all_roadmaps = list(db["roadmaps"].find().sort("started_at", -1))
    for r in all_roadmaps:
        r["_id"] = str(r["_id"])

    # Statistiques
    total_roadmaps = len(all_roadmaps)
    completed_count = sum(1 for r in all_roadmaps if r.get("status") == "completed")
    in_progress_count = total_roadmaps - completed_count
    avg_progress = round(sum(r.get("progress", 0) for r in all_roadmaps) / max(total_roadmaps, 1))

    # Formations les plus suivies
    formation_counts = {}
    for r in all_roadmaps:
        f = r.get("formation", "Inconnu")
        formation_counts[f] = formation_counts.get(f, 0) + 1

    return render_template("admin_roadmaps.html",
                           roadmaps=all_roadmaps,
                           total_roadmaps=total_roadmaps,
                           completed_count=completed_count,
                           in_progress_count=in_progress_count,
                           avg_progress=avg_progress,
                           formation_counts=formation_counts)


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5555)
