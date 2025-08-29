"""
WSGI entry point for Contract Management Platform
Production deployment with Gunicorn
"""
from app import create_app

app = create_app('production')

if __name__ == "__main__":
    app.run()
