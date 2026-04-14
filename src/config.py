import os

from dotenv import load_dotenv


def get_token() -> str:
    load_dotenv()
    token = os.getenv("TMD_API_TOKEN")
    if not token:
        raise SystemExit("Error: TMD_API_TOKEN is not set. Add it to your .env file.")
    return token
