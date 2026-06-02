"""Tests pour les routes principales de l'application"""


def test_login_page_loads(client):
    """La page login doit être accessible"""
    response = client.get('/login')
    assert response.status_code == 200


def test_register_page_loads(client):
    """La page register doit être accessible"""
    response = client.get('/register')
    assert response.status_code == 200


def test_index_requires_login(client):
    """La page index redirige vers login si non connecté"""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location


def test_index_loads_when_authenticated(auth_client):
    """La page index se charge quand on est connecté"""
    response = auth_client.get('/')
    assert response.status_code == 200


def test_dashboard_requires_admin(auth_client):
    """Le dashboard est réservé aux admins"""
    response = auth_client.get('/dashboard')
    assert response.status_code == 403


def test_dashboard_loads_for_admin(admin_client):
    """Le dashboard se charge pour un admin"""
    response = admin_client.get('/dashboard')
    assert response.status_code == 200


def test_notifications_page_loads(auth_client):
    """La page notifications se charge"""
    response = auth_client.get('/notifications')
    assert response.status_code == 200


def test_notifications_unread_count(auth_client):
    """L'API unread_count retourne un JSON valide"""
    response = auth_client.get('/api/notifications/unread_count')
    assert response.status_code == 200
    data = response.get_json()
    assert 'count' in data


def test_notifications_api(auth_client):
    """L'API notifications retourne un JSON valide"""
    response = auth_client.get('/api/notifications')
    assert response.status_code == 200
    data = response.get_json()
    assert 'notifications' in data


def test_logout(auth_client):
    """Le logout redirige vers login"""
    response = auth_client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
