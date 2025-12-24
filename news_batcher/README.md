# Synology Gemini 뉴스 배처

Google Gemini와 FastAPI를 활용하여 매일 경제 뉴스를 수집하고 요약하여 MariaDB에 저장하는 시스템입니다. Synology NAS의 Docker 환경에서 쉽게 실행할 수 있도록 설계되었습니다.

## 주요 기능

*   **뉴스 수집**: Google 뉴스 RSS (경제 섹션)에서 최신 뉴스를 가져옵니다. (기본값: 한국 경제)
*   **AI 요약**: Google Gemini API를 사용하여 각 뉴스를 한국어로 10줄 요약합니다.
*   **자동 실행**: 매일 지정된 시간(기본: 오전 9시)에 자동으로 배치가 실행됩니다.
*   **DB 저장**: 수집된 데이터는 MariaDB에 안전하게 저장됩니다.

## 설치 및 실행 방법 (Synology Docker - 외부 DB 사용)

기존에 실행 중인 MariaDB/MySQL 데이터베이스가 있다는 가정하에 설정되었습니다.

1.  **프로젝트 다운로드**: NAS의 적절한 폴더에 이 프로젝트 파일들을 업로드합니다.
2.  **데이터베이스 준비**:
    *   기존 DB에 `news_db` 데이터베이스를 생성해 두세요. (혹은 원하는 이름)
    *   `schema.sql` 파일의 내용을 참고하여 테이블을 미리 생성해도 되지만, 앱 실행 시 자동으로 테이블을 생성하려고 시도합니다.
3.  **환경 변수 설정**: `docker-compose.yml` 파일에서 다음 내용을 수정합니다.
    *   `DATABASE_URL`: `mysql+pymysql://아이디:비번@DB주소:포트/DB이름` 형식으로 입력합니다.
    *   Synology 내부 네트워크의 DB라면 `localhost` 대신 NAS 내부 IP를 사용해야 합니다.
    *   `GEMINI_API_KEY`: [Google AI Studio](https://aistudio.google.com/)에서 발급받은 키를 입력합니다.
4.  **실행**:
    *   SSH로 접속하여 `docker-compose up -d --build` 명령어를 실행하거나,
    *   Synology Container Manager에서 프로젝트를 생성하여 실행합니다.

## API 사용법

*   **상태 확인**: `GET http://<NAS_IP>:8000/`
*   **수동 배치 실행**: `POST http://<NAS_IP>:8000/trigger-batch`
*   **저장된 뉴스 조회**: `GET http://<NAS_IP>:8000/news`

## 파일 구조

*   `app/`: 소스 코드 (FastAPI, 로직)
*   `Dockerfile`: 앱 이미지 빌드 설정
*   `docker-compose.yml`: 컨테이너 실행 설정 (App 단독)
*   `schema.sql`: 데이터베이스 스키마 참고용


## 주의사항

*   초기 실행 시 MariaDB가 초기화되는 데 시간이 조금 걸릴 수 있습니다.
*   Gemini API 사용량 제한에 주의하세요.

## 로컬 테스트 방법 (Windows)

Synology에 올리기 전에 로컬 PC에서 테스트하려면 다음 두 가지 방법 중 하나를 사용하세요.

### 방법 1: Docker Desktop 사용 (권장)
Docker Desktop이 설치되어 있다면 가장 간단한 방법입니다.

1.  프로젝트 폴더(`d:\ai\news_batcher`)로 이동합니다.
2.  `docker-compose.yml` 파일을 열어 `GEMINI_API_KEY` 항목에 실제 키를 입력하거나 `.env` 파일을 생성합니다.
3.  터미널(PowerShell)에서 다음 명령어를 실행합니다:
    ```powershell
    docker-compose up --build
    ```
4.  브라우저에서 `http://localhost:8000/docs` 로 접속하여 API를 테스트합니다.

### 방법 2: Python 직접 실행 (SQLite 사용)
Docker 없이 Python 환경에서 바로 실행하려면 데이터베이스를 SQLite로 변경하는 것이 편합니다.

1.  가상환경 생성 및 패키지 설치:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  환경 변수 설정 (PowerShell):
    ```powershell
    $env:GEMINI_API_KEY="여기에_API_키_입력"
    $env:DATABASE_URL="sqlite:///./local_test.db"
    ```
3.  서버 실행:
    ```powershell
    uvicorn app.main:app --reload
    ```

## Docker Hub 배포 방법

도커 이미지를 빌드하여 Docker Hub에 업로드하려면 다음 절차를 따르세요.

1. **로그인**
   터미널에서 도커 허브 계정으로 로그인합니다.
   ```bash
   docker login
   ```

2. **이미지 빌드 및 태그 설정**
   본인의 도커 허브 아이디와 레포지토리 이름으로 이미지를 빌드합니다.
   (예: 아이디가 `myuser`, 레포지토리가 `news-batcher`인 경우)
   ```bash
   # 이미지 빌드 (맨 뒤 점(.) 필수)
   # myuser 부분을 본인의 Docker Hub ID로 변경하세요.
   docker build -t myuser/news-batcher:latest .
   ```

3. **이미지 푸시 (업로드)**
   ```bash
   docker push myuser/news-batcher:latest
   ```

4. **Synology 등 타 서버에서 실행**
   `docker-compose.yml`의 `image:` 필드를 위에서 푸시한 이미지명으로 변경하거나, 아래 명령어로 직접 실행할 수 있습니다.
   ```bash
   docker run -d --name news_batcher \
     -p 8000:8000 \
     -e DATABASE_URL="mysql+pymysql://..." \
     -e GEMINI_API_KEY="AIza..." \
     myuser/news-batcher:latest

    docker-compose -f docker-compose-synology.yml up -d
   ```

## 주의: Synology DB 연결 오류 해결 (`ECONNREFUSED 127.0.0.1`)

Synology NAS에서 도커 컨테이너 실행 시 `127.0.0.1`로 접속하면 오류가 발생합니다. 이는 **컨테이너 내부의 localhost**를 의미하기 때문입니다.

1.  **NAS IP 확인하기**
    *   `127.0.0.1` 대신 Synology NAS의 **사설 IP 주소**를 사용해야 합니다.
    *   예: `192.168.0.10` 또는 `172.30.1.5` 등
    *   제어판 -> 네트워크 -> 네트워크 인터페이스 에서 확인할 수 있습니다.

2.  **DATABASE_URL 수정**
    *   Synology Container Manager(Docker) -> 컨테이너 -> 세부사항 -> 설정 -> 환경 변수에서 `DATABASE_URL`을 수정하세요.
    *   **변경 전**: `mysql+pymysql://root:비번@127.0.0.1:3306/albert` (X)
    *   **변경 후**: `mysql+pymysql://root:비번@192.168.0.10:3306/albert` (O)

3.  **MariaDB 외부 접속 허용**
    *   Synology 패키지 센터의 MariaDB 설정에서 "TCP/IP 연결 활성화"가 체크되어 있어야 합니다.
    *   또한 방화벽이 3306 포트를 차단하고 있지 않은지 확인하세요.
