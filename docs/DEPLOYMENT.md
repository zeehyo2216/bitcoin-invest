# 리눅스 서버 배포 가이드

> 📍 위치: `Docs/DEPLOYMENT.md`

## 📋 사전 준비사항

### 1. 시스템 요구사항
- Python 3.8 이상
- 인터넷 연결 (바이낸스 API 접근)
- 최소 512MB RAM
- 디스크 공간: 1GB 이상

### 2. 필요한 패키지 설치 (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

## 🚀 배포 단계

### Step 1: 프로젝트 파일 업로드
```bash
# 서버에 프로젝트 디렉토리 업로드
scp -r bitcoin-invest/ user@your-server:/path/to/
```

### Step 2: 배포 스크립트 실행
```bash
cd /path/to/bitcoin-invest
chmod +x deploy.sh
./deploy.sh
```

### Step 3: 환경 변수 설정
```bash
cp .env.example .env
nano .env
```

`.env` 파일에 다음 정보 입력:
```bash
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
SYMBOL=BTCUSDT
LEVERAGE=20
INITIAL_BALANCE=600
INTERVAL=5m
TESTNET=False

# 로그 설정 (선택사항)
LOG_DIR=/var/log/trading_bot
LOG_TO_CONSOLE=false
```

### Step 4: 로그 디렉토리 권한 설정 (선택사항)
```bash
# /var/log 사용 시
sudo mkdir -p /var/log/trading_bot
sudo chown $USER:$USER /var/log/trading_bot
sudo chmod 755 /var/log/trading_bot
```

## 🔄 실행 방법

### 방법 1: 직접 실행 (테스트용)
```bash
cd /path/to/bitcoin-invest
source venv/bin/activate  # 가상환경 사용 시
python3 main.py
```

### 방법 2: 백그라운드 실행 (nohup)
```bash
cd /path/to/bitcoin-invest
source venv/bin/activate
nohup python3 main.py > /dev/null 2>&1 &
echo $! > bot.pid  # 프로세스 ID 저장
```

종료:
```bash
kill $(cat bot.pid)
```

### 방법 3: systemd 서비스 (권장)

#### 3-1. 서비스 파일 수정
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

다음 내용 수정:
- `YOUR_USERNAME`: 실제 사용자명
- `/path/to/bitcoin-invest`: 실제 프로젝트 경로
- Python 경로 확인: `which python3`

#### 3-2. 서비스 등록 및 시작
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

#### 3-3. 서비스 관리 명령어
```bash
# 상태 확인
sudo systemctl status trading-bot

# 로그 확인
sudo journalctl -u trading-bot -f

# 재시작
sudo systemctl restart trading-bot

# 중지
sudo systemctl stop trading-bot

# 시작
sudo systemctl start trading-bot
```

### 방법 4: PM2 사용 (Node.js 기반 프로세스 매니저)
```bash
# PM2 설치
npm install -g pm2

# 봇 실행
cd /path/to/bitcoin-invest
pm2 start main.py --name trading-bot --interpreter python3

# 자동 재시작 설정
pm2 startup
pm2 save

# 관리
pm2 status
pm2 logs trading-bot
pm2 restart trading-bot
pm2 stop trading-bot
```

## 📊 모니터링

### 로그 확인
```bash
# 로그 파일 확인
tail -f logs/trading_bot_$(date +%Y-%m-%d).log

# 또는 systemd 사용 시
sudo journalctl -u trading-bot -f
```

### 프로세스 확인
```bash
ps aux | grep main.py
```

### 리소스 사용량 확인
```bash
top -p $(pgrep -f main.py)
```

## 🔧 문제 해결

### 1. 권한 오류
```bash
# 로그 디렉토리 권한 확인
ls -la logs/
chmod 755 logs/
```

### 2. Python 모듈 오류
```bash
# 의존성 재설치
pip install -r requirements.txt --force-reinstall
```

### 3. API 연결 오류
- 방화벽 설정 확인
- API 키 권한 확인
- 네트워크 연결 확인

### 4. 서비스가 시작되지 않음
```bash
# 로그 확인
sudo journalctl -u trading-bot -n 50

# 서비스 파일 문법 확인
sudo systemctl daemon-reload
```

## 🔒 보안 권장사항

1. **.env 파일 보호**
   ```bash
   chmod 600 .env
   ```

2. **API 키 보안**
   - IP 화이트리스트 설정
   - 최소 권한만 부여
   - 정기적으로 키 갱신

3. **방화벽 설정**
   ```bash
   # 필요한 포트만 열기
   sudo ufw allow 22/tcp  # SSH
   ```

4. **로그 파일 권한**
   ```bash
   chmod 644 logs/*.log
   ```

## 📝 체크리스트

배포 전 확인사항:
- [ ] Python 3.8+ 설치 확인
- [ ] .env 파일 설정 완료
- [ ] API 키 권한 확인 (선물 거래 활성화)
- [ ] 로그 디렉토리 생성 및 권한 확인
- [ ] 테스트넷에서 먼저 테스트
- [ ] 방화벽 설정 확인
- [ ] 서비스 파일 경로 수정 완료
- [ ] 백업 계획 수립

## 🆘 긴급 상황 대응

### 봇 중지
```bash
# systemd 사용 시
sudo systemctl stop trading-bot

# 직접 실행 시
pkill -f main.py
```

### 모든 포지션 청산 (수동)
바이낸스 웹사이트에서 직접 청산하거나 API를 통해 청산

### 로그 확인
```bash
tail -100 logs/trading_bot_$(date +%Y-%m-%d).log
```

