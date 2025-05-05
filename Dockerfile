FROM python:3.10-slim

# 작업 디렉토리 생성
WORKDIR /app

# requirements.txt 복사
COPY requirements.txt .

# 패키지 설치 (torch, transformers 포함)
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 코드 복사
COPY . .

# 8000 포트용 헬스체크 HTTP 서버 추가 (선택)
EXPOSE 8000

# 실행 명령
CMD ["python3", "bot.py"]
