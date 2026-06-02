import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, socketio


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_client(client):
    """Client connecté en tant qu'utilisateur"""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'testuser'
        sess['role'] = 'user'
    return client


@pytest.fixture
def admin_client(client):
    """Client connecté en tant qu'admin"""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'admin'
        sess['role'] = 'admin'
    return client
