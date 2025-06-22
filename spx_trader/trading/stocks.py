# trading/stocks.py
import time
from ib_insync import *
from spx_trader.utils.logger import Logger  # استيراد مطلق

 #-------------------------
class StockTrader:
    def __init__(self, trader):
        """تهيئة متداول الأسهم"""
        self.trader = trader
        self.ib = trader.ib
        self.logger = Logger()
        self.current_trades = {}  # تمت الإضافة: قاموس لتتبع الصفقات المفتوحة
        self.config = trader.config  # تمت الإضافة: تكوين متسق
    
    def place_order(self, symbol, action, price=None, order_type='MARKET'):
        """تنفيذ أمر شراء/بيع سهم
        
        المعاملات:
            symbol (str): رمز السهم
            action (str): 'CALL' للشراء، 'PUT' للبيع
            price (float): السعر المطلوب لأوامر الحد/الإيقاف
            order_type (str): 'MARKET' للطلب السوقي، 'LIMIT' للحد، 'STOP' للإيقاف
        """
        try:
            # إنشاء عقد السهم والتأهل
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # إنشاء نوع الأمر المناسب
            if order_type.upper() == 'MARKET':
                order = MarketOrder('BUY' if action == 'CALL' else 'SELL', 
                                  self.config['qty'])
            elif order_type.upper() == 'LIMIT' and price:
                order = LimitOrder('BUY' if action == 'CALL' else 'SELL',
                                self.config['qty'],
                                price)
            elif order_type.upper() == 'STOP' and price:
                order = StopOrder('BUY' if action == 'CALL' else 'SELL',
                               self.config['qty'],
                               price)
            else:
                raise ValueError("نوع أمر غير صالح أو سعر مفقود")
            
            # تنفيذ الأمر
            trade = self.ib.placeOrder(contract, order)
            
            # انتظار تنفيذ الصفقة بحد أقصى 30 ثانية
            start_time = time.time()
            while not trade.fills and (time.time() - start_time) < 30:
                time.sleep(1)
            
            # إذا تم تنفيذ الصفقة
            if trade.fills:
                entry_price = trade.fills[0].execution.price
                self.logger.info(f"✅ [{symbol}] تم تنفيذ صفقة {action} عند السعر {entry_price:.2f}")
                
                # حساب أهداف الربح ووقف الخسارة
                if action == 'CALL':
                    target = entry_price * (1 + self.config['tp_pct'] / 100)
                    stop = entry_price * (1 - self.config['sl_pct'] / 100)
                else:  # PUT
                    target = entry_price * (1 - self.config['tp_pct'] / 100)
                    stop = entry_price * (1 + self.config['sl_pct'] / 100)
                
                # تسجيل الصفقة الجارية
                trade_id = f"{symbol}_{action}_{int(time.time())}"
                self.current_trades[trade_id] = {
                    'trade': trade,
                    'entry': entry_price,
                    'target': target,
                    'stop': stop,
                    'contract': contract,
                    'status': 'open',
                    'type': 'stock'
                }
                
                # حفظ الصفقة في الملف
                self._save_trade_to_file(
                    symbol=symbol,
                    action=action,
                    qty=self.config['qty'],
                    entry=entry_price,
                    tp=target,
                    sl=stop
                )
                return True
            else:
                self.logger.warning(f"⚠️ [{symbol}] فشل تنفيذ الأمر في الوقت المحدد")
                return False
                
        except ValueError as ve:
            self.logger.error(f"خطأ في التحقق من صحة الأمر: {ve}")
            return False
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ أمر السهم: {e}")
            return False
    
    def _save_trade_to_file(self, **trade_data):
        """طريقة خاصة لحفظ تفاصيل الصفقة في ملف"""
        # سيتم تنفيذ الوظيفة هنا
        pass
