# config.py
import os
import sys
import csv
import configparser
from pathlib import Path
from spx_trader.utils.resource import resource_path

def resource_path(relative_path):
    """احصل على المسار الصحيح للملفات بعد تحزيم PyInstaller"""
    try:
        base_path = sys._MEIPASS  # مسار الملفات داخل EXE
    except Exception:
        base_path = os.path.abspath(".")  # مسار الملفات عند التشغيل العادي
    return os.path.join(base_path, relative_path)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(resource_path('data'))
TRADES_DIR = DATA_DIR / 'trades'

# إنشاء المجلدات إذا لم تكن موجودة
DATA_DIR.mkdir(exist_ok=True)
TRADES_DIR.mkdir(exist_ok=True)

class Config:
    def __init__(self):
        self.config_file = DATA_DIR / 'config.ini'
        self.watchlist_file = DATA_DIR / 'watchlist.ini'
        self.trades_log = TRADES_DIR / 'executed_trades.csv'
        self._ensure_files_exist()
        
    def _ensure_files_exist(self):
        if not self.config_file.exists():
            self._create_default_config()
            
        if not self.watchlist_file.exists():
            self._create_default_watchlist()
            
        if not self.trades_log.exists():
            self._create_trades_log()
    
    def _create_default_config(self):
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'qty': '1',
            'tp_pct': '5',
            'sl_pct': '3',
            'expiry': '',
            'rsi_period': '14',
            'rsi_overbought': '70',
            'rsi_oversold': '30',
            'use_rsi': 'True',
            'use_ma': 'True',
            'ma_period': '50'
        }
        with open(self.config_file, 'w') as f:
            config.write(f)
    
    def _create_default_watchlist(self):
        with open(self.watchlist_file, 'w') as f:
            f.write("SPX\n")
    
    def _create_trades_log(self):
        with open(self.trades_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp', 'Symbol', 'Type', 'Strike', 'Qty', 
                'Entry', 'TP', 'SL', 'Expiry', 'Status',
                'ExitPrice', 'ExitTime'
            ])

config = Config()
