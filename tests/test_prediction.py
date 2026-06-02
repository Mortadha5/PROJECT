"""Tests pour l'API de prédiction"""
import json


def test_predict_api_requires_auth(client):
    """L'API predict nécessite une authentification"""
    response = client.post('/api/predict_advanced',
                           data=json.dumps({
                               "nom": "Test",
                               "prenom": "User",
                               "age": 25,
                               "experience": 3,
                               "competence": "python"
                           }),
                           content_type='application/json')
    assert response.status_code == 302


def test_predict_api_invalid_competence(auth_client):
    """L'API retourne une erreur pour une compétence invalide"""
    response = auth_client.post('/api/predict_advanced',
                                data=json.dumps({
                                    "nom": "Test",
                                    "prenom": "User",
                                    "age": 25,
                                    "experience": 3,
                                    "competence": "competence_inexistante"
                                }),
                                content_type='application/json')
    assert response.status_code == 400


def test_predict_api_success(auth_client):
    """L'API retourne une prédiction valide"""
    response = auth_client.post('/api/predict_advanced',
                                data=json.dumps({
                                    "nom": "Test",
                                    "prenom": "User",
                                    "age": 28,
                                    "experience": 3,
                                    "competence": "ia/ml, kubernetes"
                                }),
                                content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'recommendations' in data
    assert 'profile_analysis' in data
    assert len(data['recommendations']) > 0


def test_predict_api_returns_correct_structure(auth_client):
    """L'API retourne la structure attendue"""
    response = auth_client.post('/api/predict_advanced',
                                data=json.dumps({
                                    "nom": "Marie",
                                    "prenom": "Dupont",
                                    "age": 30,
                                    "experience": 5,
                                    "competence": "ia/ml, kubernetes"
                                }),
                                content_type='application/json')
    data = response.get_json()

    rec = data['recommendations'][0]
    assert 'formation' in rec
    assert 'confidence_score' in rec
    assert 'confidence_level' in rec
    assert 'details' in rec

    profile = data['profile_analysis']
    assert 'career_stage' in profile
    assert 'learning_capacity' in profile
    assert 'recommendations' in profile
