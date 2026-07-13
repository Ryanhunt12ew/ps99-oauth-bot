import os
import json
import requests
from flask import Flask, redirect, url_for, session, request, jsonify
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from flask_dance.consumer import oauth_authorized

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# OAuth 2.0 Configuration for PS99
ps99_blueprint = OAuth2ConsumerBlueprint(
    "ps99",
    __name__,
    client_id=os.environ.get("PS99_CLIENT_ID"),
    client_secret=os.environ.get("PS99_CLIENT_SECRET"),
    base_url="https://ps99.biggamesapi.io/",
    token_url="https://ps99.biggamesapi.io/v1/oauth/token",
    authorization_url="https://ps99.biggamesapi.io/v1/oauth/authorize",
    redirect_url=os.environ.get("REDIRECT_URI", "https://your-app.onrender.com/callback"),
    storage=MemoryStorage(),
)

app.register_blueprint(ps99_blueprint, url_prefix="/login")

@app.route('/')
def index():
    return '''
    <h1>PS99 Bot OAuth Setup</h1>
    <p>Click the link below to authorize your bot to access your PS99 data:</p>
    <a href="/login/ps99">🔑 Link Your PS99 Account</a>
    <br><br>
    <p>After authorizing, your bot will be able to track your purchases!</p>
    '''

@oauth_authorized.connect
def logged_in(blueprint, token):
    """Store the token when user authorizes"""
    print(f"✅ Token received! {token}")
    # In a real app, you'd save this to a database
    # For now, it's stored in memory
    return False

@app.route('/token')
def get_token():
    """Endpoint for your Discord bot to get the token"""
    token_data = session.get('ps99_oauth_token')
    if token_data:
        return jsonify({
            "access_token": token_data.get('access_token'),
            "expires_in": token_data.get('expires_in'),
            "refresh_token": token_data.get('refresh_token')
        })
    return jsonify({"error": "Not authenticated"}), 401

@app.route('/inventory')
def get_inventory():
    """Example: Get your inventory using the token"""
    token_data = session.get('ps99_oauth_token')
    if not token_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    
    response = requests.get(
        "https://ps99.biggamesapi.io/v1/account/inventory",
        headers=headers
    )
    
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))