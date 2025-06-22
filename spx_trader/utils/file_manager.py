# utils/file_manager.py
import csv
from datetime import datetime
from config import config

def save_trade_to_file(symbol, option_type, strike, qty, entry, tp, sl, expiry):
    """حفظ تفاصيل الصفقة في ملف CSV"""
    try:
        file_exists = config.trades_log.exists()
        
        with open(config.trades_log, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    'Timestamp', 'Symbol', 'Type', 'Strike', 'Qty', 
                    'Entry', 'TP', 'SL', 'Expiry', 'Status',
                    'ExitPrice', 'ExitTime'
                ])
                
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                symbol,
                option_type,
                strike,
                qty,
                entry,
                tp,
                sl,
                expiry,
                'OPEN',
                '',
                ''
            ])
    except Exception as e:
        raise Exception(f"فشل في حفظ الصفقة: {e}")
