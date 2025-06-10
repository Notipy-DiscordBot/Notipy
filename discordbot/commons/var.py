import os

token = os.environ["DISCORD_TOKEN"]
notion_api_url = os.environ["NOTION_API_URL"]  # Notion API URL
# notion_token = os.environ["NOTION_TOKEN"]  # Notion API token
notion_api_version = os.environ["NOTION_API_VERSION"]

# Replace with actual server ID
devserver = int(os.environ["DISCORD_DEVSERVER"])
supportchannelid = int(
    os.environ.get("DISCORD_SUPPORT_CHANNEL")
)  # Replace with actual support channel ID

# Replace with actual developer IDs
developers = os.environ["DISCORD_DEVELOPERS"]
developers = [int(dev) for dev in developers.split(",")]

# logfiles, they will be located at discordbot/logs
debugfile = os.environ["DISCORD_DEBUG_FILE"]  # File to log debug information
errfile = os.environ["DISCORD_ERROR_LOG"]  # File to log error information
apiport = os.environ["BACKEND_PORT"]

app_root = os.environ["DISCORD_APP_ROOT"]
backend_url = "http://notipy-backend"
backend_api_root = os.environ["BACKEND_APP_ROOT"]


api_root = f"{backend_url}:{apiport}{backend_api_root}"  # Backend API root URL

githuburl = "https://github.com"
