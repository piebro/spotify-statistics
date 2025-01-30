import base64
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode

import requests


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        query_components = parse_qs(self.path.split("?")[1])
        self.server.authorization_code = query_components["code"][0]
        self.wfile.write(b"Authorization successful! You can close this window.")

    def log_message(self, format, *args):
        return


def get_spotify_bearer():
    # Get credentials from environment variables
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")

    # Start local server to receive callback
    server = HTTPServer(("localhost", 8888), OAuthHandler)
    server.authorization_code = None

    # Prepare authorization URL
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": "http://localhost:8888/callback",
        "scope": "user-read-playback-state user-modify-playback-state user-read-recently-played",
    }

    # Open browser for user authorization
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    webbrowser.open(auth_url)

    # Wait for callback
    while server.authorization_code is None:
        server.handle_request()

    # Exchange authorization code for token
    auth_b64 = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": server.authorization_code,
            "redirect_uri": "http://localhost:8888/callback",
        },
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    return response.json()["access_token"]


def update_env_file(bearer_token):
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

    # Read existing .env content<
    env_content = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    env_content[key] = value.strip("\"'")

    # Update or add the bearer token
    env_content["SPOTIFY_BEARER_TOKEN"] = bearer_token
    print(bearer_token)

    # Write back to .env file
    with open(env_path, "w") as f:
        for key, value in env_content.items():
            f.write(f'{key}="{value}"\n')


if __name__ == "__main__":
    try:
        bearer_token = get_spotify_bearer()
        update_env_file(bearer_token)
        print("Bearer token has been updated in .env file")
    except Exception as e:
        print(f"Error: {e}")
