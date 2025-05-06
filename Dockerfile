FROM python:3.10-slim

# 작업 디렉토리 생성 및 이동
WORKDIR /app

# requirements 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 나머지 코드 복사
COPY . .

# 포트 노출 (예: 8000)
EXPOSE 8000

# 실행 명령
CMD ["python3", "bot.py"]
