#!/usr/bin/env python3

import jwt
from datetime import datetime, timedelta, timezone
import hashlib
import os



class Authenticator:
    def __init__(self, credentials_file, secret_key):
        self.credentials_file = credentials_file
        self.secret_key = secret_key

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16) # Generate a random salt
        hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return hashed_password.hex(), salt.hex()
    
    def validate_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['username']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        
    def generate_token(self, username):
        expiration_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            'username': username,
            'exp': expiration_time
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token.decode()


    def register_user(self, username, email, password):
        
        if self.check_user_existence(username, email):
            return False, "User already Exists"
        
        hashed_password, salt = self.hash_password(password)

        with open(self.credentials_file, 'a') as f:
            f.write(f"{username}:{email}:{hashed_password}:{salt}\n")

        return True, "User Registered successfully"
    
    def login(self, username, password):
        with open(self.credentials_file, 'r') as f:
            for line in f:
                stored_username, _, stored_password, stored_salt = line.strip().split(':')
                if stored_username == username:
                    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(stored_salt), 100000).hex()
                    if hashed_password == stored_password:
                        return True, self.generate_token(username)
                    else:
                        return False, "Incorrect Password"
        return False, "User not Found"

    def check_user_existence(self, username, email):
        if not os.path.isfile(self.credentials_file):
            return False
        
        with open(self.credentials_file, 'r') as f:
            for line in f:
                stored_username, stored_email, _, _ = line.strip().split(':')
                if stored_username == username or stored_email == email:
                    return True
        return False

