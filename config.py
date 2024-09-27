import os

class Config(object):
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")  # Removed the extra closing parenthesis
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    SUDO_USERS = [int(user) for user in os.environ.get("SUDO_USERS", "").split()]
    
