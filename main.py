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
from logger import logger

# Colorama 초기화
init(autoreset=True)

load_dotenv()


class TradingBot:
    """메인 트레이딩 봇 클래스"""
    
    def __init__(self):
        log_msg = "=" * 60 + "\n🚀 바이낸스 선물 거래 봇 시작\n" + "=" * 60
        print(Fore.CYAN + log_msg)
        logger.info(log_msg)
        
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
        
        init_msg = f"✅ 초기화 완료\n   심볼: {self.client.symbol}\n   레버리지: {self.leverage}x\n   초기 자본: ${self.initial_balance:,.2f} USDT\n   데이터 간격: {self.interval}"
        print(Fore.GREEN + init_msg)
        logger.info(init_msg)
        print()
    
    def run_analysis(self):
        """분석 및 거래 실행"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            header = f"\n{'='*60}\n📊 {timestamp} - 시장 분석 시작\n{'='*60}"
            print(Fore.CYAN + header)
            logger.info(header)
            
            # 1. 데이터 수집
            print(Fore.YELLOW + "📥 데이터 수집 중...")
            logger.info("📥 데이터 수집 중...")
            df = self.client.get_klines(interval=self.interval, limit=200)
            
            if df.empty:
                error_msg = "❌ 데이터를 가져올 수 없습니다."
                print(Fore.RED + error_msg)
                logger.error(error_msg)
                return
            
            current_price = self.client.get_current_price()
            price_msg = f"✅ 현재 가격: ${current_price:,.2f}"
            print(Fore.GREEN + price_msg)
            logger.info(price_msg)
            
            # 2. 기술적 지표 계산
            print(Fore.YELLOW + "📈 기술적 지표 계산 중...")
            logger.info("📈 기술적 지표 계산 중...")
            indicators = TechnicalIndicators(df)
            signals = indicators.get_latest_signals()
            
            # 지표 출력
            indicators_msg = (
                f"\n📊 주요 지표:\n"
                f"   RSI: {signals['rsi']:.2f}\n"
                f"   MACD: {signals['macd']:.4f} (Signal: {signals['macd_signal']:.4f})\n"
                f"   추세: {signals['trend']}\n"
                f"   모멘텀: {signals['momentum']}\n"
                f"   변동성: {signals['volatility']}\n"
                f"   거래량 비율: {signals['volume_ratio']:.2f}x"
            )
            print(Fore.CYAN + indicators_msg)
            logger.info(indicators_msg)
            
            # 3. 전략 분석
            print(Fore.YELLOW + "\n🧠 전략 분석 중...")
            logger.info("🧠 전략 분석 중...")
            analysis = self.strategy.analyze(indicators)
            
            signal_color = Fore.GREEN if analysis['signal'] in ['LONG', 'STRONG_LONG'] else Fore.RED if analysis['signal'] in ['SHORT', 'STRONG_SHORT'] else Fore.YELLOW
            analysis_msg = (
                f"\n🎯 분석 결과:\n"
                f"   신호: {analysis['signal']}\n"
                f"   점수: {analysis['score']:.2f}/10.0\n"
                f"   신뢰도: {analysis['confidence']*100:.1f}%"
            )
            print(Fore.CYAN + "\n🎯 분석 결과:")
            print(f"   신호: {signal_color}{analysis['signal']}")
            print(f"   점수: {analysis['score']:.2f}/10.0")
            print(f"   신뢰도: {analysis['confidence']*100:.1f}%")
            logger.info(analysis_msg)
            
            if analysis['signal'] != 'HOLD':
                signal_detail = (
                    f"   포지션 크기: {analysis['position_size']:.6f} {self.client.symbol.replace('USDT', '')}\n"
                    f"   진입가: ${analysis['entry_price']:,.2f}\n"
                    f"   Take Profit: ${analysis['take_profit']:,.2f} ({((analysis['take_profit'] - analysis['entry_price']) / analysis['entry_price'] * 100):.2f}%)\n"
                    f"   Stop Loss: ${analysis['stop_loss']:,.2f} ({((analysis['stop_loss'] - analysis['entry_price']) / analysis['entry_price'] * 100):.2f}%)"
                )
                print(signal_detail)
                logger.info(signal_detail)
            
            # 4. 현재 포지션 상태
            print(Fore.CYAN + "\n💼 포지션 상태:")
            logger.info("\n💼 포지션 상태:")
            position_summary = self.position_manager.get_position_summary()
            
            if position_summary['has_position']:
                position_msg = (
                    f"   포지션: {position_summary['side']}\n"
                    f"   크기: {position_summary['size']:.6f} {self.client.symbol.replace('USDT', '')}\n"
                    f"   진입가: ${position_summary['entry_price']:,.2f}\n"
                    f"   현재가: ${position_summary['mark_price']:,.2f}\n"
                    f"   미실현 손익: ${position_summary['unrealized_pnl']:,.2f} ({position_summary['pnl_percent']:.2f}%)"
                )
                pnl_color = Fore.GREEN if position_summary['unrealized_pnl'] >= 0 else Fore.RED
                print(f"   포지션: {Fore.GREEN if position_summary['side'] == 'LONG' else Fore.RED}{position_summary['side']}")
                print(f"   크기: {position_summary['size']:.6f} {self.client.symbol.replace('USDT', '')}")
                print(f"   진입가: ${position_summary['entry_price']:,.2f}")
                print(f"   현재가: ${position_summary['mark_price']:,.2f}")
                print(f"   미실현 손익: {pnl_color}${position_summary['unrealized_pnl']:,.2f} ({position_summary['pnl_percent']:.2f}%)")
                logger.info(position_msg)
            else:
                print(Fore.YELLOW + "   포지션 없음")
                logger.info("   포지션 없음")
            
            balance_msg = (
                f"   총 잔액: ${position_summary['total_balance']:,.2f} USDT\n"
                f"   사용 가능: ${position_summary['available_balance']:,.2f} USDT"
            )
            print(balance_msg)
            logger.info(balance_msg)
            
            # 5. 거래 실행
            print(Fore.YELLOW + "\n⚙️ 거래 실행 검토 중...")
            logger.info("⚙️ 거래 실행 검토 중...")
            executed = self.position_manager.execute_trade(analysis)
            
            if executed:
                success_msg = "✅ 거래가 실행되었습니다."
                print(Fore.GREEN + success_msg)
                logger.info(success_msg)
            else:
                skip_msg = "ℹ️ 거래 조건을 만족하지 않아 실행하지 않았습니다."
                print(Fore.YELLOW + skip_msg)
                logger.info(skip_msg)
            
            footer = f"\n{'='*60}\n"
            print(Fore.CYAN + footer)
            logger.info(footer)
            
        except Exception as e:
            error_msg = f"❌ 오류 발생: {e}"
            print(Fore.RED + error_msg)
            logger.error(error_msg, exc_info=True)
    
    def start(self):
        """봇 시작"""
        start_msg = f"\n✅ 봇이 시작되었습니다. {self.interval} 간격으로 분석을 실행합니다."
        print(Fore.GREEN + start_msg)
        logger.info(start_msg)
        warning_msg = "⚠️ 종료하려면 Ctrl+C를 누르세요."
        print(Fore.YELLOW + warning_msg + "\n")
        logger.info(warning_msg)
        
        # 즉시 한 번 실행
        self.run_analysis()
        
        # 스케줄 설정
        schedule.every(5).minutes.do(self.run_analysis)
        
        # 메인 루프
        try:
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    # 스케줄 실행 중 오류 발생 시 로그만 기록하고 계속 실행
                    error_msg = f"⚠️ 스케줄 실행 중 오류 발생: {e}"
                    logger.error(error_msg, exc_info=True)
                    time.sleep(5)  # 잠시 대기 후 재시도
        except KeyboardInterrupt:
            shutdown_msg = "\n\n⚠️ 봇이 종료되었습니다."
            print(Fore.YELLOW + shutdown_msg)
            logger.info(shutdown_msg)
        except Exception as e:
            # 예상치 못한 오류 발생 시
            error_msg = f"❌ 치명적 오류 발생: {e}"
            logger.critical(error_msg, exc_info=True)
            raise


def main():
    """메인 함수"""
    try:
        bot = TradingBot()
        bot.start()
    except Exception as e:
        error_msg = f"❌ 초기화 오류: {e}"
        print(Fore.RED + error_msg)
        logger.error(error_msg, exc_info=True)


if __name__ == "__main__":
    main()

