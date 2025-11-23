"""
바이낸스 선물 거래 API 클라이언트
"""
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import pandas as pd
from typing import Optional, Dict, List
from logger import logger

load_dotenv()


class BinanceFuturesClient:
    def __init__(self):
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        testnet = os.getenv('TESTNET', 'False').lower() == 'true'
        
        if not api_key or not api_secret:
            raise ValueError("BINANCE_API_KEY와 BINANCE_API_SECRET을 .env 파일에 설정해주세요.")
        
        if testnet:
            self.client = Client(api_key, api_secret, testnet=True)
        else:
            self.client = Client(api_key, api_secret)
        
        self.symbol = os.getenv('SYMBOL', 'BTCUSDT')
        self.leverage = int(os.getenv('LEVERAGE', '20'))
        
        # 레버리지 설정
        self._set_leverage()
    
    def _set_leverage(self):
        """레버리지 설정"""
        try:
            self.client.futures_change_leverage(
                symbol=self.symbol,
                leverage=self.leverage
            )
            logger.info(f"✅ 레버리지 {self.leverage}x 설정 완료")
        except BinanceAPIException as e:
            logger.warning(f"⚠️ 레버리지 설정 오류: {e}")
    
    def get_klines(self, interval: str = '5m', limit: int = 200) -> pd.DataFrame:
        """캔들스틱 데이터 가져오기"""
        try:
            klines = self.client.futures_klines(
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # 데이터 타입 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except BinanceAPIException as e:
            logger.error(f"❌ 데이터 가져오기 오류: {e}")
            return pd.DataFrame()
    
    def get_current_price(self) -> float:
        """현재 가격 가져오기"""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"❌ 현재 가격 가져오기 오류: {e}")
            return 0.0
    
    def get_account_balance(self) -> Dict:
        """계정 잔액 정보 가져오기"""
        try:
            account = self.client.futures_account()
            balance = float(account['totalWalletBalance'])
            available = float(account['availableBalance'])
            unrealized_pnl = float(account['totalUnrealizedProfit'])
            
            return {
                'total_balance': balance,
                'available_balance': available,
                'unrealized_pnl': unrealized_pnl
            }
        except BinanceAPIException as e:
            logger.error(f"❌ 계정 정보 가져오기 오류: {e}")
            return {'total_balance': 0, 'available_balance': 0, 'unrealized_pnl': 0}
    
    def get_open_positions(self) -> List[Dict]:
        """열린 포지션 가져오기"""
        try:
            positions = self.client.futures_position_information(symbol=self.symbol)
            open_positions = []
            
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    open_positions.append({
                        'symbol': pos['symbol'],
                        'position_amt': position_amt,
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'unrealized_pnl': float(pos['unRealizedProfit']),
                        'leverage': int(pos['leverage']),
                        'side': 'LONG' if position_amt > 0 else 'SHORT'
                    })
            
            return open_positions
        except BinanceAPIException as e:
            logger.error(f"❌ 포지션 정보 가져오기 오류: {e}")
            return []
    
    def place_order(self, side: str, quantity: float, price: Optional[float] = None,
                   order_type: str = 'MARKET', stop_price: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Optional[Dict]:
        """주문 실행"""
        try:
            if order_type == 'MARKET':
                order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity
                )
            elif order_type == 'LIMIT':
                if not price:
                    raise ValueError("LIMIT 주문에는 가격이 필요합니다.")
                order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side=side,
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=quantity,
                    price=price
                )
            else:
                raise ValueError(f"지원하지 않는 주문 타입: {order_type}")
            
            logger.info(f"✅ 주문 성공: {side} {quantity} {self.symbol}")
            
            # TP/SL 주문 설정
            if take_profit:
                self._set_take_profit(side, quantity, take_profit)
            
            if stop_price:
                self._set_stop_loss(side, quantity, stop_price)
            
            return order
        except BinanceAPIException as e:
            logger.error(f"❌ 주문 실행 오류: {e}")
            return None
    
    def _set_take_profit(self, side: str, quantity: float, price: float):
        """Take Profit 주문 설정"""
        try:
            tp_side = 'SELL' if side == 'BUY' else 'BUY'
            self.client.futures_create_order(
                symbol=self.symbol,
                side=tp_side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=price,
                closePosition=True
            )
            logger.info(f"✅ Take Profit 설정: {price}")
        except BinanceAPIException as e:
            logger.warning(f"⚠️ Take Profit 설정 오류: {e}")
    
    def _set_stop_loss(self, side: str, quantity: float, price: float):
        """Stop Loss 주문 설정"""
        try:
            sl_side = 'SELL' if side == 'BUY' else 'BUY'
            self.client.futures_create_order(
                symbol=self.symbol,
                side=sl_side,
                type='STOP_MARKET',
                stopPrice=price,
                closePosition=True
            )
            logger.info(f"✅ Stop Loss 설정: {price}")
        except BinanceAPIException as e:
            logger.warning(f"⚠️ Stop Loss 설정 오류: {e}")
    
    def close_position(self, side: str = None):
        """포지션 청산"""
        try:
            positions = self.get_open_positions()
            if not positions:
                logger.warning("⚠️ 청산할 포지션이 없습니다.")
                return
            
            for pos in positions:
                if side and pos['side'] != side:
                    continue
                
                close_side = 'SELL' if pos['side'] == 'LONG' else 'BUY'
                quantity = abs(pos['position_amt'])
                
                self.client.futures_create_order(
                    symbol=self.symbol,
                    side=close_side,
                    type='MARKET',
                    quantity=quantity
                )
                logger.info(f"✅ 포지션 청산 완료: {pos['side']} {quantity}")
        except BinanceAPIException as e:
            logger.error(f"❌ 포지션 청산 오류: {e}")

