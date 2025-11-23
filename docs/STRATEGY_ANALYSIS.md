# 투자 전략 상세 분석

> 📍 위치: `Docs/STRATEGY_ANALYSIS.md`

## 📊 전체 전략 구조

이 코드는 **다중 지표 융합 기술적 분석(Multi-Indicator Technical Analysis)**과 **리스크 기반 포지션 사이징(Risk-Based Position Sizing)**을 결합한 자동화 트레이딩 전략입니다.

---

## 1. 기술적 지표 분석 (indicators.py)

### 1.1 추세 지표 (Trend Indicators)

#### EMA (Exponential Moving Average)
```python
# indicators.py:44-49
self.df['ema_9'] = EMAIndicator(close=self.df['close'], window=9).ema_indicator()
self.df['ema_21'] = EMAIndicator(close=self.df['close'], window=21).ema_indicator()
self.df['ema_50'] = EMAIndicator(close=self.df['close'], window=50).ema_indicator()
self.df['ema_200'] = EMAIndicator(close=self.df['close'], window=200).ema_indicator()
```

**경제학 원리:**
- **이동평균 이론 (Moving Average Theory)**: 가격의 단기 변동을 완화하여 장기 추세를 파악
- **EMA vs SMA**: 최근 가격에 더 높은 가중치를 부여 (지수 가중)
- **다중 기간 분석**: 9일(단기), 21일(중기), 50일(장기), 200일(초장기)로 추세의 강도와 방향 파악

**크로스오버 전략:**
```python
# indicators.py:124-135
if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
    if prev['ema_9'] <= prev['ema_21']:
        return 'BULLISH_CROSS'  # 골든 크로스
```

**이론적 배경:**
- **골든 크로스 (Golden Cross)**: 단기 이동평균이 장기 이동평균을 상향 돌파 → 강세 신호
- **데드 크로스 (Death Cross)**: 단기 이동평균이 장기 이동평균을 하향 돌파 → 약세 신호
- **다우 이론 (Dow Theory)**: 추세의 3단계 (주요 추세, 중간 조정, 단기 변동)

#### MACD (Moving Average Convergence Divergence)
```python
# indicators.py:37-42
macd = MACD(close=self.df['close'])
self.df['macd'] = macd.macd()
self.df['macd_signal'] = macd.macd_signal()
self.df['macd_diff'] = macd.macd_diff()
```

**경제학 원리:**
- **모멘텀 이론**: 가격 변화의 속도와 방향을 측정
- **MACD = EMA(12) - EMA(26)**: 두 이동평균의 수렴/발산을 측정
- **신호선 크로스**: MACD가 신호선을 상향 돌파 → 매수, 하향 돌파 → 매도

**신호 생성 로직:**
```python
# indicators.py:137-155
macd_bullish = latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']
if macd_bullish and rsi_oversold:
    return 'STRONG_BUY'
```

**이론적 배경:**
- **Gerald Appel의 MACD 이론**: 1970년대 개발, 추세 추종과 모멘텀을 결합
- **발산 (Divergence)**: 가격과 지표의 방향이 다를 때 추세 전환 가능성

### 1.2 모멘텀 지표 (Momentum Indicators)

#### RSI (Relative Strength Index)
```python
# indicators.py:56-59
rsi = RSIIndicator(close=self.df['close'], window=14)
self.df['rsi'] = rsi.rsi()
```

**경제학 원리:**
- **상대강도 지수**: 0-100 범위에서 과매수/과매도 구간 판단
- **RSI = 100 - (100 / (1 + RS))**, RS = 평균 상승폭 / 평균 하락폭
- **평균회귀 이론 (Mean Reversion)**: 극단적 수준에서 반등 가능성

**과매수/과매도 구간:**
```python
# strategy.py:75-84
if 30 < rsi < 40:
    score += 1.5  # 과매도 근처 (반등 가능)
elif rsi < 30:
    score += 0.5  # 과매도 (반등 가능하지만 약함)
elif rsi > 70:
    score -= 0.5  # 과매수 (하락 가능)
```

**이론적 배경:**
- **J. Welles Wilder의 RSI (1978)**: 14일 기간이 표준
- **과매수 (Overbought)**: RSI > 70 → 매도 압력 증가
- **과매도 (Oversold)**: RSI < 30 → 매수 압력 증가

#### Stochastic Oscillator
```python
# indicators.py:61-70
stoch = StochasticOscillator(
    high=self.df['high'],
    low=self.df['low'],
    close=self.df['close'],
    window=14
)
```

**경제학 원리:**
- **%K = ((현재가 - 최저가) / (최고가 - 최저가)) × 100**
- **가격의 상대적 위치**: 일정 기간 내에서 현재가의 위치를 백분율로 표현
- **모멘텀 측정**: 가격 변화의 속도와 방향

### 1.3 변동성 지표 (Volatility Indicators)

#### 볼린저 밴드 (Bollinger Bands)
```python
# indicators.py:72-78
bb = BollingerBands(close=self.df['close'], window=20, window_dev=2)
self.df['bb_upper'] = bb.bollinger_hband()  # 상단 밴드
self.df['bb_middle'] = bb.bollinger_mavg()  # 중간선 (SMA 20)
self.df['bb_lower'] = bb.bollinger_lband()  # 하단 밴드
```

**경제학 원리:**
- **통계적 변동성**: 표준편차(σ)를 이용한 변동성 측정
- **상단 밴드 = SMA(20) + 2σ**, **하단 밴드 = SMA(20) - 2σ**
- **평균회귀**: 밴드 밖으로 벗어나면 평균으로 회귀할 가능성

**신호 생성:**
```python
# strategy.py:86-99
if price < bb_lower:
    score += 1.0  # 하단 터치 (반등 가능)
elif price > bb_upper:
    score -= 1.0  # 상단 터치 (하락 가능)
```

**이론적 배경:**
- **John Bollinger의 볼린저 밴드 (1980년대)**: 변동성 기반 거래 전략
- **밴드 폭 (Bandwidth)**: 변동성의 크기를 나타냄
- **스퀴즈 (Squeeze)**: 밴드가 좁아지면 큰 움직임 예고

#### ATR (Average True Range)
```python
# indicators.py:80-88
atr = AverageTrueRange(
    high=self.df['high'],
    low=self.df['low'],
    close=self.df['close'],
    window=14
)
self.df['atr'] = atr.average_true_range()
```

**경제학 원리:**
- **변동성 측정**: 가격의 실제 변동 범위를 측정
- **True Range = max(high-low, |high-prev_close|, |low-prev_close|)**
- **리스크 관리**: 변동성에 따라 포지션 크기와 SL 거리 조정

**리스크 관리 활용:**
```python
# strategy.py:140-143
sl_distance = atr * 2  # Stop Loss 거리 = 2 ATR
if sl_distance == 0:
    sl_distance = price * 0.01  # 기본 1%
```

**이론적 배경:**
- **J. Welles Wilder의 ATR (1978)**: 변동성 기반 리스크 관리
- **동적 리스크 관리**: 시장 변동성에 따라 SL 거리를 조정

### 1.4 거래량 지표 (Volume Indicators)

#### 거래량 SMA
```python
# indicators.py:90-92
self.df['volume_sma'] = self.df['volume'].rolling(window=20).mean()
volume_ratio = latest['volume'] / latest['volume_sma']
```

**경제학 원리:**
- **거래량 분석 (Volume Analysis)**: 가격 움직임의 신뢰도 측정
- **가격-거래량 관계**: 가격 상승 + 거래량 증가 = 강한 상승 추세
- **거래량 비율**: 평균 대비 현재 거래량으로 시장 관심도 측정

**신호 강화:**
```python
# strategy.py:101-108
if volume_ratio > 1.5:  # 거래량이 평균의 1.5배 이상
    if score > 0:
        score += 0.5  # 상승 추세 강화
    elif score < 0:
        score -= 0.5  # 하락 추세 강화
```

**이론적 배경:**
- **Wyckoff 이론**: 가격과 거래량의 관계 분석
- **On-Balance Volume (OBV)**: 거래량 누적을 통한 추세 확인

---

## 2. 종합 점수 시스템 (strategy.py)

### 2.1 가중치 기반 의사결정

```python
# strategy.py:51-110
def _calculate_score(self, signals: Dict, latest: pd.Series) -> float:
    score = 0.0
    
    # 1. 추세 점수 (40%)
    # 2. 모멘텀 점수 (30%)
    # 3. RSI 점수 (15%)
    # 4. 볼린저 밴드 점수 (10%)
    # 5. 거래량 점수 (5%)
```

**경제학 원리:**
- **다중 기준 의사결정 (Multi-Criteria Decision Making, MCDM)**
- **가중 평균**: 각 지표의 중요도에 따라 가중치 부여
- **정보 융합 (Information Fusion)**: 여러 정보원을 결합하여 신뢰도 향상

**가중치 배분 이유:**
1. **추세 (40%)**: 가장 중요한 요소, 추세를 따르는 것이 수익성 높음
2. **모멘텀 (30%)**: 추세의 강도와 지속성 측정
3. **RSI (15%)**: 과매수/과매도 구간 판단
4. **볼린저 밴드 (10%)**: 변동성 기반 진입/청산 시점
5. **거래량 (5%)**: 신호의 신뢰도 보조 지표

**이론적 배경:**
- **효율적 시장 가설 (EMH) 약형**: 과거 가격 정보는 이미 반영됨 → 기술적 분석의 한계
- **행동 금융학 (Behavioral Finance)**: 시장 참가자의 심리적 편향 활용
- **추세 추종 전략 (Trend Following)**: "추세는 당신의 친구" (The trend is your friend)

### 2.2 신호 결정 로직

```python
# strategy.py:112-128
def _determine_entry_signal(self, score: float, signals: Dict) -> str:
    if score >= 6.0:
        return 'STRONG_LONG'    # 강한 매수
    elif score >= 3.0:
        return 'LONG'           # 매수
    elif score <= -6.0:
        return 'STRONG_SHORT'   # 강한 매도
    elif score <= -3.0:
        return 'SHORT'          # 매도
    else:
        return 'HOLD'           # 보류
```

**경제학 원리:**
- **임계값 기반 의사결정 (Threshold-Based Decision Making)**
- **리스크-수익 트레이드오프**: 신호 강도에 따라 포지션 크기 조정 가능
- **불확실성 관리**: 중립 구간(-3 ~ +3)에서는 거래하지 않음

**이론적 배경:**
- **신호 이론 (Signal Theory)**: 노이즈와 진짜 신호 구분
- **샘플링 이론**: 충분한 신뢰도 확보 후 행동

---

## 3. 리스크 관리 (Risk Management)

### 3.1 포지션 사이징 (Position Sizing)

```python
# strategy.py:130-155
def _calculate_position_size(self, price: float, atr: float) -> float:
    # 사용 가능한 자본의 80%만 사용
    available_capital = self.initial_balance * self.position_size_multiplier  # 0.8
    
    # 레버리지 적용
    leveraged_capital = available_capital * self.leverage  # 20x
    
    # 리스크 기반 포지션 크기
    risk_amount = self.initial_balance * self.risk_per_trade  # 2%
    sl_distance = atr * 2  # Stop Loss 거리
    
    # 리스크에 맞는 포지션 크기
    position_size_usdt = risk_amount / (sl_distance / price)
    
    # 최대 포지션 크기 제한
    max_position = leveraged_capital
    position_size_usdt = min(position_size_usdt, max_position)
```

**경제학 원리:**

#### 1. **Kelly Criterion (켈리 공식) 변형**
- **원래 공식**: f* = (p × b - q) / b
  - f*: 최적 베팅 비율
  - p: 승률
  - q: 패배 확률 (1-p)
  - b: 승리 시 배당률
- **이 코드의 적용**: 고정 리스크 비율 (2%) 사용
- **보수적 접근**: Kelly의 절반 정도만 사용 (자본의 80%)

#### 2. **Fixed Fractional Position Sizing**
- **리스크 금액 고정**: 거래당 총 자본의 2%만 리스크
- **ATR 기반 동적 조정**: 변동성에 따라 포지션 크기 자동 조정
- **레버리지 활용**: 20배 레버리지로 수익 극대화 (동시에 리스크도 증가)

#### 3. **자본 보존 원칙**
```python
self.position_size_multiplier = 0.8  # 자본의 80%만 사용
```
- **안전 마진**: 전체 자본을 사용하지 않아 급격한 손실 방지
- **연속 손실 대비**: 여러 번의 손실에도 생존 가능

**이론적 배경:**
- **Ralph Vince의 Portfolio Management Formulas**: 최적 포지션 사이징
- **Van Tharp의 Position Sizing**: 리스크 기반 포지션 관리
- **자본 보존 (Capital Preservation)**: 수익보다 손실 방지가 우선

### 3.2 레버리지 활용

```python
# strategy.py:135-136
leveraged_capital = available_capital * self.leverage  # 20x
```

**경제학 원리:**
- **레버리지 효과**: 작은 자본으로 큰 포지션 운영
- **수익률 증폭**: 1% 가격 변동 → 20% 수익/손실 (20배 레버리지)
- **마진 콜 리스크**: 가격 변동이 크면 강제 청산 가능

**리스크 관리:**
- **레버리지 20x**: 고위험 고수익 전략
- **초기 자본 600 USDT**: 레버리지 적용 시 최대 12,000 USDT 포지션 가능
- **실제 사용**: 리스크 기반 계산으로 더 작은 포지션 사용

**이론적 배경:**
- **Modigliani-Miller 정리**: 레버리지가 기업 가치에 미치는 영향
- **Black-Scholes 모델**: 옵션 가격 결정에서 레버리지 개념 활용

### 3.3 Take Profit / Stop Loss 설정

```python
# strategy.py:157-194
def _calculate_tp_sl(self, entry_price: float, signal: str, atr: float):
    atr_distance = atr * 2
    
    if signal in ['LONG', 'STRONG_LONG']:
        tp_price = entry_price + (atr_distance * 3)  # TP: 3 ATR
        sl_price = entry_price - atr_distance         # SL: 2 ATR
```

**경제학 원리:**

#### 1. **Risk-Reward Ratio (위험-수익 비율)**
- **TP:SL = 3:2 = 1.5:1**: 수익 목표가 손실 한도보다 1.5배 큼
- **이론적 최소 승률**: 1.5:1 비율에서 최소 40% 승률 필요
  - 승률 40%: (0.4 × 1.5) - (0.6 × 1) = 0 (손익분기)
  - 승률 50%: (0.5 × 1.5) - (0.5 × 1) = 0.25 (25% 수익)

#### 2. **ATR 기반 동적 설정**
- **변동성 적응**: 시장 변동성이 클수록 TP/SL 거리 증가
- **노이즈 필터링**: 작은 변동성에서는 TP/SL이 너무 가까워 조정

#### 3. **최소 비율 보장**
```python
if tp_ratio < 0.01:  # 최소 1% 수익
    tp_price = entry_price * 1.01
if sl_ratio < 0.005:  # 최소 0.5% 손실
    sl_price = entry_price * 0.995
```

**이론적 배경:**
- **손익분기점 분석 (Break-Even Analysis)**
- **최적화 이론**: 수익 극대화와 리스크 최소화의 균형
- **행동 금융학**: 손절매 심리적 저항 극복 (자동화)

---

## 4. 포지션 관리 (position_manager.py)

### 4.1 진입 조건

```python
# position_manager.py:23-40
def should_open_position(self, analysis: Dict, current_position: Optional[Dict]) -> bool:
    signal = analysis['signal']
    confidence = analysis['confidence']
    
    # HOLD 신호면 포지션 오픈 안함
    if signal == 'HOLD':
        return False
    
    # 이미 포지션이 있으면 오픈 안함
    if current_position:
        return False
    
    # 신뢰도가 0.5 이상일 때만 진입
    if confidence < 0.5:
        return False
```

**경제학 원리:**
- **확률적 의사결정**: 신뢰도 임계값(50%) 이상일 때만 행동
- **기회비용 (Opportunity Cost)**: 불확실한 기회보다 기회 비용 최소화
- **단일 포지션 원칙**: 한 번에 하나의 포지션만 유지 (리스크 집중 방지)

**이론적 배경:**
- **베이지안 의사결정 이론**: 사전 확률과 신뢰도 결합
- **불확실성 하의 선택**: Knightian Uncertainty 대응

### 4.2 청산 조건

```python
# position_manager.py:42-68
def should_close_position(self, analysis: Dict, current_position: Optional[Dict]) -> bool:
    signal = analysis['signal']
    position_side = current_position['side']
    
    # 반대 신호가 나오면 청산
    if position_side == 'LONG' and signal in ['SHORT', 'STRONG_SHORT']:
        return True
    
    # HOLD 신호이고 추세 반전이면 청산
    if signal == 'HOLD':
        if signals['trend'] in ['BEARISH', 'BEARISH_CROSS']:
            if signals['momentum'] in ['SELL', 'STRONG_SELL']:
                return True
```

**경제학 원리:**
- **추세 반전 감지**: 추세가 끝나면 즉시 청산
- **손실 최소화**: 추세 전환 시점에서 빠른 대응
- **확인 신호**: 추세와 모멘텀 모두 반전 확인 후 청산

**이론적 배경:**
- **추세 전환 이론**: 추세의 3단계 (축적, 참여, 분배)
- **시장 사이클**: 상승 → 정점 → 하락 → 저점의 반복

---

## 5. 전체 전략의 경제학적 평가

### 5.1 강점

1. **다중 지표 융합**: 단일 지표의 한계 극복
2. **동적 리스크 관리**: ATR 기반 변동성 적응
3. **자동화**: 감정적 편향 제거
4. **레버리지 활용**: 자본 효율성 극대화

### 5.2 약점 및 리스크

1. **기술적 분석의 한계**: 
   - 효율적 시장 가설(EMH)에 따르면 기술적 분석은 장기적으로 초과수익을 보장하지 않음
   - 랜덤 워크 가설: 가격 변동이 랜덤하다면 기술적 분석 무효

2. **과최적화 (Overfitting) 위험**:
   - 과거 데이터에 맞춘 전략이 미래에 작동하지 않을 수 있음
   - 가중치(40%, 30%, 15% 등)가 특정 시장 환경에만 최적화

3. **레버리지 리스크**:
   - 20배 레버리지는 작은 가격 변동으로도 큰 손실 가능
   - 마진 콜 위험

4. **시장 환경 의존성**:
   - 추세 시장에서는 효과적이나 횡보 시장에서는 손실 가능
   - 급격한 시장 변화(블랙스완)에 취약

### 5.3 개선 가능한 부분

1. **백테스팅**: 과거 데이터로 전략 검증
2. **포트폴리오 다각화**: 여러 자산에 분산 투자
3. **동적 가중치**: 시장 환경에 따라 가중치 조정
4. **머신러닝**: 지표 가중치를 학습 데이터로 최적화

---

## 6. 결론

이 전략은 **기술적 분석**, **리스크 관리**, **자동화**를 결합한 체계적인 접근법입니다. 

**핵심 경제학 원리:**
1. **추세 추종 (Trend Following)**: 추세는 지속된다는 가정
2. **평균회귀 (Mean Reversion)**: 극단적 수준에서 반등
3. **리스크 기반 자본 배분**: Kelly Criterion 변형
4. **확률적 의사결정**: 신뢰도 기반 진입/청산

**실전 적용 시 주의사항:**
- 충분한 백테스팅과 포워드 테스팅 필요
- 시장 환경 변화에 대한 모니터링
- 레버리지 리스크 관리
- 감정적 편향 제거 (자동화의 장점)

