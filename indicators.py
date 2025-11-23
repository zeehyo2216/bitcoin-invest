"""
기술적 지표 계산 모듈
"""
import pandas as pd
import numpy as np
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
# VolumeSMAIndicator는 ta 라이브러리에 없으므로 pandas로 직접 계산


class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._calculate_all()
    
    def _calculate_all(self):
        """모든 지표 계산"""
        # 추세 지표
        self._calculate_macd()
        self._calculate_ema()
        self._calculate_sma()
        
        # 모멘텀 지표
        self._calculate_rsi()
        self._calculate_stochastic()
        
        # 변동성 지표
        self._calculate_bollinger_bands()
        self._calculate_atr()
        
        # 거래량 지표
        self._calculate_volume_sma()
    
    def _calculate_macd(self):
        """MACD 지표 계산"""
        macd = MACD(close=self.df['close'])
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_diff'] = macd.macd_diff()
    
    def _calculate_ema(self):
        """EMA 지표 계산"""
        self.df['ema_9'] = EMAIndicator(close=self.df['close'], window=9).ema_indicator()
        self.df['ema_21'] = EMAIndicator(close=self.df['close'], window=21).ema_indicator()
        self.df['ema_50'] = EMAIndicator(close=self.df['close'], window=50).ema_indicator()
        self.df['ema_200'] = EMAIndicator(close=self.df['close'], window=200).ema_indicator()
    
    def _calculate_sma(self):
        """SMA 지표 계산"""
        self.df['sma_20'] = SMAIndicator(close=self.df['close'], window=20).sma_indicator()
        self.df['sma_50'] = SMAIndicator(close=self.df['close'], window=50).sma_indicator()
    
    def _calculate_rsi(self):
        """RSI 지표 계산"""
        rsi = RSIIndicator(close=self.df['close'], window=14)
        self.df['rsi'] = rsi.rsi()
    
    def _calculate_stochastic(self):
        """Stochastic Oscillator 계산"""
        stoch = StochasticOscillator(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=14
        )
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()
    
    def _calculate_bollinger_bands(self):
        """볼린저 밴드 계산"""
        bb = BollingerBands(close=self.df['close'], window=20, window_dev=2)
        self.df['bb_upper'] = bb.bollinger_hband()
        self.df['bb_middle'] = bb.bollinger_mavg()
        self.df['bb_lower'] = bb.bollinger_lband()
        self.df['bb_width'] = (self.df['bb_upper'] - self.df['bb_lower']) / self.df['bb_middle']
    
    def _calculate_atr(self):
        """ATR (Average True Range) 계산"""
        atr = AverageTrueRange(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=14
        )
        self.df['atr'] = atr.average_true_range()
    
    def _calculate_volume_sma(self):
        """거래량 SMA 계산"""
        self.df['volume_sma'] = self.df['volume'].rolling(window=20).mean()
    
    def get_latest_signals(self) -> dict:
        """최신 신호 반환"""
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        signals = {
            'price': latest['close'],
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'macd_signal': latest['macd_signal'],
            'macd_diff': latest['macd_diff'],
            'ema_9': latest['ema_9'],
            'ema_21': latest['ema_21'],
            'ema_50': latest['ema_50'],
            'bb_upper': latest['bb_upper'],
            'bb_lower': latest['bb_lower'],
            'bb_middle': latest['bb_middle'],
            'atr': latest['atr'],
            'stoch_k': latest['stoch_k'],
            'stoch_d': latest['stoch_d'],
            'volume_ratio': latest['volume'] / latest['volume_sma'] if latest['volume_sma'] > 0 else 1.0,
        }
        
        # 신호 생성
        signals['trend'] = self._get_trend_signal(latest, prev)
        signals['momentum'] = self._get_momentum_signal(latest, prev)
        signals['volatility'] = self._get_volatility_signal(latest)
        
        return signals
    
    def _get_trend_signal(self, latest: pd.Series, prev: pd.Series) -> str:
        """추세 신호"""
        # EMA 크로스오버
        if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
            if prev['ema_9'] <= prev['ema_21']:
                return 'BULLISH_CROSS'
            return 'BULLISH'
        elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
            if prev['ema_9'] >= prev['ema_21']:
                return 'BEARISH_CROSS'
            return 'BEARISH'
        return 'NEUTRAL'
    
    def _get_momentum_signal(self, latest: pd.Series, prev: pd.Series) -> str:
        """모멘텀 신호"""
        # MACD 크로스오버
        macd_bullish = latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']
        macd_bearish = latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']
        
        # RSI 조건
        rsi_oversold = latest['rsi'] < 30
        rsi_overbought = latest['rsi'] > 70
        
        if macd_bullish and rsi_oversold:
            return 'STRONG_BUY'
        elif macd_bullish:
            return 'BUY'
        elif macd_bearish and rsi_overbought:
            return 'STRONG_SELL'
        elif macd_bearish:
            return 'SELL'
        return 'NEUTRAL'
    
    def _get_volatility_signal(self, latest: pd.Series) -> str:
        """변동성 신호"""
        # 볼린저 밴드 위치
        if latest['close'] < latest['bb_lower']:
            return 'OVERSOLD'
        elif latest['close'] > latest['bb_upper']:
            return 'OVERBOUGHT'
        return 'NORMAL'
    
    def get_dataframe(self) -> pd.DataFrame:
        """계산된 데이터프레임 반환"""
        return self.df

