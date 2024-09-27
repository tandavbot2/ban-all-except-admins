import os

class Config(object):
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH"))
    BOT_TOKEN = os.environ.get("BOT_TOKEN"))

    # Add sudo users as a list of user IDs
    SUDO_USERS = [6265954306, 7169824974]  # Replace with actual user IDs
