import os

TOKEN = os.getenv("TOKEN")

admin_chat = os.getenv("ADMIN_CHAT_ID")
if not admin_chat:
    raise ValueError("ADMIN_CHAT_ID is not set in Railway variables")

ADMIN_CHAT_ID = int(admin_chat)