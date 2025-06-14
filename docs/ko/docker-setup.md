# 🐳 Docker로 실행하기

도커 환경에서 쉽게 실행할 수 있도록 `Dockerfile`과 `docker-compose.yml`이 제공됩니다.  
디스코드 봇을 생성하는 과정은 [Discord-py-Interactions](https://interactions-py.github.io/interactions.py/Guides/)에서, 노션 앱
생성은 [노션 개발자 페이지](https://developers.notion.com/docs/getting-started)를 참고해주세요.

## 📂 디렉토리 구조
![a](/resources/dirstructure.png)

## 🚀 설정 및 실행 가이드
### 1. `.env` 파일 생성

현재 기본적으로 `var.env.example` 파일이 제공되어 있습니다.    
이를 복서하여 `notipy` 루트 디렉토리에 다음 내용을 포함하는 `.env` 파일을 만듭니다:

✅ **수정이 반드시 필요한 값들**

| 항목 | 설명                                                                        |
| -------------------- |---------------------------------------------------------------------------|
| `GITHUB_TOKEN`       | GitHub Personal Access Token                                              |
| `DISCORD_TOKEN`      | Discord 봇 토큰                                                              |
| `DISCORD_CLIENT_ID`  | Discord 애플리케이션 클라이언트 ID                                                   |
| `DISCORD_SECRET`     | Discord 애플리케이션 클라이언트 Secret                                               |
| `DISCORD_DEVSERVER`  | 테스트용 Discord 서버 ID (예: `123456789012345678`)                              |
| `DISCORD_DEVELOPERS` | Discord 개발자 ID들, 쉼표로 구분 (예: `123,456,789`)                                |
| `DISCORD_OAUTH2_URL` | Discord OAuth2 인증 URL (예: `https://discord.com/api/oauth2/authorize?...`) |
| `REDIRECT_URI`       | OAuth2 인증 후 리디렉션될 URI (예: `https://yourdomain.com/discord/redirect`)      |
| `NOTION_TOKEN`       | Notion integration 토큰                                                     |
| `MYSQL_USER`         | MySQL ㅣㄴ사용자 이름                                                            |
| `MYSQL_PASSWORD`     | MySQL 비밀번호                                                                |
| `MYSQL_DATABASE`     | 사용할 MySQL 데이터베이스 이름                                                       |

🟡 **선택적으로 수정 가능한 값들**

| 항목 | 설명 |
| -------------------- | -------------------------------- |
| `DISCORD_DEBUG_FILE` | 디버그 로그 파일 경로 (기본: `"debug.log"`) |
| `DISCORD_ERROR_LOG`  | 에러 로그 파일 경로 (기본: `"error.log"`)  |
| `DISCORD_PORT`       | Discord 서비스 포트 (기본: `9090`)      |
| `BACKEND_PORT`       | 백엔드 서비스 포트 (기본: `9091`)          |
| `MYSQL_TCP_PORT`     | MySQL 포트 (기본: `3306`)            |

### 2. Docker 이미지 빌드 및 네트워크 생성

```bash
docker build -t notipy .
docker network create nginx-proxy
docker network create notipy_backend
```

### 3. Docker-Compose 설정

| 위치                              | 항목                              | 설명                                                                                                   |
|---------------------------------|---------------------------------|------------------------------------------------------------------------------------------------------|
| `discordbot` → `container_name` | `notipy-discordbot`             | 필요 시 컨테이너명 변경 가능, 변경시 Docker Network 접근 URL 이 달라지니 비추천                                               |
| `discordbot` → `DEBUG`          | `notipy-discordbot`             | 디버그 모드를 활성화 할지 여부입니다. 디버그 모드를 활성화 할경우 개발서버를 제외한 모든 서버에서 나가며 개발서버와 모든 명령어를 강제 동기화 하며 일부 로깅 기능이 강화됩니다. |
| `backend` → `container_name`    | `notipy-backend`                | 이 또한 필요시 변경                                                                                          |
| `database` → `volumes`          | `./database:/var/lib/mysql`     | 실제 볼륨 경로 확인 및 유지 가능                                                                                  |
| `networks`                      | `nginx-proxy`, `notipy_backend` | 2번 단계에서 생성된 네트워크 이름과 일치해야함                                                                           |

이 밖에도 각종 포트번호가 var.env 파일과 일치하는지 확인

### 3. Docker 컨테이너 실행

```bash
docker compose up -d
```

nginx, Ollama 컨테이너는 사용하지 않으실 경우 굳이 생성하실 필요는 없습니다.

```bash
docker compose up database backend discordbot -d
```

### 실행 중 어렵거나 문제가 발생하는 경우
디스코드 [지원서버](https://discord.gg/HzAnBSCN7t)에 문의해주세요.