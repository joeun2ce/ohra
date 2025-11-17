# OHRA Open WebUI

Open WebUI 프로젝트 디렉토리입니다.

## 구조

```
ohra-open-webui/
├── data/          # webui.db 저장 디렉토리
└── README.md      # 이 파일
```

## 데이터베이스

- SQLite 데이터베이스 파일: `data/webui.db`
- docker-compose.yml에서 volume으로 마운트됩니다.

## 설정

docker-compose.yml에서 다음 환경변수로 설정됩니다:
- `OPENAI_API_BASE_URL`: Backend API URL
- `DATABASE_URL`: SQLite 데이터베이스 경로
- 기타 WebUI 설정들

