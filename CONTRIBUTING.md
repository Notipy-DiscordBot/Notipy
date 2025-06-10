# 🤝 Contributing to Notipy

Notipy 프로젝트에 기여해주셔서 감사합니다!  
이 문서는 코드 기여, 문서 수정, 버그 리포트 등을 포함한 전반적인 기여 절차를 안내합니다.

---

## 📦 저장소 구조

- [`Notipy`](https://github.com/Notipy-DiscordBot/Notipy) — 메인 레포지토리로 현재 모든 파일이 들어 있습니다.
---

## 🛠 개발 환경 설정

1. 저장소 Fork 및 클론:
   ```bash
   git clone https://github.com/Notipy-DiscordBot/Notipy.git
   cd Notipy
   ```

2. 의존성 설치 및 `.env` 구성:

   * `.env.example`을 복사하여 `.env` 파일을 생성하고, 필요한 설정을 입력해주세요.
   * 로컬 실행 또는 Docker Compose를 통해 빠르게 실행할 수 있습니다.

3. Docker 실행 예시:

   ```bash
   docker compose up database backend discordbot -d
   ```

---

## 🧪 커밋 및 PR 규칙

* **커밋 메시지 스타일**

  ```
  feat: 새로운 기능 추가
  fix: 버그 수정
  docs: 문서 변경
  refactor: 리팩토링
  chore: 빌드/배포 설정 등 잡다한 변경
  ```

* **PR 규칙**

  * 제목: `[feat] 기능명` 또는 `[fix] 버그명`
  * 본문: 변경 목적, 내용 요약, 관련 이슈, 테스트 방법 등
  * 대상 브랜치: `dev/main`

---

## 💬 문의 및 협업

* Discord 서버: [초대링크](https://discord.gg/HzAnBSCN7t)
* 공식 홈페이지: [https://notipy.code0987.com](https://notipy.code0987.com)
* 깃허브 Discussions 또는 Issues 탭에서 의견 주세요!

---

감사합니다 🙌
