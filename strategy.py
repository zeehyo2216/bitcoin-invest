"""
투자 전략 모듈
"""
import pandas as pd
from typing import Dict, Optional, Tuple
from indicators import TechnicalIndicators


class TradingStrategy:
    """통합 투자 전략 클래스"""
    
    def __init__(self, initial_balance: float = 600, leverage: int = 20, risk_per_trade: float = 0.20):
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.risk_per_trade = risk_per_trade  # 거래당 리스크 (20%)
        self.position_size_multiplier = 0.8  # 사용 가능한 자본의 80%만 사용
    
    def analyze(self, indicators: TechnicalIndicators) -> Dict:
        """시장 분석 및 신호 생성"""
        signals = indicators.get_latest_signals()
        df = indicators.get_dataframe()
        latest = df.iloc[-1]
        
        # 종합 점수 계산
        score = self._calculate_score(signals, latest)
        
        # 진입 신호 결정
        entry_signal = self._determine_entry_signal(score, signals)
        
        # 포지션 크기 계산
        position_size = self._calculate_position_size(signals['price'], signals['atr'])
        
        # TP/SL 계산
        tp_price, sl_price = self._calculate_tp_sl(
            signals['price'],
            entry_signal,
            signals['atr']
        )
        
        return {
            'signal': entry_signal,
            'score': score,
            'position_size': position_size,
            'entry_price': signals['price'],
            'take_profit': tp_price,
            'stop_loss': sl_price,
            'signals': signals,
            'confidence': abs(score) / 10.0  # 신뢰도 (0-1)
        }
    
    def _calculate_score(self, signals: Dict, latest: pd.Series) -> float:
        """종합 점수 계산 (-10 ~ +10)"""
        score = 0.0
        
        # 1. 추세 점수 (40%)
        if signals['trend'] == 'BULLISH_CROSS':
            score += 4.0
        elif signals['trend'] == 'BULLISH':
            score += 2.0
        elif signals['trend'] == 'BEARISH_CROSS':
            score -= 4.0
        elif signals['trend'] == 'BEARISH':
            score -= 2.0
        
        # 2. 모멘텀 점수 (30%)
        if signals['momentum'] == 'STRONG_BUY':
            score += 3.0
        elif signals['momentum'] == 'BUY':
            score += 1.5
        elif signals['momentum'] == 'STRONG_SELL':
            score -= 3.0
        elif signals['momentum'] == 'SELL':
            score -= 1.5
        
        # 3. RSI 점수 (15%)
        rsi = signals['rsi']
        if 30 < rsi < 40:
            score += 1.5  # 과매도 근처
        elif 60 < rsi < 70:
            score -= 1.5  # 과매수 근처
        elif rsi < 30:
            score += 0.5  # 과매도 (반등 가능)
        elif rsi > 70:
            score -= 0.5  # 과매수 (하락 가능)
        
        # 4. 볼린저 밴드 점수 (10%)
        price = signals['price']
        bb_upper = signals['bb_upper']
        bb_lower = signals['bb_lower']
        bb_middle = signals['bb_middle']
        
        if price < bb_lower:
            score += 1.0  # 하단 터치 (반등 가능)
        elif price > bb_upper:
            score -= 1.0  # 상단 터치 (하락 가능)
        elif price < bb_middle:
            score += 0.5  # 중간선 아래
        else:
            score -= 0.5  # 중간선 위
        
        # 5. 거래량 점수 (5%)
        volume_ratio = signals['volume_ratio']
        if volume_ratio > 1.5:
            # 현재 추세와 같은 방향이면 가점
            if score > 0:
                score += 0.5
            elif score < 0:
                score -= 0.5
        
        return max(-10.0, min(10.0, score))
    
    def _determine_entry_signal(self, score: float, signals: Dict) -> str:
        """진입 신호 결정"""
        # 강한 매수 신호
        if score >= 6.0:
            return 'STRONG_LONG'
        # 매수 신호
        elif score >= 3.0:
            return 'LONG'
        # 강한 매도 신호
        elif score <= -6.0:
            return 'STRONG_SHORT'
        # 매도 신호
        elif score <= -3.0:
            return 'SHORT'
        # 보류
        else:
            return 'HOLD'
    
    def _calculate_position_size(self, price: float, atr: float) -> float:
        """포지션 크기 계산 (USDT 기준)"""
        # 사용 가능한 자본
        available_capital = self.initial_balance * self.position_size_multiplier
        
        # 레버리지 적용
        leveraged_capital = available_capital * self.leverage
        
        # 리스크 기반 포지션 크기
        risk_amount = self.initial_balance * self.risk_per_trade
        # ATR 기반 SL 거리 (2 ATR)
        sl_distance = atr * 2
        if sl_distance == 0:
            sl_distance = price * 0.01  # 기본 1%
        
        # 리스크에 맞는 포지션 크기
        position_size_usdt = risk_amount / (sl_distance / price)
        
        # 레버리지 적용된 최대 포지션 크기 제한
        max_position = leveraged_capital
        position_size_usdt = min(position_size_usdt, max_position)
        
        # BTC 수량으로 변환
        position_size_btc = position_size_usdt / price
        
        return round(position_size_btc, 6)
    
    def _calculate_tp_sl(self, entry_price: float, signal: str, atr: float) -> Tuple[float, float]:
        """Take Profit과 Stop Loss 가격 계산"""
        # ATR 기반 거리
        atr_distance = atr * 2
        
        if signal in ['LONG', 'STRONG_LONG']:
            # 롱 포지션
            tp_price = entry_price + (atr_distance * 3)  # TP: 3 ATR
            sl_price = entry_price - atr_distance  # SL: 2 ATR
            
            # 최소/최대 비율 제한
            tp_ratio = (tp_price - entry_price) / entry_price
            sl_ratio = (entry_price - sl_price) / entry_price
            
            if tp_ratio < 0.01:  # 최소 1% 수익
                tp_price = entry_price * 1.01
            if sl_ratio < 0.005:  # 최소 0.5% 손실
                sl_price = entry_price * 0.995
            
        elif signal in ['SHORT', 'STRONG_SHORT']:
            # 숏 포지션
            tp_price = entry_price - (atr_distance * 3)  # TP: 3 ATR
            sl_price = entry_price + atr_distance  # SL: 2 ATR
            
            # 최소/최대 비율 제한
            tp_ratio = (entry_price - tp_price) / entry_price
            sl_ratio = (sl_price - entry_price) / entry_price
            
            if tp_ratio < 0.01:  # 최소 1% 수익
                tp_price = entry_price * 0.99
            if sl_ratio < 0.005:  # 최소 0.5% 손실
                sl_price = entry_price * 1.005
        else:
            # HOLD 신호
            tp_price = entry_price
            sl_price = entry_price
        
        return round(tp_price, 2), round(sl_price, 2)
    
    def should_close_position(self, current_price: float, entry_price: float,
                             position_side: str, signals: Dict) -> bool:
        """포지션 청산 여부 결정"""
        # 추세 반전 확인
        if position_side == 'LONG':
            if signals['trend'] == 'BEARISH_CROSS' or signals['trend'] == 'BEARISH':
                if signals['momentum'] == 'SELL' or signals['momentum'] == 'STRONG_SELL':
                    return True
        elif position_side == 'SHORT':
            if signals['trend'] == 'BULLISH_CROSS' or signals['trend'] == 'BULLISH':
                if signals['momentum'] == 'BUY' or signals['momentum'] == 'STRONG_BUY':
                    return True
        
        return False

