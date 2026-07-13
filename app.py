import os
import json
import requests
from flask import Flask, redirect, url_for, session, request, jsonify
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from flask_dance.consumer import oauth_authorized

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["PS99_CLIENT_ID"] = os.environ.get("PS99_CLIENT_ID")
app.config["PS99_CLIENT_SECRET"] = os.environ.get("PS99_CLIENT_SECRET")

# OAuth 2.0 Configuration for PS99
ps99_blueprint = OAuth2ConsumerBlueprint(
    "ps99",
    __name__,
    client_id=os.environ.get("PS99_CLIENT_ID"),
    client_secret=os.environ.get("PS99_CLIENT_SECRET"),
    base_url="https://ps99.biggamesapi.io/",
    token_url="https://db.biggames.io/oauth/token",
    authorization_url="https://db.biggames.io/oauth/authorize",
    redirect_url="https://ps99-oauth-bot-1.onrender.com/callback",  # Must match registered URI
    storage=MemoryStorage(),
)

# Override the default callback path to match the registered redirect URI
@ps99_blueprint.route("/callback", methods=["GET", "POST"])
def callback():
    """Handle the OAuth callback at the registered redirect URI."""
    from flask_dance.consumer import oauth_authorized
    from flask import request, session, current_app
    import requests as req
    
    # Get the code from the request
    code = request.args.get("code")
    if not code:
        return "Missing code parameter", 400
    
    # Exchange code for token
    token_url = "https://db.biggames.io/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://ps99-oauth-bot-1.onrender.com/callback",
        "client_id": current_app.config.get("PS99_CLIENT_ID"),
        "client_secret": current_app.config.get("PS99_CLIENT_SECRET"),
    }
    
    response = req.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        session["ps99_oauth_token"] = token_data
        return "✅ Authorization successful! You can close this window."
    else:
        return f"❌ Error: {response.text}", 400

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