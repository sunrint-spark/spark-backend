
# Spark Backend (FastAPI)

Spark 프로젝트의 백엔드



## 프로젝트 실행 준비

 - [Docker or Docker Desktop - 필수](https://www.docker.com/)
 - [docker-compose - 필수](https://docs.docker.com/compose/install/)
 - [Pycharm - 권장](https://www.jetbrains.com/ko-kr/pycharm/)


## 개발 환경 세팅

### 1.virtualenv(venv) 설정하기  
콘솔이나 Pycharm을 통해 venv를 설정하세요.

### 2.의존성 설치하기

```bash
python -m pip install -r requirements.txt
```

### 3.도커 컨테이너 실행하기

```bash
docker compose -f docker-compose-dev.yml up -d
```

### 4.프로젝트 실행

**Windows**
```bash
copy .env.example .env
python -m app
```

**MacOS or Linux**
```
cp .env.example .env
python -m app
```
