import os
import jwt
import datetime
from ..utils.crypto import generate_token, verify_token

class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
        # In a real application, these would be stored in a database
        self.users = {
            'admin': {
                'password': 'admin123',
                'role': 'admin'
            },
            'worker': {
                'password': 'worker123',
                'role': 'worker'
            }
        }
        self.active_tokens = set()

    def authenticate(self, username, password):
        """Authenticate a user with username and password"""
        if username in self.users and self.users[username]['password'] == password:
            return True
        return False

    def generate_auth_token(self, username):
        """Generate a JWT token for authenticated users"""
        if username not in self.users:
            return None
            
        payload = {
            'username': username,
            'role': self.users[username]['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        
        token = generate_token(payload)
        self.active_tokens.add(token)
        return token

    def verify_auth_token(self, token):
        """Verify a JWT token"""
        if token not in self.active_tokens:
            return None
            
        try:
            payload = verify_token(token)
            if payload and payload['username'] in self.users:
                return payload
        except jwt.ExpiredSignatureError:
            self.active_tokens.remove(token)
            
        return None

    def invalidate_token(self, token):
        """Invalidate a token (logout)"""
        if token in self.active_tokens:
            self.active_tokens.remove(token)
            return True
        return False

    def check_permission(self, token, required_role):
        """Check if the user has the required role"""
        payload = self.verify_auth_token(token)
        if not payload:
            return False
            
        return payload['role'] == required_role

    def create_user(self, username, password, role='user'):
        """Create a new user (admin only)"""
        if username in self.users:
            return False
            
        self.users[username] = {
            'password': password,
            'role': role
        }
        return True

    def delete_user(self, username):
        """Delete a user (admin only)"""
        if username in self.users:
            del self.users[username]
            return True
        return False

    def change_password(self, username, old_password, new_password):
        """Change user password"""
        if self.authenticate(username, old_password):
            self.users[username]['password'] = new_password
            return True
        return False