# spx_trader/core/trader.py
import os
import time
import threading
import configparser
from datetime import datetime, timedelta
from tkinter import messagebox
from ib_insync import *

# تصحيح الاستيرادات لتكون مطلقة
from spx_trader.trading.stocks import StockTrader
from spx_trader.trading.options import OptionTrader
from spx_trader.utils.logger import Logger
from spx_trader.utils.indicators import TechnicalIndicators
from spx_trader.core.connection import IBConnection
from spx_trader.core.monitoring import TradeMonitor
from spx_trader.config import config as app_config  # <<< مفقود سابقًا وتم تصحيحه


class SPXTrader:
    def __init__(self):
        self.ib = IB()
        self.running = False
        self.current_trades = {}
        self.connection_status = False
        self.logger = Logger()
        self.indicators = TechnicalIndicators()
        self.config = self.load_config()

        self.stock_trader = StockTrader(self)
        self.option_trader = OptionTrader(self)

    def load_config(self):
        default_config = {
            'qty': 1,
            'tp_pct': 5,
            'sl_pct': 3,
            'expiry': self.get_next_friday(),
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'use_rsi': True,
            'use_ma': True,
            'ma_period': 50
        }

        if os.path.exists(app_config.config_file):
            try:
                cfg = configparser.ConfigParser()
                cfg.read(app_config.config_file)
                if 'DEFAULT' in cfg:
                    for key in default_config:
                        if key in cfg['DEFAULT']:
                            value = cfg['DEFAULT'][key]
                            if value.lower() in ['true', 'false']:
                                default_config[key] = value.lower() == 'true'
                            elif value.replace('.', '', 1).isdigit():
                                default_config[key] = float(value) if '.' in value else int(value)
                            else:
                                default_config[key] = value
            except Exception as e:
                messagebox.showerror("\u062e\u0637\u0623", f"\u0641\u0634\u0644 \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a: {e}")

        return default_config

    def save_config(self):
        try:
            cfg = configparser.ConfigParser()
            cfg['DEFAULT'] = {k: str(v) for k, v in self.config.items()}
            with open(app_config.config_file, 'w', encoding='utf-8') as f:
                cfg.write(f)
        except Exception as e:
            messagebox.showerror("\u062e\u0637\u0623", f"\u0641\u0634\u0644 \u062d\u0641\u0638 \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a: {e}")

    def get_next_friday(self):
        today = datetime.today()
        days_ahead = (4 - today.weekday()) % 7
        next_friday = today + timedelta(days=days_ahead)
        return next_friday.strftime('%Y%m%d')

    def analyze_market_data(self, prices_df):
        try:
            rsi_values = self.indicators.calculate_rsi(prices_df['close'])
            signal = self.indicators.identify_reversal_candles(prices_df)
            if signal == 'reversal_up':
                self.execute_option_trade('CALL', prices_df['close'].iloc[-1], self.logger.info)
            elif signal == 'reversal_down':
                self.execute_option_trade('PUT', prices_df['close'].iloc[-1], self.logger.info)
            return signal
        except Exception as e:
            self.logger.error(f"\u062e\u0637\u0623 \u0641\u064a \u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a: {e}")
            return None

    def execute_option_trade(self, option_type, price, log_func):
        return self.option_trader.place_order(option_type, price, log_func)

    def execute_stock_trade(self, symbol, action, price, log_func):
        return self.stock_trader.place_order(symbol, action, price, log_func)

    def connect_ibkr(self):
        try:
            if not self.ib.isConnected():
                self.ib.connect('127.0.0.1', 7497, clientId=1, timeout=15)
                self.connection_status = True
                return True
        except Exception as e:
            self.logger.error(f"\u0641\u0634\u0644 \u0627\u0644\u0627\u062a\u0635\u0627\u0644 \u0628\u0640 IBKR: {e}")
            return False

    def disconnect_ibkr(self):
        try:
            if self.ib.isConnected():
                self.ib.disconnect()
                self.connection_status = False
        except Exception as e:
            self.logger.error(f"\u062e\u0637\u0623 \u0623\u062b\u0646\u0627\u0621 \u0642\u0637\u0639 \u0627\u0644\u0627\u062a\u0635\u0627\u0644: {e}")

    def start_trading(self):
        if not self.connect_ibkr():
            return False
        self.running = True
        self._start_monitoring_threads()
        return True

    def stop_trading(self):
        self.running = False
        self.disconnect_ibkr()

    def _start_monitoring_threads(self):
        threading.Thread(target=self._monitor_watchlist, daemon=True).start()
        threading.Thread(target=self._monitor_open_trades, daemon=True).start()

    def _monitor_watchlist(self):
        while self.running:
            try:
                time.sleep(60)
            except Exception as e:
                self.logger.error(f"\u062e\u0637\u0623 \u0641\u064a \u0645\u0631\u0627\u0642\u0628\u0629 \u0627\u0644\u0642\u0627\u0626\u0645\u0629: {e}")

    def _monitor_open_trades(self):
        while self.running and self.current_trades:
            try:
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"\u062e\u0637\u0623 \u0641\u064a \u0645\u062a\u0627\u0628\u0639\u0629 \u0627\u0644\u0635\u0641\u0642\u0627\u062a: {e}")

    def get_account_balance(self):
        try:
            if self.ib.isConnected():
                account = self.ib.accountSummary()
                return {item.tag: item.value for item in account}
            return {}
        except Exception as e:
            self.logger.error(f"\u062e\u0637\u0623 \u0641\u064a \u0627\u0644\u0631\u0635\u064a\u062f: {e}")
            return {}

    def get_market_data(self, symbol):
        try:
            contract = Index(symbol, 'CBOE') if symbol == 'SPX' else Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            ticker = self.ib.reqMktData(contract)
            self.ib.sleep(1)
            return ticker
        except Exception as e:
            self.logger.error(f"\u062e\u0637\u0623 \u0641\u064a \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a: {e}")
            return None
