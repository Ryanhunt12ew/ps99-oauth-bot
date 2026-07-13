import os
import requests
from flask import Flask, redirect, session, jsonify, request
import secrets
import hashlib
import base64

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# Get credentials from environment
CLIENT_ID = os.environ.get("PS99_CLIENT_ID")
CLIENT_SECRET = os.environ.get("PS99_CLIENT_SECRET")
REDIRECT_URI = "https://ps99-oauth-bot-1.onrender.com/callback"

@app.route('/')
def index():
    return '''
    <h1>PS99 Bot OAuth Setup</h1>
    <p>Click the link below to authorize your bot to access your PS99 data:</p>
    <a href="/authorize">🔑 Link Your PS99 Account</a>
    <br><br>
    <p>After authorizing, your bot will be able to track your purchases!</p>
    '''

@app.route('/authorize')
def authorize():
    """Redirect user to BIG Games OAuth page"""
    # Generate PKCE code verifier and challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    # Store verifier in session
    session['code_verifier'] = code_verifier
    
    # Build authorization URL
    auth_url = (
        "https://db.biggames.io/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle the OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return f"❌ Authorization error: {error}", 400
    
    if not code:
        return "❌ No authorization code received", 400
    
    # Exchange code for token
    token_url = "https://db.biggames.io/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": session.get('code_verifier', ''),
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        session['ps99_oauth_token'] = token_data
        return '''
        <h1>✅ Authorization Successful!</h1>
        <p>You can close this window and return to Discord.</p>
        <p>Your bot can now track your PS99 data.</p>
        '''
    else:
        return f"❌ Error exchanging code: {response.text}", 400

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))