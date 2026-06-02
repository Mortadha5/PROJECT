from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
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
    "Python": {
        "description": "Programmation orientée objet, développement web, data science",
        "duration": "6-8 mois",
        "difficulty": "Intermédiaire",
        "salary_range": "45000-75000€",
        "job_opportunities": "Très élevées",
        "skills": ["Logique", "Résolution de problèmes", "Analyse"],
        "industries": ["Tech", "Finance", "Santé", "E-commerce"]
    },
    "JavaScript": {
        "description": "Développement front-end, frameworks modernes, applications web",
        "duration": "4-6 mois",
        "difficulty": "Intermédiaire",
        "salary_range": "40000-70000€",
        "job_opportunities": "Très élevées",
        "skills": ["Créativité", "Logique", "Design"],
        "industries": ["Web", "Mobile", "Gaming", "E-commerce"]
    },
    "Data Science": {
        "description": "Analyse de données, machine learning, visualisation",
        "duration": "8-12 mois",
        "difficulty": "Avancé",
        "salary_range": "55000-95000€",
        "job_opportunities": "Élevées",
        "skills": ["Mathématiques", "Statistiques", "Analyse"],
        "industries": ["Tech", "Finance", "Recherche", "Santé"]
    },
    "DevOps": {
        "description": "Automatisation, conteneurisation, déploiement continu",
        "duration": "6-9 mois",
        "difficulty": "Avancé",
        "salary_range": "50000-85000€",
        "job_opportunities": "Élevées",
        "skills": ["Automatisation", "Système", "Réseau"],
        "industries": ["Tech", "Cloud", "Infrastructure"]
    },
    "Cybersécurité": {
        "description": "Sécurité informatique, tests de pénétration, audit",
        "duration": "9-12 mois",
        "difficulty": "Avancé",
        "salary_range": "55000-90000€",
        "job_opportunities": "Très élevées",
        "skills": ["Sécurité", "Analyse", "Investigation"],
        "industries": ["Sécurité", "Finance", "Gouvernement"]
    }
}

def analyze_user_profile(age, experience, competence):
    """Analyse le profil utilisateur pour des recommandations personnalisées"""
    analysis = {
        "career_stage": "",
        "learning_capacity": "",
        "time_availability": "",
        "risk_tolerance": "",
        "recommendations": []
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
    
    return analysis

def calculate_recommendation_score(formation, age, experience, competence, base_probability):
    """Calcule un score personnalisé pour chaque recommandation"""
    details = FORMATION_DETAILS.get(formation, {})
    score = base_probability * 100
    
    # Ajustements basés sur l'âge
    if age < 30:
        if details.get("difficulty") == "Avancé":
            score += 5  # Bonus pour les jeunes sur formations avancées
    elif age > 40:
        if details.get("difficulty") == "Intermédiaire":
            score += 3  # Bonus pour formations moins risquées
    
    # Ajustements basés sur l'expérience
    if experience < 2:
        if details.get("difficulty") == "Intermédiaire":
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

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        role = request.form["role"]
        
        # Validation
        if len(username) < 3:
            error = "Le nom d'utilisateur doit contenir au moins 3 caractères"
        elif len(password) < 6:
            error = "Le mot de passe doit contenir au moins 6 caractères"
        elif role not in ["user", "admin"]:
            error = "Veuillez sélectionner un rôle valide"
        else:
            users_collection = db["utilisateurs"]
            if users_collection.find_one({"username": username}):
                error = "Ce nom d'utilisateur existe déjà"
            else:
                # Hasher le mot de passe
                from utils import hash_password, log_user_action
                hashed_password = hash_password(password)
                
                users_collection.insert_one({
                    "username": username,
                    "password": hashed_password,
                    "created_at": datetime.now(),
                    "role": role
                })
                
                role_text = "Administrateur" if role == "admin" else "Utilisateur"
                log_user_action(db, username, "register", f"Nouveau compte créé - Rôle: {role_text}")
                success = f"Compte {role_text} créé avec succès ! Vous pouvez maintenant vous connecter."

    return render_template("register.html", error=error, success=success)

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
def api_predict():
    data = request.get_json()
    age = data.get("age", 0)
    experience = data.get("experience", 0)
    competence = data.get("competence", "").lower()

    comp_encoded = comp_dict.get(competence, 0)
    features = np.array([[age, experience, comp_encoded]])
    pred = model.predict(features)[0]
    formation = inv_form_dict[pred]

    return jsonify({"formation_suggeree": formation})

@app.route("/api/predict_advanced", methods=["POST"])
@login_required
def predict_advanced():
    try:
        data = request.get_json()
        age = int(data.get("age", 0))
        experience = int(data.get("experience", 0))
        competence = data.get("competence", "").lower().strip()
        
        # Validation
        if not competence or competence not in comp_dict:
            return jsonify({"error": "Compétence non reconnue"}), 400
        
        # Prédiction avec probabilités
        comp_encoded = comp_dict.get(competence, 0)
        features = np.array([[age, experience, comp_encoded]])
        
        # Obtenir les probabilités pour toutes les classes
        probabilities = model.predict_proba(features)[0]
        classes = model.classes_
        
        # Créer les recommandations avec scores personnalisés
        recommendations = []
        for i, prob in enumerate(probabilities):
            if prob > 0.05:  # Seulement les formations avec probabilité > 5%
                formation_encoded = classes[i]
                formation = inv_form_dict[formation_encoded]
                
                # Calculer le score personnalisé
                custom_score = calculate_recommendation_score(
                    formation, age, experience, competence, prob
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
                        formation, age, experience, competence, custom_score
                    )
                })
        
        # Trier par score de confiance
        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        # Limiter aux 5 meilleures recommandations
        top_recommendations = recommendations[:5]
        
        # Analyse du profil
        profile_analysis = analyze_user_profile(age, experience, competence)
        
        # Sauvegarder la prédiction avancée
        prediction_data = {
            "nom": data.get("nom", ""),
            "prenom": data.get("prenom", ""),
            "age": age,
            "experience": experience,
            "competence": competence,
            "formation_suggeree": top_recommendations[0]["formation"] if top_recommendations else "Aucune",
            "confidence_score": top_recommendations[0]["confidence_score"] if top_recommendations else 0,
            "all_recommendations": [r["formation"] for r in top_recommendations[:3]],  # Top 3
            "created_by": session["username"],
            "created_at": datetime.now(),
            "prediction_type": "advanced"
        }
        
        collection.insert_one(prediction_data)
        
        # Envoyer une notification à l'utilisateur
        send_notification(
            session["username"],
            "prediction",
            "Nouvelle recommandation",
            f"Formation recommandée : {top_recommendations[0]['formation']} (score: {top_recommendations[0]['confidence_score']}%)",
            link="/mes_predictions"
        )
        
        return jsonify({
            "success": True,
            "recommendations": top_recommendations,
            "profile_analysis": profile_analysis,
            "total_analyzed": len(recommendations)
        })
        
    except Exception as e:
        print(f"Erreur prédiction avancée: {str(e)}")
        return jsonify({"error": f"Erreur lors de la prédiction: {str(e)}"}), 500

def generate_recommendation_reasons(formation, age, experience, competence, score):
    """Génère les raisons pour une recommandation"""
    reasons = []
    details = FORMATION_DETAILS.get(formation, {})
    
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
    
    if details.get("difficulty") == "Intermédiaire" and experience < 3:
        reasons.append("Niveau de difficulté adapté")
    
    return reasons[:3]  # Limiter à 3 raisons principales

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
@login_required
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
@login_required
def notifications_page():
    username = session["username"]
    notifications = list(db["notifications"].find(
        {"recipient": username}
    ).sort("created_at", -1).limit(50))
    for n in notifications:
        n["_id"] = str(n["_id"])
    return render_template("notifications.html", notifications=notifications)

@app.route("/api/notifications")
@login_required
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
@login_required
def unread_count():
    username = session["username"]
    count = db["notifications"].count_documents({"recipient": username, "read": False})
    return jsonify({"count": count})

@app.route("/api/notifications/mark_read", methods=["POST"])
@login_required
def mark_notification_read():
    notif_id = request.json.get("id")
    if notif_id:
        db["notifications"].update_one(
            {"_id": ObjectId(notif_id), "recipient": session["username"]},
            {"$set": {"read": True}}
        )
    return jsonify({"success": True})

@app.route("/api/notifications/mark_all_read", methods=["POST"])
@login_required
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
@login_required
def delete_notification():
    notif_id = request.json.get("id")
    if notif_id:
        db["notifications"].delete_one(
            {"_id": ObjectId(notif_id), "recipient": session["username"]}
        )
    return jsonify({"success": True})

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5555)
