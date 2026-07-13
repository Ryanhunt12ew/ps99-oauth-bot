import os
from flask import Flask, redirect, session, jsonify
import petsim.api as api

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# Initialize the API with OAuth
rap = api.Rap()

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
    """Redirect user to BIG Games OAuth page using petsim-py"""
    # Get the authorization URL
    auth_url = rap.get_authorization_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle the OAuth callback"""
    code = request.args.get('code')
    if not code:
        return "No authorization code received", 400
    
    # Exchange code for token using petsim-py
    try:
        token = rap.exchange_code_for_token(code)
        session['ps99_token'] = token
        return '''
        <h1>✅ Authorization Successful!</h1>
        <p>You can close this window and return to Discord.</p>
        '''
    except Exception as e:
        return f"❌ Error: {e}", 400

@app.route('/token')
def get_token():
    """Endpoint for your Discord bot to get the token"""
    token_data = session.get('ps99_token')
    if token_data:
        return jsonify(token_data)
    return jsonify({"error": "Not authenticated"}), 401

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))