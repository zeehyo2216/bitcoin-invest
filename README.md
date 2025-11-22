# 바이낸스 선물 거래 봇

바이낸스 선물 거래를 위한 자동화된 트레이딩 봇입니다. 여러 기술적 지표를 분석하여 최적의 진입/청산 시점을 결정합니다.

## 주요 기능

- 📊 **다양한 기술적 지표 분석**
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - EMA/SMA (Exponential/Simple Moving Averages)
  - 볼린저 밴드 (Bollinger Bands)
  - Stochastic Oscillator
  - ATR (Average True Range)
  - 거래량 분석

- 🎯 **통합 투자 전략**
  - 여러 지표를 종합한 점수 기반 신호 생성
  - 레버리지 20x 지원
  - 자동 TP/SL 설정
  - 리스크 관리 (거래당 2% 리스크)

- ⏰ **실시간 모니터링**
  - 5분 간격 자동 분석
  - 현재 포지션 상태 실시간 표시
  - 미실현 손익 추적

## 설치 방법

### 1. 필요한 라이브러리 설치

```bash
python3 -m pip install -r requirements.txt
```

또는

```bash
pip3 install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 바이낸스 API 키를 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
SYMBOL=BTCUSDT
LEVERAGE=20
INITIAL_BALANCE=600
INTERVAL=5m
TESTNET=False
```

### 3. 바이낸스 API 키 발급

1. [바이낸스](https://www.binance.com)에 로그인
2. API Management로 이동
3. 새로운 API 키 생성
4. **선물 거래 권한** 활성화 필수
5. IP 제한 설정 권장 (보안)

⚠️ **주의사항**: 
- 실제 거래 전에 `TESTNET=True`로 설정하여 테스트넷에서 먼저 테스트하세요
- API 키는 절대 공개하지 마세요
- 선물 거래는 고위험 투자입니다

## 사용 방법

```bash
python3 main.py
```

봇이 시작되면:
1. 즉시 한 번 분석을 실행합니다
2. 이후 5분 간격으로 자동으로 분석을 반복합니다
3. 종료하려면 `Ctrl+C`를 누르세요

## 투자 전략 설명

### 신호 생성 로직

1. **추세 분석 (40%)**
   - EMA 크로스오버 감지
   - 장기/단기 이동평균선 관계

2. **모멘텀 분석 (30%)**
   - MACD 크로스오버
   - RSI 과매수/과매도 구간

3. **변동성 분석 (15%)**
   - RSI 수준
   - 볼린저 밴드 위치

4. **거래량 분석 (5%)**
   - 평균 거래량 대비 현재 거래량

### 포지션 크기 계산

- 사용 가능한 자본의 80% 사용
- 레버리지 20x 적용
- ATR 기반 리스크 관리
- 거래당 최대 2% 리스크

### TP/SL 설정

- **Take Profit**: 진입가 ± 3 ATR
- **Stop Loss**: 진입가 ± 2 ATR
- 최소 1% 수익, 0.5% 손실 보장

## 파일 구조

```
bitcoin-invest/
├── main.py                 # 메인 실행 스크립트
├── binance_client.py       # 바이낸스 API 클라이언트
├── indicators.py           # 기술적 지표 계산
├── strategy.py             # 투자 전략 로직
├── position_manager.py     # 포지션 관리
├── requirements.txt        # 필요한 라이브러리
├── .env.example           # 환경 변수 예시
└── README.md              # 이 파일
```

## 주의사항

⚠️ **이 봇은 교육 목적으로 제작되었습니다**

- 실제 자금으로 거래하기 전에 충분히 테스트하세요
- 시장 상황에 따라 전략을 조정해야 할 수 있습니다
- 과거 성과가 미래 수익을 보장하지 않습니다
- 선물 거래는 고위험 투자입니다
- 손실을 감당할 수 있는 금액만 투자하세요

## 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.

