import os

class Config:
    # Secret key used to sign session cookies securely
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_helm_ai_key_change_me'
    # Define database path
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
