<!-- <p align="center">
  <img src="https://yourdomain.com/banner.png" alt="Notipy Logo" width="400"/>
</p> -->

<h1 align="center">Notipy</h1>
<p align="center">A real-time alert system connecting Notion and Discord</p>
<p align="center">
  <a href="https://www.docker.com/">
    <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  </a>
  <a href="https://www.mysql.com/">
    <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL">
  </a>
  <a href="https://discord.com/">
    <img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python">
  </a>
</p>
<p align="center">
  <a href="/README.md">
    <img src="https://img.shields.io/badge/lang-한국어-blue" alt="Korean">
  </a>
  <a href="/docs/en/README.md">
    <img src="https://img.shields.io/badge/lang-English-lightgrey" alt="English">
  </a>
</p>

---
<p align="center">
This page was translated with the help of ChatGPT. Some elements may not perfectly reflect the original content.
</p>

## Table of Contents
- [Key Features](#key-features)
  - [Notion](#notion)
  - [Database Integration](#database-integration)
  - [GitHub Profile Analysis and Summary](#github-profile-analysis-and-summary)
  - [Project Creation and Management](#project-creation-and-management)
  - [Internal Request Validation and Security](#internal-request-validation-and-security)
- [Getting Started as a User](#getting-started-as-a-user)
- [Commonly Used Commands](#commonly-used-commands)
- [Running with Docker](#running-with-docker)
- [Contributing](#contributing)
- [Community](#community)
- [Terms of Service and Privacy Policy](#terms-of-service-and-privacy-policy)
- [License](#license)

<a id="this-project-is-currently-under-development"></a>
## 🚧 This project is currently under development!

Notipy is a Python-based Discord bot that monitors a Notion database and sends notifications to a Discord channel when specific conditions are met.
It can be used as a real-time alert tool in various collaboration scenarios, such as scheduling, task management, and issue tracking.
It is structured using a FastAPI-based backend server and SQLAlchemy ORM, supporting seamless integration with the Notion API and Discord interaction system.
**Note: As this project is under active development, some services may be unstable or temporarily unavailable without prior notice.**
<a id="key-features"></a>

## ✨ Key Features

### Notion

* Users must individually create a Notion Integration for their own workspace and provide its token directly.
* This token only grants access to events within the user's workspace and is never transmitted outside the server or shared.

#### 📌 Webhook Reception and Processing

* Receives events such as page creation, updates, and deletion via webhook and relays this information to the Discord channel.
* Supports creating threads in forum channels or updating existing messages.
<a id="database-integration"></a>
* Stores linkage data between Notion pages and Discord threads in the database to maintain persistent alert tracking.

### 🗃️ Database Integration

* Synchronizes page properties from the registered Notion databases to use as filter conditions or message content.
* Detects changes in page content and periodically updates the corresponding Discord notification.
* Supports multiple database connections per server, with each server managed independently.

#### 🔎 Why must users provide their own Notion token?

* **Access Control**: By creating the integration themselves, users can **explicitly control which workspaces or databases the bot can access**.
* **Flexible Webhook Configuration**: Users can **manually configure desired events** (e.g., page creation/updates) within Notion.
* **Security and Data Isolation**: Since each token is tied to a user's workspace only, it ensures isolated and secure integration.

📖 **Notion Token Setup Guide:**
👉 [How to create a Notion Integration and get the token](https://developers.notion.com/docs/create-a-notion-integration)

<a id="github-profile-analysis-and-summary"></a>
### 🧠 GitHub Profile Analysis and Summary

* Collects GitHub profile data based on user-provided URLs and summarizes key information using LLM.
* Summaries can be accessed by other users on Discord if permission is granted.

<a id="project-creation-and-management"></a>
### 🛠️ Project Creation and Management

* Users can create new projects via Discord commands or interaction.
* Projects are uniquely identified by server ID and user ID, allowing each user to manage their own list.
* Each project has metadata like title, description, and category, and can be easily edited through the Discord UI.

<a id="internal-request-validation-and-security"></a>
### 🔒 Internal Request Validation and Security

All internal API requests are validated via the `X-Internal-Request` header in FastAPI.
This header is automatically set to `false` by Nginx for external requests, while only internal Docker network requests may bypass or set it to `true`.

* External requests → `X-Internal-Request: false` (forced by Nginx)
* Internal Docker communication → Direct access or set to `true`

This prevents external actors from spoofing internal API calls.

---

<a id="getting-started-as-a-user"></a>
## 🧭 Getting Started as a User

You can use **Notipy without self-hosting**. Simply invite the bot to your Discord server and start using its features immediately. Here's a quick guide:

### ✅ Step 1. Invite the Bot

* You can invite the bot from the [official website](https://notipy.code0987.com) or directly via this [invite link](https://discord.com/oauth2/authorize?client_id=955999346321686609).
* After inviting the bot, we recommend using the `/settings set-modrole` command to ensure smooth operation.

<a id="commonly-used-commands"></a>
## 📋 Commonly Used Commands

| Command                        | Description                                   |
| ----------------------------- | --------------------------------------------- |
| `/settings view`              | View the current settings for the server      |
| `/notion notiontoken set`           | Register your Notion integration token        |
| `/notion database connect`          | Connect a Notion database to a channel        |
| `/notion database view`             | View the list of connected databases          |
| `/notion notiontoken remove`        | Disconnect your Notion integration            |
| `/create-ticket`              | Create a support ticket within Discord        |
| `/github link`                | Link your GitHub account                      |
| `/create-project`             | Create and manage a collaborative project     |

If you want to configure the environment and host the bot yourself, refer to the section below titled “Running with Docker”.


---

<a id="running-with-docker"></a>
## 🐳 Running with Docker

`Dockerfile` and `docker-compose.yml` are provided for easy deployment in a Docker environment.  
To create a Discord bot, please refer to the [Discord-py-Interactions Guide](https://interactions-py.github.io/interactions.py/Guides/).  
To create a Notion integration, please refer to the [Notion Developer Documentation](https://developers.notion.com/docs/getting-started).

### 1. Create a `.env` File

A sample `var.env.example` file is provided.
Duplicate it to the root directory as `.env` and fill in the following:

✅ **Required Settings**

| Variable             | Description                                                     |
| -------------------- | --------------------------------------------------------------- |
| `GITHUB_TOKEN`       | GitHub Personal Access Token                                    |
| `DISCORD_TOKEN`      | Discord bot token                                               |
| `DISCORD_CLIENT_ID`  | Discord application client ID                                   |
| `DISCORD_SECRET`     | Discord application client secret                               |
| `DISCORD_DEVSERVER`  | Development Discord server ID (e.g., `123456789012345678`)      |
| `DISCORD_DEVELOPERS` | Developer user IDs (comma-separated, e.g., `123,456,789`)       |
| `DISCORD_OAUTH2_URL` | Discord OAuth2 URL (e.g., `https://discord.com/api/oauth2/...`) |
| `REDIRECT_URI`       | Redirect URI after OAuth2 (e.g., `https://yourdomain.com/...`)  |
| `NOTION_TOKEN`       | Notion integration token                                        |
| `MYSQL_USER`         | MySQL username                                                  |
| `MYSQL_PASSWORD`     | MySQL password                                                  |
| `MYSQL_DATABASE`     | MySQL database name                                             |

🟡 **Optional Settings**

| Variable             | Description                            |
| -------------------- | -------------------------------------- |
| `DISCORD_DEBUG_FILE` | Debug log path (default: `debug.log`)  |
| `DISCORD_ERROR_LOG`  | Error log path (default: `error.log`)  |
| `DISCORD_PORT`       | Discord service port (default: `9090`) |
| `BACKEND_PORT`       | Backend service port (default: `9091`) |
| `MYSQL_TCP_PORT`     | MySQL port (default: `3306`)           |

### 2. Build Docker Image & Create Networks

```bash
docker build -t notipy .
docker network create nginx-proxy
docker network create notipy_backend
```

### 3. Configure Docker-Compose

| Location                        | Field                       | Description                                                        |
| ------------------------------- | --------------------------- | ------------------------------------------------------------------ |
| `discordbot` → `container_name` | `notipy-discordbot`         | Optional: renaming changes network access URLs, so not recommended |
| `discordbot` → `DEBUG`          | Enables debug mode          | Exits all servers except dev server and forcibly syncs commands    |
| `backend` → `container_name`    | `notipy-backend`            | Optional renaming possible                                         |
| `database` → `volumes`          | `./database:/var/lib/mysql` | Keeps volume data persistent                                       |
| `networks`                      | Must match names            | Should match networks created in step 2                            |

Ensure all port numbers match those in your `.env` file.

### 4. Run Docker Containers

```bash
docker compose up -d
```

If not using nginx or Ollama, you may run only selected containers:

```bash
docker compose up database backend discordbot -d
```

---

<a id="contributing"></a>
## 🤝 Contributing

Notipy is an open-source project — contributions are welcome!

### 🧹 How to Contribute

1. **Fork** the repository.
2. Create a new branch:
3. Add features or fix bugs.
4. Create a Pull Request:

   * Title format: `[Feature] Feature name` or `[Bug] Bug description`
   * Describe your changes, related issues, and how to test them.
   * PRs should target the `dev/main` branch.
5. Include a PR template if possible.

   * Code formatting is handled automatically.

---

<a id="community"></a>
## 🧑‍🤝‍🧑 Community

You can get announcements and support through the following:

* Official website: [link](https://notipy.code0987.com)
* Discord support server: [Invite link](https://discord.gg/HzAnBSCN7t)
* Or send a DM to the bot!
* GitHub repository: [macqueen0987/notipy](https://github.com/macqueen0987/notipy)

<a id="terms-of-service-and-privacy-policy"></a>
## 📃 Terms of Service and Privacy Policy
You can read the full terms and privacy policy within this repository.
- [English version](terms-policy.md)
- [Korean version](../ko/terms-policy.md)

---

<a id="license"></a>
## License

This project is licensed under the Apache 2.0 License.
