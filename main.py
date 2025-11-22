"""
바이낸스 선물 거래 봇 - 메인 실행 스크립트
"""
import os
import time
import schedule
from datetime import datetime
from colorama import init, Fore, Style
from dotenv import load_dotenv

from binance_client import BinanceFuturesClient
from indicators import TechnicalIndicators
from strategy import TradingStrategy
from position_manager import PositionManager

# Colorama 초기화
init(autoreset=True)

load_dotenv()


class TradingBot:
    """메인 트레이딩 봇 클래스"""
    
    def __init__(self):
        print(Fore.CYAN + "=" * 60)
        print(Fore.CYAN + "🚀 바이낸스 선물 거래 봇 시작")
        print(Fore.CYAN + "=" * 60)
        
        # 클라이언트 초기화
        self.client = BinanceFuturesClient()
        
        # 설정값
        self.initial_balance = float(os.getenv('INITIAL_BALANCE', '600'))
        self.leverage = int(os.getenv('LEVERAGE', '20'))
        self.interval = os.getenv('INTERVAL', '5m')
        
        # 전략 및 매니저 초기화
        self.strategy = TradingStrategy(
            initial_balance=self.initial_balance,
            leverage=self.leverage
        )
        self.position_manager = PositionManager(self.client)
        
        print(Fore.GREEN + f"✅ 초기화 완료")
        print(Fore.YELLOW + f"   심볼: {self.client.symbol}")
        print(Fore.YELLOW + f"   레버리지: {self.leverage}x")
        print(Fore.YELLOW + f"   초기 자본: ${self.initial_balance:,.2f} USDT")
        print(Fore.YELLOW + f"   데이터 간격: {self.interval}")
        print()
    
    def run_analysis(self):
        """분석 및 거래 실행"""
        try:
            print(Fore.CYAN + f"\n{'='*60}")
            print(Fore.CYAN + f"📊 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 시장 분석 시작")
            print(Fore.CYAN + f"{'='*60}")
            
            # 1. 데이터 수집
            print(Fore.YELLOW + "📥 데이터 수집 중...")
            df = self.client.get_klines(interval=self.interval, limit=200)
            
            if df.empty:
                print(Fore.RED + "❌ 데이터를 가져올 수 없습니다.")
                return
            
            current_price = self.client.get_current_price()
            print(Fore.GREEN + f"✅ 현재 가격: ${current_price:,.2f}")
            
            # 2. 기술적 지표 계산
            print(Fore.YELLOW + "📈 기술적 지표 계산 중...")
            indicators = TechnicalIndicators(df)
            signals = indicators.get_latest_signals()
            
            # 지표 출력
            print(Fore.CYAN + "\n📊 주요 지표:")
            print(f"   RSI: {signals['rsi']:.2f}")
            print(f"   MACD: {signals['macd']:.4f} (Signal: {signals['macd_signal']:.4f})")
            print(f"   추세: {signals['trend']}")
            print(f"   모멘텀: {signals['momentum']}")
            print(f"   변동성: {signals['volatility']}")
            print(f"   거래량 비율: {signals['volume_ratio']:.2f}x")
            
            # 3. 전략 분석
            print(Fore.YELLOW + "\n🧠 전략 분석 중...")
            analysis = self.strategy.analyze(indicators)
            
            print(Fore.CYAN + "\n🎯 분석 결과:")
            print(f"   신호: {Fore.GREEN if analysis['signal'] in ['LONG', 'STRONG_LONG'] else Fore.RED if analysis['signal'] in ['SHORT', 'STRONG_SHORT'] else Fore.YELLOW}{analysis['signal']}")
            print(f"   점수: {analysis['score']:.2f}/10.0")
            print(f"   신뢰도: {analysis['confidence']*100:.1f}%")
            
            if analysis['signal'] != 'HOLD':
                print(f"   포지션 크기: {analysis['position_size']:.6f} {self.client.symbol.replace('USDT', '')}")
                print(f"   진입가: ${analysis['entry_price']:,.2f}")
                print(f"   Take Profit: ${analysis['take_profit']:,.2f} ({((analysis['take_profit'] - analysis['entry_price']) / analysis['entry_price'] * 100):.2f}%)")
                print(f"   Stop Loss: ${analysis['stop_loss']:,.2f} ({((analysis['stop_loss'] - analysis['entry_price']) / analysis['entry_price'] * 100):.2f}%)")
            
            # 4. 현재 포지션 상태
            print(Fore.CYAN + "\n💼 포지션 상태:")
            position_summary = self.position_manager.get_position_summary()
            
            if position_summary['has_position']:
                pnl_color = Fore.GREEN if position_summary['unrealized_pnl'] >= 0 else Fore.RED
                print(f"   포지션: {Fore.GREEN if position_summary['side'] == 'LONG' else Fore.RED}{position_summary['side']}")
                print(f"   크기: {position_summary['size']:.6f} {self.client.symbol.replace('USDT', '')}")
                print(f"   진입가: ${position_summary['entry_price']:,.2f}")
                print(f"   현재가: ${position_summary['mark_price']:,.2f}")
                print(f"   미실현 손익: {pnl_color}${position_summary['unrealized_pnl']:,.2f} ({position_summary['pnl_percent']:.2f}%)")
            else:
                print(Fore.YELLOW + "   포지션 없음")
            
            print(f"   총 잔액: ${position_summary['total_balance']:,.2f} USDT")
            print(f"   사용 가능: ${position_summary['available_balance']:,.2f} USDT")
            
            # 5. 거래 실행
            print(Fore.YELLOW + "\n⚙️ 거래 실행 검토 중...")
            executed = self.position_manager.execute_trade(analysis)
            
            if executed:
                print(Fore.GREEN + "✅ 거래가 실행되었습니다.")
            else:
                print(Fore.YELLOW + "ℹ️ 거래 조건을 만족하지 않아 실행하지 않았습니다.")
            
            print(Fore.CYAN + f"\n{'='*60}\n")
            
        except Exception as e:
            print(Fore.RED + f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """봇 시작"""
        print(Fore.GREEN + f"\n✅ 봇이 시작되었습니다. {self.interval} 간격으로 분석을 실행합니다.")
        print(Fore.YELLOW + "⚠️ 종료하려면 Ctrl+C를 누르세요.\n")
        
        # 즉시 한 번 실행
        self.run_analysis()
        
        # 스케줄 설정
        schedule.every(5).minutes.do(self.run_analysis)
        
        # 메인 루프
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n⚠️ 봇이 종료되었습니다.")


def main():
    """메인 함수"""
    try:
        bot = TradingBot()
        bot.start()
    except Exception as e:
        print(Fore.RED + f"❌ 초기화 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

