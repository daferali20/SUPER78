# core/monitoring.py
import time
import threading
import pandas as pd
from typing import Callable
from ib_insync import *
from config import config
from utils.logger import Logger
from utils.indicators import TechnicalIndicators
from trading.stocks import StockTrader
from trading.options import OptionTrader

class MarketMonitor:
    def __init__(self, trader):
        self.trader = trader
        self.ib = trader.ib
        self.logger = Logger()
        self.indicators = TechnicalIndicators()
        self.stock_trader = StockTrader(trader)
        self.option_trader = OptionTrader(trader)
        self.running = False
        self.watchlist = []
        self.bar_size = '15 mins'
        self.duration = '2 D'

    def start_monitoring(self, log_func: Callable):
        """بدء عملية مراقبة السوق"""
        if not self._connect_ibkr():
            log_func("⚠️ فشل بدء المراقبة - لا يوجد اتصال")
            return False

        self.running = True
        self.watchlist = self._load_watchlist()
        
        # بدء خيوط المراقبة
        threading.Thread(
            target=self._monitor_watchlist,
            args=(log_func,),
            daemon=True
        ).start()

        threading.Thread(
            target=self._monitor_open_trades,
            args=(log_func,),
            daemon=True
        ).start()

        log_func("🚀 بدء مراقبة السوق والصفقات...")
        return True

    def stop_monitoring(self):
        """إيقاف عملية المراقبة"""
        self.running = False

    def _connect_ibkr(self) -> bool:
        """إجراء اتصال بـ IBKR"""
        try:
            if not self.ib.isConnected():
                self.ib.connect('127.0.0.1', 7497, clientId=1, timeout=15)
            return True
        except Exception as e:
            self.logger.error(f"فشل الاتصال بـ IBKR: {e}")
            return False

    def _load_watchlist(self) -> list:
        """تحميل قائمة المتابعة من الملف"""
        try:
            with open(config.watchlist_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.logger.error(f"خطأ في تحميل قائمة المتابعة: {e}")
            return ['SPX']  # القيمة الافتراضية

    def _monitor_watchlist(self, log_func: Callable):
        """مراقبة أدوات قائمة المتابعة"""
        while self.running:
            try:
                for symbol in self.watchlist:
                    if not self.running:
                        break

                    contract = self._create_contract(symbol)
                    if not contract:
                        continue

                    bars = self._get_historical_data(contract)
                    if bars is None:
                        continue

                    df = util.df(bars)
                    self._analyze_symbol(symbol, df, log_func)

                time.sleep(60)  # فحص كل دقيقة

            except Exception as e:
                self.logger.error(f"خطأ في مراقبة القائمة: {e}")
                time.sleep(30)

    def _create_contract(self, symbol: str):
        """إنشاء عقد التداول المناسب"""
        try:
            if symbol == 'SPX':
                contract = Index(symbol, 'CBOE')
            else:
                contract = Stock(symbol, 'SMART', 'USD')
            
            self.ib.qualifyContracts(contract)
            return contract
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء عقد لـ {symbol}: {e}")
            return None

    def _get_historical_data(self, contract) -> Optional[pd.DataFrame]:
        """الحصول على البيانات التاريخية"""
        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=self.duration,
                barSizeSetting=self.bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            return bars
        except Exception as e:
            self.logger.error(f"خطأ في جلب البيانات: {e}")
            return None

    def _analyze_symbol(self, symbol: str, df: pd.DataFrame, log_func: Callable):
        """تحليل البيانات وإرسال إشارات التداول"""
        try:
            signal = self.indicators.identify_reversal_candles(df)
            if not signal:
                return

            price = df['close'].iloc[-1]
            log_func(f"📊 [{symbol}] إشارة {signal} عند السعر {price:.2f}")

            if symbol == 'SPX':
                self.option_trader.place_order(
                    signal.split('_')[1].upper(),
                    price,
                    log_func
                )
            else:
                self.stock_trader.place_order(
                    symbol,
                    signal.split('_')[1].upper(),
                    price,
                    log_func
                )

        except Exception as e:
            self.logger.error(f"خطأ في تحليل {symbol}: {e}")

    def _monitor_open_trades(self, log_func: Callable):
        """مراقبة الصفقات المفتوحة وتنفيذ TP/SL"""
        while self.running and self.trader.current_trades:
            try:
                for trade_id, trade_info in list(self.trader.current_trades.items()):
                    if not self.running:
                        break

                    if trade_info['status'] != 'open':
                        continue

                    self._check_trade_conditions(trade_id, trade_info, log_func)

                time.sleep(10)  # فحص كل 10 ثواني

            except Exception as e:
                self.logger.error(f"خطأ في متابعة الصفقات: {e}")
                time.sleep(30)

    def _check_trade_conditions(self, trade_id: str, trade_info: dict, log_func: Callable):
        """فحص شروط إغلاق الصفقة"""
        try:
            ticker = self.ib.reqMktData(trade_info['contract'], '', False, False)
            self.ib.sleep(1)
            
            if not hasattr(ticker, 'last') or ticker.last != ticker.last:
                return

            current_price = ticker.last
            self._process_tp_sl(trade_id, trade_info, current_price, log_func)

        except Exception as e:
            self.logger.error(f"خطأ في فحص الصفقة {trade_id}: {e}")

    def _process_tp_sl(self, trade_id: str, trade_info: dict, current_price: float, log_func: Callable):
        """معالجة أوامر جني الربح ووقف الخسارة"""
        try:
            if current_price >= trade_info['target']:
                self._close_trade(trade_id, trade_info, current_price, 'TP', log_func)
            elif current_price <= trade_info['stop']:
                self._close_trade(trade_id, trade_info, current_price, 'SL', log_func)

        except Exception as e:
            self.logger.error(f"خطأ في معالجة TP/SL: {e}")

    def _close_trade(self, trade_id: str, trade_info: dict, price: float, reason: str, log_func: Callable):
        """إغلاق الصفقة"""
        try:
            close_order = MarketOrder('SELL', trade_info['quantity'])
            self.ib.placeOrder(trade_info['contract'], close_order)
            
            trade_info.update({
                'status': 'closed',
                'exit_price': price,
                'exit_time': pd.Timestamp.now()
            })

            log_func(f"✅ {reason} تم تنفيذ {trade_id} عند السعر {price:.2f}")
            self._update_trade_in_db(trade_id, trade_info)

        except Exception as e:
            self.logger.error(f"خطأ في إغلاق الصفقة: {e}")

    def _update_trade_in_db(self, trade_id: str, trade_info: dict):
        """تحديث سجل الصفقات"""
        # سيتم تنفيذ هذه الوظيفة في ملف إدارة البيانات
        pass
