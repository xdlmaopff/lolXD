import os

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8274285655:AAGQUT68rJV_DbELtV5f8ChW0r4rnyT3p1k')  # Get from @BotFather
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '-1003623382800'))  # Admin chat ID
CHANNEL_ORDERS_ID = int(os.getenv('CHANNEL_ORDERS_ID', '-1003566833787'))  # Private channel for orders
YOUR_ADMIN_ID = int(os.getenv('YOUR_ADMIN_ID', '7871463306'))  # Your Telegram ID
DB_NAME = os.getenv('DB_NAME', 'dropchat.db')  # Database file name

# Database settings
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'