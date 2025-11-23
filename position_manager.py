"""
포지션 관리 모듈
"""
from typing import Dict, Optional, List
from binance_client import BinanceFuturesClient
import time
from logger import logger


class PositionManager:
    """포지션 관리 클래스"""
    
    def __init__(self, client: BinanceFuturesClient):
        self.client = client
        self.symbol = client.symbol
    
    def get_current_position(self) -> Optional[Dict]:
        """현재 포지션 정보 가져오기"""
        positions = self.client.get_open_positions()
        if positions:
            return positions[0]
        return None
    
    def should_open_position(self, analysis: Dict, current_position: Optional[Dict]) -> bool:
        """포지션 오픈 여부 결정"""
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
        
        return True
    
    def should_close_position(self, analysis: Dict, current_position: Optional[Dict]) -> bool:
        """포지션 청산 여부 결정"""
        if not current_position:
            return False
        
        signal = analysis['signal']
        position_side = current_position['side']
        
        # 반대 신호가 나오면 청산
        if position_side == 'LONG' and signal in ['SHORT', 'STRONG_SHORT']:
            return True
        elif position_side == 'SHORT' and signal in ['LONG', 'STRONG_LONG']:
            return True
        
        # HOLD 신호이고 추세 반전이면 청산
        if signal == 'HOLD':
            signals = analysis['signals']
            if position_side == 'LONG':
                if signals['trend'] in ['BEARISH', 'BEARISH_CROSS']:
                    if signals['momentum'] in ['SELL', 'STRONG_SELL']:
                        return True
            elif position_side == 'SHORT':
                if signals['trend'] in ['BULLISH', 'BULLISH_CROSS']:
                    if signals['momentum'] in ['BUY', 'STRONG_BUY']:
                        return True
        
        return False
    
    def execute_trade(self, analysis: Dict) -> bool:
        """거래 실행"""
        current_position = self.get_current_position()
        
        # 포지션 청산 확인
        if self.should_close_position(analysis, current_position):
            logger.info("🔄 포지션 청산 신호 감지")
            self.client.close_position()
            time.sleep(1)  # API 호출 간격
            current_position = None
        
        # 새 포지션 오픈 확인
        if self.should_open_position(analysis, current_position):
            signal = analysis['signal']
            position_size = analysis['position_size']
            entry_price = analysis['entry_price']
            tp_price = analysis['take_profit']
            sl_price = analysis['stop_loss']
            
            if signal in ['LONG', 'STRONG_LONG']:
                side = 'BUY'
            elif signal in ['SHORT', 'STRONG_SHORT']:
                side = 'SELL'
            else:
                return False
            
            logger.info(f"📈 포지션 오픈: {side} {position_size} {self.symbol}")
            logger.info(f"   진입가: ${entry_price:,.2f}")
            logger.info(f"   Take Profit: ${tp_price:,.2f}")
            logger.info(f"   Stop Loss: ${sl_price:,.2f}")
            
            # 주문 실행
            order = self.client.place_order(
                side=side,
                quantity=position_size,
                order_type='MARKET',
                take_profit=tp_price,
                stop_price=sl_price
            )
            
            return order is not None
        
        return False
    
    def update_tp_sl(self, analysis: Dict, current_position: Optional[Dict]) -> bool:
        """TP/SL 업데이트 (트레일링 스탑)"""
        if not current_position:
            return False
        
        # 간단한 트레일링 스탑 로직
        # 실제로는 더 복잡한 로직이 필요할 수 있음
        entry_price = current_position['entry_price']
        mark_price = current_position['mark_price']
        position_side = current_position['side']
        
        # 수익이 발생한 경우에만 TP/SL 업데이트 고려
        unrealized_pnl = current_position['unrealized_pnl']
        if unrealized_pnl > 0:
            # 수익이 2% 이상이면 TP를 현재가 근처로 이동
            profit_ratio = unrealized_pnl / (entry_price * abs(current_position['position_amt']))
            if profit_ratio > 0.02:
                # 여기서는 간단히 표시만 함
                # 실제 구현 시에는 주문 취소 후 재설정 필요
                pass
        
        return False
    
    def get_position_summary(self) -> Dict:
        """포지션 요약 정보"""
        position = self.get_current_position()
        balance = self.client.get_account_balance()
        
        if position:
            entry_price = position['entry_price']
            mark_price = position['mark_price']
            pnl = position['unrealized_pnl']
            pnl_percent = (pnl / (entry_price * abs(position['position_amt']))) * 100
            
            return {
                'has_position': True,
                'side': position['side'],
                'size': abs(position['position_amt']),
                'entry_price': entry_price,
                'mark_price': mark_price,
                'unrealized_pnl': pnl,
                'pnl_percent': pnl_percent,
                'total_balance': balance['total_balance'],
                'available_balance': balance['available_balance']
            }
        else:
            return {
                'has_position': False,
                'total_balance': balance['total_balance'],
                'available_balance': balance['available_balance']
            }

