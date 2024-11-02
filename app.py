from flask import Flask, redirect, url_for, session, request, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
from dotenv import load_dotenv

# Load environment variables (useful for local testing)
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Environment variables for OAuth and Redirect URI
GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # e.g., 'https://your-app-name.herokuapp.com/oauth2callback'

# Set up the OAuth flow
flow = Flow.from_client_config(
    {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    },
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/documents"
        # Add more scopes as needed for additional Google services
    ],
    redirect_uri=REDIRECT_URI
)

# Homepage route - Displays login link if not authenticated
@app.route("/")
def home():
    if "credentials" not in session:
        return '<a href="/login">Login with Google</a>'
    
    # If logged in, show action links
    return """
        <h1>Welcome! You're logged in.</h1>
        <a href="/create_sheet">Create a Google Sheet</a><br>
        <a href="/list_drive_files">List Google Drive Files</a>
    """

# Login route - Redirects to Google OAuth consent page
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

# OAuth callback route - Handles the response from Google's OAuth
@app.route("/oauth2callback")
def oauth2callback():
    # Complete the OAuth flow
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)
    return redirect(url_for("home"))

# Helper function - Converts credentials to dictionary for storage
def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }

# Example route to create a Google Sheet
@app.route("/create_sheet")
def create_sheet():
    if "credentials" not in session:
        return redirect("login")

    creds = Credentials(**session["credentials"])
    service = build("sheets", "v4", credentials=creds)

    # Create a new Google Sheet
    spreadsheet_body = {
        "properties": {
            "title": "New Spreadsheet"
        }
    }
    spreadsheet = service.spreadsheets().create(body=spreadsheet_body).execute()
    return jsonify(spreadsheet)

# Example route to list Google Drive files
@app.route("/list_drive_files")
def list_drive_files():
    if "credentials" not in session:
        return redirect("login")

    creds = Credentials(**session["credentials"])
    service = build("drive", "v3", credentials=creds)

    # List the first 10 files in Google Drive
    results = service.files().list(pageSize=10).execute()
    files = results.get("files", [])
    return jsonify(files)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
