"""Run locally once to authorize the YouTube channel and create token.json."""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    if not os.path.exists("client_secret.json"):
        raise SystemExit(
            "Missing client_secret.json. Download an OAuth Desktop-app JSON "
            "from Google Cloud Console and save it beside this script."
        )
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    with open("token.json", "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print("Created token.json. Keep it private; it grants access to your YouTube channel.")

if __name__ == "__main__":
    main()
