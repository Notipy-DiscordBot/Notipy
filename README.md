<p align="center">   
  <img src="https://github.com/Notipy-DiscordBot/Notipy/blob/main/resources/banner.png" alt="Notipy Logo"/>
</p>

<!-- <h1 align="center">Notipy</h1> -->
<p align="center">Notion과 Discord를 연결하는 실시간 알림 시스템</p>
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
  <a href="docs/en/README.md">
    <img src="https://img.shields.io/badge/lang-English-lightgrey" alt="English">
  </a>
</p>

---

## 해당 프로젝트는 아직 개발중입니다!
Notipy는 Notion 데이터베이스를 모니터링하여 특정 조건이 충족되면 Discord 채널에 알림을 전송하는 Python 기반 Discord 봇입니다. 일정, 태스크 관리, 이슈 트래킹 등 다양한 협업 시나리오에서 실시간 알림 도구로 활용할 수 있습니다.     
FastAPI 기반의 백엔드 서버와 SQLAlchemy ORM을 통해 구조적으로 관리되며, Notion API 및 Discord 인터랙션 시스템과의 연계를 지원합니다.    
**현재 개발중인 프로젝트로 일부 서비스가 불안정하거나 공지 없이 서비스가 중단될 수 있습니다**

## 목차
- [주요 기능](#주요-기능)
  - [Notion](#notion)
  - [데이터베이스 연동](#데이터베이스-연동)
  - [GitHub 프로필 분석 및 요약](#github-프로필-분석-및-요약)
  - [프로젝트 생성 및 관리](#프로젝트-생성-및-관리)
  - [내부 요청 검증 및 보안 구조](#내부-요청-검증-및-보안-구조)
- [사용자 입장에서 시작하기](#사용자-입장에서-시작하기)
- [자주 사용하는 명령어 요약](#자주-사용하는-명령어-요약)
- [Docker로 실행하기](#docker로-실행하기)
- [Contributing](#contributing)
- [커뮤니티](#커뮤니티)
- [이용약관 및 개인정보 처리방침](#이용약관-및-개인정보-처리방침)
- [License](#license)

<a id="주요-기능"></a>

## ✨ 주요 기능
### Notion 
- 사용자는 자신의 Notion 워크스페이스에 대해 **개별적으로 Notion Integration을 생성하고, 해당 토큰을 직접 제공**해야 합니다.
- 이 토큰은 오직 해당 사용자의 워크스페이스에서 발생하는 이벤트에만 접근할 수 있으며, **서버 외부로 전송되거나 공유되지 않습니다.**

#### 📌 웹훅 수신 및 처리
- Notion에서 발생하는 페이지 생성, 수정, 삭제 등의 이벤트를 웹훅을 통해 수신하고, 해당 정보를 Discord 채널로 전송합니다.
- 포럼 채널 내 스레드 생성 또는 기존 메시지 업데이트 기능을 지원합니다.
- 페이지와 스레드 간의 연동 정보를 데이터베이스에 저장해 알림의 지속적 연결성을 유지합니다.
<a id="데이터베이스-연동"></a>

### 🗃️ 데이터베이스 연동
- 등록된 Notion 데이터베이스의 페이지 속성들을 동기화하여, 알림의 필터링 조건이나 출력 메시지로 활용합니다.
- 페이지 내용 변경 여부를 감지하고, 변경된 페이지에 대한 정보를 Discord에 주기적으로 갱신할 수 있습니다.
- 서버별로 다중 데이터베이스 연결을 지원하며, 각 서버는 독립적으로 구성됩니다.

#### 🔎 왜 개인별로 Notion 토큰을 제공해야 하나요?
- **접근 범위 통제**: 사용자가 Integration을 직접 생성함으로써, **봇이 접근 가능한 워크스페이스나 데이터베이스를 직접 지정**할 수 있습니다.
- **웹훅 설정 유연성**: 사용자가 Notion 내에서 **원하는 이벤트(예: 페이지 생성/변경 등)에 대해 직접 웹훅을 구성**할 수 있습니다.
- **보안 및 데이터 격리**: 각 사용자의 토큰은 **자신의 워크스페이스에만 적용되므로**, 다른 사용자와의 데이터 혼동이나 침해 없이 개별로 안전하게 데이터베이스를 연동할 수 있습니다.

📖 **Notion 토큰 발급 및 설정 가이드:**  
👉 [Notion Integration 생성 및 토큰 설정 방법](https://developers.notion.com/docs/create-a-notion-integration)
<a id="github-프로필-분석-및-요약"></a>


### 🧠 GitHub 프로필 분석 및 요약
- 사용자가 제공한 GitHub URL 기반으로 프로필 데이터를 수집하고, LLM을 활용해 핵심 정보를 요약합니다.
- 요약된 결과는 Discord 상에서 자신이 허용한 경우 다른 사용자가 조회할 수 있습니다.

<a id="프로젝트-생성-및-관리"></a>
### 🛠️ 프로젝트 생성 및 관리
- 사용자는 Discord 명령어 또는 인터랙션을 통해 새로운 프로젝트를 생성할 수 있습니다.
- 생성된 프로젝트는 내부적으로 서버 ID 및 사용자 ID를 기반으로 구분되며, 사용자 단위로 자신이 속한 프로젝트 목록을 확인할 수 있습니다.
- 각 프로젝트는 제목, 설명, 분류(category) 등의 메타데이터를 가지며, Discord UI를 통해 쉽게 편집 가능합니다.

<a id="내부-요청-검증-및-보안-구조"></a>
### 🔒 내부 요청 검증 및 보안 구조

모든 내부 API 요청은 `X-Internal-Request` 헤더를 통해 FastAPI 단에서 검증됩니다.  
이 헤더는 Nginx를 통해 외부 요청에는 자동으로 `false`로 설정되며, 내부 Docker 네트워크에서 직접 접근하는 요청만 통과할 수 있습니다.

- 외부 요청 → `X-Internal-Request: false` (Nginx에서 강제 설정)
- 내부 Docker 간 통신 → Nginx를 우회하여 직접 접근 (또는 내부에서 true 설정 가능)

이를 통해 외부에서 내부 API를 가장해 접근하는 시도를 방지합니다.

---

<a id="사용자-입장에서-시작하기"></a>
## 🧭 사용자 입장에서 시작하기

Notipy는 **직접 서버에 설치하지 않아도** 사용할 수 있습니다. 디스코드 서버에 봇을 초대하고 바로 기능을 사용할 수 있습니다. 아래는 기본적인 사용 절차입니다:

### ✅ 1단계. 봇 초대하기

* [공식 홈페이지](https://notipy.code0987.com) 또는 [초대링크](https://discord.com/oauth2/authorize?client_id=955999346321686609&permissions=8&response_type=code&redirect_uri=https%3A%2F%2Fnotipy.code0987.com%2Foauth-popup&integration_type=0&scope=bot+identify)를 활용하여 봇을 초대할 수 있습니다.
* 초대를 하시면 원활한 사용을 위해 `/설정 관리자역할 설정` 명령어를 사용해주세요

<a id="자주-사용하는-명령어-요약"></a>
## 📋 자주 사용하는 명령어 요약

| 명령어                    | 설명               |
| ---------------------- | ---------------- |
| `/설정 보기` | 현재 서버의 설정을 보여줍니다 |
| `/노션 노션토큰 설정`    | Notion 통합 토큰 등록  |
| `/노션 데이터베이스 연결`   | 데이터베이스와 채널 연결    |
| `/노션 데이터베이스 목록`      | 연결된 데이터베이스 목록 보기 |
| `/노션 노션토큰 제거` | Notion 연결 해제     |
| `/티켓생성`       | 디스코드 내 티켓 생성     |
| `/깃허브 연결`         | GitHub 계정 연결     |
| `/프로젝트 생성`      | 프로젝트 생성 및 관리     |


직접 환경 구성 및 서버에 설치하여 사용하고 싶은 경우 아래 "Docker로 실행하기" 섹션을 참고하세요.


---

<a id="docker로-실행하기"></a>
## 🐳 Docker로 실행하기

도커 환경에서 쉽게 실행할 수 있도록 `Dockerfile`과 `docker-compose.yml`이 제공됩니다.  
디스코드 봇을 생성하는 과정은 [Discord-py-Interactions](https://interactions-py.github.io/interactions.py/Guides/)에서, 노션 앱 생성은 [노션 개발자 페이지](https://developers.notion.com/docs/getting-started)를 참고해주세요.

### 1. `.env` 파일 생성

현재 기본적으로 `var.env.example` 파일이 제공되어 있습니다.    
이를 복서하여 `notipy` 루트 디렉토리에 다음 내용을 포함하는 `.env` 파일을 만듭니다:

✅ **수정이 반드시 필요한 값들**
| 항목                   | 설명                                                                        |
| -------------------- | ------------------------------------------------------------------------- |
| `GITHUB_TOKEN`       | GitHub Personal Access Token                                              |
| `DISCORD_TOKEN`      | Discord 봇 토큰                                                              |
| `DISCORD_CLIENT_ID`  | Discord 애플리케이션 클라이언트 ID                                                   |
| `DISCORD_SECRET`     | Discord 애플리케이션 클라이언트 Secret                                               |
| `DISCORD_DEVSERVER`  | 테스트용 Discord 서버 ID (예: `123456789012345678`)                              |
| `DISCORD_DEVELOPERS` | Discord 개발자 ID들, 쉼표로 구분 (예: `123,456,789`)                                |
| `DISCORD_OAUTH2_URL` | Discord OAuth2 인증 URL (예: `https://discord.com/api/oauth2/authorize?...`) |
| `REDIRECT_URI`       | OAuth2 인증 후 리디렉션될 URI (예: `https://yourdomain.com/discord/redirect`)      |
| `NOTION_TOKEN`       | Notion integration 토큰                                                     |
| `MYSQL_USER`         | MySQL 사용자 이름                                                              |
| `MYSQL_PASSWORD`     | MySQL 비밀번호                                                                |
| `MYSQL_DATABASE`     | 사용할 MySQL 데이터베이스 이름                                                       |

🟡 **선택적으로 수정 가능한 값들**
| 항목                   | 설명                               |
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
| 위치                              | 항목                              | 설명                                                                                                                                                          |
| ------------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `discordbot` → `container_name` | `notipy-discordbot`             | 필요 시 컨테이너명 변경 가능, 변경시 Docker Network 접근 URL 이 달라지니 비추천                                                                                                                                    |
| `discordbot` → `DEBUG` | `notipy-discordbot` | 디버그 모드를 활성화 할지 여부입니다. 디버그 모드를 활성화 할경우 개발서버를 제외한 모든 서버에서 나가며 개발서버와 모든 명령어를 강제 동기화 하며 일부 로깅 기능이 강화됩니다.     |
| `backend` → `container_name`    | `notipy-backend`                | 이 또한 필요시 변경                                                                                                                                     |
| `database` → `volumes`          | `./database:/var/lib/mysql`     | 실제 볼륨 경로 확인 및 유지 가능                                                                                                                                         |
| `networks`                      | `nginx-proxy`, `notipy_backend` | 2번 단계에서 생성된 네트워크 이름과 일치해야함 |


이 밖에도 각종 포트번호가 var.env 파일과 일치하는지 확인  


### 3. Docker 컨테이너 실행
```bash
docker compose up -d
```
nginx, Ollama 컨테이너는 사용하지 않으실 경우 굳이 생성하실 필요는 없습니다.   
```bash
docker compose up database backend discordbot -d
```

---

<a id="contributing"></a>
## 🤝 Contributing

Notipy는 오픈소스 프로젝트로, 누구든지 기여할 수 있습니다.

기여 전 다음 사항을 확인해주세요:

### 🧩 기여 방법

1. 이 저장소를 **Fork**합니다.
2. 새로운 브랜치를 생성합니다:  
3. 원하는 기능을 추가하거나 버그를 수정합니다.
4. Pull Request를 생성합니다.
    - PR 제목은 `[기능] 기능명` 또는 `[버그] 버그명` 형식으로 작성합니다.
    - PR 설명에는 변경 사항, 관련 이슈 번호, 테스트 방법 등을 포함합니다.
    - PR은 `dev/main` 브랜치로 생성합니다.
5. 기여한 내용을 설명하는 PR 템플릿을 작성합니다.   
    - 이때 코드는 자동으로 포맷팅됩니다.

자세한 사항은 [기여 가이드](CONTRIBUTING.md)를 참고하세요.

---

<a id="커뮤니티"></a>
## 커뮤니티
각종 공지사항 및 봇에대한 도움을 받을 수 있는 곳입니다.
- 공식 홈페이지 : [링크](https://notipy.code0987.com)
- 디스코드 지원서버: [초대링크](https://discord.gg/HzAnBSCN7t)
- 또는 봇에게 DM 하세요!
- 공식 GitHub 저장소: [Notipy-DiscordBot/Notipy](https://github.com/Notipy-DiscordBot/Notipy)

<a id="이용약관-및-개인정보-처리방침"></a>
## 📃 이용약관 및 개인정보 처리방침
서비스 이용약관과 개인정보 처리방침 전문은 다음 문서에서 확인할 수 있습니다.
- [이용약관 및 개인정보 처리방침 (한국어)](docs/ko/terms-policy.md)
- [Terms of Service and Privacy Policy (English)](docs/en/terms-policy.md)

---

<a id="license"></a>
## License
본 프로젝트는 Apache 2.0 라이센스를 따릅니다.
