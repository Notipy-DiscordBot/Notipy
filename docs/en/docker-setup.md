# 🐳 Running with Docker

`Dockerfile` and `docker-compose.yml` are provided for easy execution in a Docker environment.  
For the process of creating a Discord bot, refer
to [Discord-py-Interactions](https://interactions-py.github.io/interactions.py/Guides/), and for creating a Notion app,
refer to the [Notion Developer Page](https://developers.notion.com/docs/getting-started).

### 1. Create a `.env` file

A `var.env.example` file is provided by default.  
Copy this file and create a `.env` file in the root directory of `notipy` with the following contents:

✅ **Values that must be modified**

| Item                  | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| `GITHUB_TOKEN`        | GitHub Personal Access Token                                                |
| `DISCORD_TOKEN`       | Discord bot token                                                           |
| `DISCORD_CLIENT_ID`   | Discord application client ID                                               |
| `DISCORD_SECRET`      | Discord application client secret                                           |
| `DISCORD_DEVSERVER`   | Discord server ID for testing (e.g., `123456789012345678`)                  |
| `DISCORD_DEVELOPERS`  | Discord developer IDs, comma-separated (e.g., `123,456,789`)                |
| `DISCORD_OAUTH2_URL`  | Discord OAuth2 authentication URL (e.g., `https://discord.com/api/oauth2/authorize?...`) |
| `REDIRECT_URI`        | URI to redirect to after OAuth2 authentication (e.g., `https://yourdomain.com/discord/redirect`) |
| `NOTION_TOKEN`        | Notion integration token                                                    |
| `MYSQL_USER`          | MySQL username                                                              |
| `MYSQL_PASSWORD`      | MySQL password                                                              |
| `MYSQL_DATABASE`      | MySQL database name to use                                                  |

🟡 **Values that can be optionally modified**

| Item                  | Description                                 |
| --------------------- | ------------------------------------------- |
| `DISCORD_DEBUG_FILE`  | Debug log file path (default: `"debug.log"`)|
| `DISCORD_ERROR_LOG`   | Error log file path (default: `"error.log"`)|
| `DISCORD_PORT`        | Discord service port (default: `9090`)      |
| `BACKEND_PORT`        | Backend service port (default: `9091`)      |
| `MYSQL_TCP_PORT`      | MySQL port (default: `3306`)                |

### 2. Build Docker Image and Create Networks

```bash
docker build -t notipy .
docker network create nginx-proxy
docker network create notipy_backend
```

### 3. Docker-Compose Settings

| Location                          | Item                        | Description                                                                                                   |
|------------------------------------|-----------------------------|---------------------------------------------------------------------------------------------------------------|
| `discordbot` → `container_name`    | `notipy-discordbot`         | You can change the container name if needed, but it is not recommended as the Docker Network access URL will change. |
| `discordbot` → `DEBUG`             | `notipy-discordbot`         | Whether to enable debug mode. If enabled, the bot will leave all servers except the development server, force sync all commands with the dev server, and enhance some logging features. |
| `backend` → `container_name`       | `notipy-backend`            | This can also be changed if needed.                                                                           |
| `database` → `volumes`             | `./database:/var/lib/mysql` | Check and maintain the actual volume path.                                                                    |
| `networks`                         | `nginx-proxy`, `notipy_backend` | Must match the network names created in step 2.                                                          |

Also, make sure that the various port numbers match those in the var.env file.

### 3. Run Docker Containers

```bash
docker compose up -d
```

You do not need to create nginx or Ollama containers if you are not using them.

```bash
docker compose up database backend discordbot -d
```

### If you encounter difficulties or problems during execution
Please contact the Discord [support server](https://discord.gg/HzAnBSCN7t).