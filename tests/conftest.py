import os
import tempfile
import pytest
from app import create_app
from app.db import init_db, get_db, close_db, seed_db # Added seed_db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'SECRET_KEY': 'test_secret_key', # Ensure a consistent secret key for testing sessions
        'WTF_CSRF_ENABLED': False, # Disable CSRF for simpler form testing, if applicable
    })

    with app.app_context():
        init_db() # Initialize the schema for the new database
        # You might want to seed some initial common data here if needed for all tests
        # e.g., common genres, tags, or a couple of users

    yield app

    # Close and remove the temporary database
    close_db()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def init_database(app):
    """Fixture to ensure the database is initialized and optionally seeded."""
    with app.app_context():
        # init_db() # Already called in app fixture, but can be called again if needed for specific state
        # For some tests, you might want a completely clean DB without seeds from app fixture
        # For others, you might want to seed specific data.
        pass # Database is initialized by the `app` fixture.
             # Seeding can be done here if specific baseline data is needed for a module/test.

@pytest.fixture
def seeded_database(app):
    """Fixture to ensure the database is initialized AND seeded with sample data."""
    with app.app_context():
        # init_db() # Ensure schema is clean if not already done by app fixture for this specific context
        seed_db() # Seed with sample data from db.py
    return app # Return app for context if needed, or just use for side effect


# --- Authentication Fixtures ---

class AuthActions:
    def __init__(self, client):
        self._client = client

    def register(self, username, email, password):
        return self._client.post(
            '/auth/register',
            data={'username': username, 'email': email, 'password': password}
        )

    def login(self, identifier, password): # identifier can be username or email
        return self._client.post(
            '/auth/login',
            data={'identifier': identifier, 'password': password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.get('/auth/logout', follow_redirects=True)


@pytest.fixture
def auth(client):
    """Provides an AuthActions object to simplify auth operations in tests."""
    return AuthActions(client)


@pytest.fixture
def user1_data():
    return {'username': 'testuser1', 'email': 'user1@example.com', 'password': 'password1'}

@pytest.fixture
def user2_data():
    return {'username': 'testuser2', 'email': 'user2@example.com', 'password': 'password2'}


@pytest.fixture
def registered_user1(app, auth, user1_data):
    """Registers user1 and returns their data. DB state is managed by app fixture."""
    with app.app_context(): # Ensure operations are within app context for db access
        auth.register(user1_data['username'], user1_data['email'], user1_data['password'])
    return user1_data

@pytest.fixture
def registered_user2(app, auth, user2_data):
    """Registers user2 and returns their data."""
    with app.app_context():
        auth.register(user2_data['username'], user2_data['email'], user2_data['password'])
    return user2_data


@pytest.fixture
def client_user1(client, auth, registered_user1):
    """A test client logged in as user1."""
    auth.login(registered_user1['username'], registered_user1['password'])
    yield client # client is now logged in
    auth.logout() # Ensure logout after test

@pytest.fixture
def client_user2(client, auth, registered_user2):
    """A test client logged in as user2."""
    auth.login(registered_user2['username'], registered_user2['password'])
    yield client
    auth.logout()

# Example of how to get a user ID from the database if needed in tests
def get_user_id(app, username):
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM Users WHERE username = ?", (username,)).fetchone()
        return user['id'] if user else None
