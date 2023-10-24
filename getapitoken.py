import requests
from urllib.parse import urlencode
import base64
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()

#credentials from app spotify
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

token_url = 'https://accounts.spotify.com/api/token'
auth_headers = {
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": "http://localhost:8181",
    "scope": "user-library-read"
}
#%%
#Just once to get the code
webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))

#%%
#this code change, and get from the previous step 
code = "AQCXrKPBJ7Df3li9QWRrg8MFuHN5y8X4zdx8f6o4oO0DV-uiHf4fmxpvpdGCvYSGgo7-16cPI3MMrxKbMS4P5SBr-9nKpZKuBbjZv9Xcj4JhPIatbACM8U7wp1h_yj9mJw2dW-NJ1bnzZEVHiBu7zfro3Fz8A8i5r1LpPHs1HoGLrh32bAcDh7OCQak"

#%%
encoded_credentials = base64.b64encode(CLIENT_ID.encode() + b':' + CLIENT_SECRET.encode()).decode("utf-8")

token_headers = {
    "Authorization": "Basic " + encoded_credentials,
    "Content-Type": "application/x-www-form-urlencoded"
}

token_data = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": "http://localhost:8181"
}

r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)

#this result go to .env as refresh_token
refresh_token = r.json()["refresh_token"]
