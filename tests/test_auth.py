import pytest
from flask import g, session
from app.db import get_db, find_user_by_username

# Registration Tests
def test_register(client, app, auth, user1_data):
    # Test GET request to register page
    assert client.get('/auth/register').status_code == 200

    # Test POST request to register a new user
    response = auth.register(user1_data['username'], user1_data['email'], user1_data['password'])
    # Registration redirects to login page on success
    assert response.status_code == 302 
    assert response.headers['Location'] == '/auth/login' # or wherever it redirects

    # Check that the user was added to the database
    with app.app_context():
        db_user = find_user_by_username(user1_data['username'])
        assert db_user is not None
        assert db_user.email == user1_data['email']

def test_register_duplicate_username(client, auth, user1_data, registered_user1):
    # user1 is already registered via fixture
    response = auth.register(user1_data['username'], 'newemail@example.com', 'newpassword')
    # Should ideally stay on register page and show error
    assert response.status_code == 200 # Assuming it re-renders the form with an error
    assert b"already registered" in response.data # Check for flash message or error text
    # Or, if it redirects and flashes:
    # assert response.headers['Location'] == '/auth/register' # Or wherever it redirects on error
    # with client.session_transaction() as sess:
    #     assert any("already registered" in message[1] for message in sess['_flashes'])


def test_register_duplicate_email(client, auth, user1_data, registered_user1):
    # user1 is already registered
    response = auth.register('newuser', user1_data['email'], 'newpassword')
    assert response.status_code == 200 # Assuming re-render with error
    assert b"already registered" in response.data


# Login and Logout Tests
def test_login_logout(client, auth, registered_user1):
    user_data = registered_user1 # Get data from fixture
    
    # Test GET request to login page
    assert client.get('/auth/login').status_code == 200

    # Test successful login (using username)
    response = auth.login(user_data['username'], user_data['password'])
    # Successful login redirects, e.g., to a test success page or home
    assert response.status_code == 200 # From follow_redirects=True
    assert b"Login Successful!" in response.data # Check for success message
    
    # Check that session contains user_id
    with client: # Opens context to access session, g, etc.
        client.get('/') # Make a request to establish context if needed
        assert session.get('user_id') is not None
        logged_in_user = find_user_by_username(user_data['username']) # Assuming g.user is populated
        assert g.user.id == logged_in_user.id
        assert g.user.username == user_data['username']

    # Test successful login (using email)
    auth.logout() # Logout first
    response_email_login = auth.login(user_data['email'], user_data['password'])
    assert response_email_login.status_code == 200
    assert b"Login Successful!" in response_email_login.data
    with client:
        client.get('/')
        assert session.get('user_id') is not None


    # Test logout
    logout_response = auth.logout()
    assert b"You have been logged out." in logout_response.data # Check flash message
    # Successful logout redirects to login page
    assert logout_response.status_code == 200 # From follow_redirects=True
    assert b"Log In" in logout_response.data # Check if login form is present

    with client:
        client.get('/')
        assert session.get('user_id') is None
        assert g.user is None


def test_login_invalid_username(client, auth, user1_data): # user1_data is not registered here
    response = auth.login('nonexistentuser', 'fakepassword')
    assert b"Incorrect username/email." in response.data

def test_login_invalid_email(client, auth, user1_data):
    response = auth.login('nonexistent@example.com', 'fakepassword')
    assert b"Incorrect username/email." in response.data

def test_login_incorrect_password(client, auth, registered_user1):
    user_data = registered_user1
    response = auth.login(user_data['username'], 'wrongpassword')
    assert b"Incorrect password." in response.data


# Test @login_required decorator
# Assuming '/user/profile/<username>' is a login-required route (as per previous subtasks)
# And '/auth/test_login_success' is a simple login-required route
@pytest.mark.parametrize(('path', 'message'), (
    ('/user/profile/testuser1', b"You are not authorized to view this profile or you need to log in."), 
    # Note: The profile route itself has logic that might redirect even if logged in,
    # if trying to view another's profile and that's restricted.
    # For a generic login_required test, a simpler route is better.
    ('/auth/test_login_success', b"Access Denied. Please login.") # Assuming this is a more direct test
))
def test_login_required_redirects(client, path, message):
    response = client.get(path) # No login
    assert response.status_code == 302 # Redirect to login
    assert response.headers['Location'] == '/auth/login'
    
    # Follow redirect to login page
    response_redirect = client.get(path, follow_redirects=True)
    # The original page's specific error message might not be shown after redirect to login.
    # Instead, the login page is shown.
    # If the protected route flashes a message *before* redirecting, that's harder to test here.
    # For now, confirming it redirects to login is the primary check.
    assert b"Log In" in response_redirect.data # Check that we are on the login page

def test_login_required_access_after_login(client_user1, user1_data): # client_user1 is already logged in
    # Test accessing the profile page of the logged-in user
    response = client_user1.get(f'/user/profile/{user1_data["username"]}')
    assert response.status_code == 200
    assert f"Profile: {user1_data['username']}".encode() in response.data

    # Test accessing the generic test_login_success page
    response_test_success = client_user1.get('/auth/test_login_success')
    assert response_test_success.status_code == 200
    assert b"Login Successful! User ID:" in response_test_success.data


# Test load_logged_in_user
def test_load_logged_in_user(client, auth, registered_user1, app):
    user_data = registered_user1
    
    # Check g.user is None when not logged in
    with client:
        client.get('/') # Any request to set up g
        assert g.user is None

    # Log in
    auth.login(user_data['username'], user_data['password'])
    
    with client:
        client.get('/') # Any request
        assert g.user is not None
        assert g.user.username == user_data['username']
        
        # Check if user data is loaded correctly from DB (e.g., email)
        db_user = find_user_by_username(user_data['username']) # Fetch from DB for comparison
        assert g.user.email == db_user.email
        assert g.user.id == db_user.id

    # Log out and check again
    auth.logout()
    with client:
        client.get('/')
        assert g.user is None

# Test validation messages on registration
@pytest.mark.parametrize(('username', 'email', 'password', 'message'), (
    ('', 'a@b.com', 'pass', b'Username is required.'),
    ('user', '', 'pass', b'Email is required.'),
    ('user', 'a@b.com', '', b'Password is required.'),
))
def test_register_validate_input(auth, username, email, password, message):
    response = auth.register(username, email, password)
    assert message in response.data # Assuming errors are flashed and re-rendered on same page
    assert response.status_code == 200 # Stays on register page


# Test validation messages on login
@pytest.mark.parametrize(('identifier', 'password', 'message'), (
    ('', 'pass', b'Incorrect username/email.'), # Or specific "Identifier is required" if implemented
    ('user', '', b'Incorrect password.'), # Or specific "Password is required"
))
def test_login_validate_input(auth, identifier, password, message):
    # This assumes that empty identifier or password will lead to these messages.
    # If your app has client-side validation or different server-side messages for empty fields, adjust.
    response = auth.login(identifier, password)
    assert message in response.data
    assert response.status_code == 200 # Stays on login page
