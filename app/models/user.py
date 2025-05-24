from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, id, username, email, password_hash, avatar_url=None, created_at=None, last_login=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.avatar_url = avatar_url
        self.created_at = created_at
        self.last_login = last_login

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
