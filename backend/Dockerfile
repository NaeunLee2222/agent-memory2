FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    curl wget gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 경로 설정
ENV PYTHONPATH=/app

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p models services database utils evaluation

# __init__.py 파일들 생성
RUN touch __init__.py && \
    touch models/__init__.py && \
    touch services/__init__.py && \
    touch database/__init__.py && \
    touch utils/__init__.py && \
    touch evaluation/__init__.py

# 포트 노출
EXPOSE 8000

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 시작
CMD ["python", "main.py"]