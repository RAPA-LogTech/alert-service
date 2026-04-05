# alert-service

Slack OAuth, 이벤트, 메시지 전송과 시크릿 접근을 담당하고,
인시던트 상태/이력을 DynamoDB + S3에 저장/조회하는 FastAPI 서비스입니다. 기본 포트: **8082**

---

## 이미지 빌드 & 푸시

### 빌드 및 푸시

```bash
./deploy.sh
```

### 수동 빌드

```bash
docker build -t rapa-logtech/alert-service:latest .
docker push rapa-logtech/alert-service:latest
```

---

## API Endpoints

| Method | Path | 설명 |
| ------ | ---- | ---- |
| GET | `/health` | 헬스 체크 |
| GET | `/v1/incidents` | 인시던트 목록 조회(status, 커서 페이지네이션) |
| GET | `/v1/incidents/{incident_id}` | 인시던트 상세 조회(DynamoDB + S3) |
| GET | `/v1/slack/oauth/connect` | Slack OAuth 시작(슬랙) |
| GET | `/v1/slack/oauth/callback` | Slack OAuth 콜백(슬랙) |
| POST | `/v1/slack/events` | Slack 이벤트 수신(슬랙) |

---

## 데이터 소스 매핑 (alert-service)

| 데이터 종류 | AWS 소스 | 주요 리소스/키 | 비고 |
| ------ | ---- | ---- | ---- |
| Slack OAuth 설정 | AWS Secrets Manager | Secret `${project_name}-slack-oauth-config` | `client_id`, `client_secret`, `signing_secret`, `bot_scopes` |
| Slack 설치/연동 정보 | AWS Secrets Manager | Secret `${project_name}-slack-installation` | `bot_token`, `team_id`, `channel_id` 등 |
| Slack 알람/이벤트 히스토리 | DynamoDB | Table `${project_name}-slack-messages` | Slack 이벤트/알림 이력 저장 |
| 인시던트 상세 페이로드 | S3 | Bucket `${project_name}-slack-messages-*` | 인시던트 본문/부가 데이터 저장 |

참고:
- OAuth 시작/콜백 처리에서 필요한 자격 정보는 Secrets Manager에서 조회합니다.
- DynamoDB는 Slack 알람/이벤트 및 인시던트 이력 저장 용도로 사용합니다.
