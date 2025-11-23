#!/bin/bash
# 리눅스 서버 배포 스크립트

set -e

echo "🚀 바이낸스 트레이딩 봇 배포 시작..."

# 1. Python 버전 확인
echo "📋 Python 버전 확인 중..."
python3 --version || { echo "❌ Python3가 설치되어 있지 않습니다."; exit 1; }

# 2. 가상환경 생성 (선택사항)
if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
fi

# 3. 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source venv/bin/activate

# 4. 의존성 설치
echo "📥 의존성 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# 6. 로그 디렉토리 생성
echo "📁 로그 디렉토리 생성 중..."
mkdir -p logs
chmod 755 logs

# 7. 실행 권한 부여
chmod +x main.py

echo "✅ 배포 완료!"
echo ""
echo "다음 명령어로 실행하세요:"
echo "  python3 main.py"
echo ""
echo "또는 systemd 서비스로 등록:"
echo "  sudo cp trading-bot.service /etc/systemd/system/"
echo "  sudo nano /etc/systemd/system/trading-bot.service  # 경로 수정 필요"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable trading-bot"
echo "  sudo systemctl start trading-bot"

