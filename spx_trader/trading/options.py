# trading/options.py
from ib_insync import *
import time
from spx_trader.utils.logger import Logger  # استيراد مطلق
from spx_trader.utils.file_manager import save_trade_to_file  # استيراد مطلق


class OptionTrader:
    def __init__(self, trader):
        self.trader = trader
        self.ib = trader.ib
        self.logger = Logger()
        self.current_trades = trader.current_trades
    
    def place_order(self, option_type, price, log_func):
        """
        تنفيذ أمر شراء خيار
        :param option_type: نوع الخيار (CALL/PUT)
        :param price: سعر السوق الحالي
        :param log_func: دالة تسجيل الرسائل
        :return: bool نتيجة التنفيذ
        """
        try:
            # تحديد سعر الإضراب الأقرب
            nearest_strike = self._calculate_nearest_strike(price)
            right = 'C' if option_type == 'CALL' else 'P'
            
            # إنشاء عقد الخيار
            option = self._create_option_contract(option_type, nearest_strike, right)
            
            # تأهيل العقد وتنفيذ الأمر
            self.ib.qualifyContracts(option)
            trade = self._execute_option_order(option)
            
            # انتظار التنفيذ
            if self._wait_for_order_execution(trade, 30):
                return self._handle_successful_trade(trade, option_type, nearest_strike, log_func)
            else:
                log_func("⚠️ فشل تنفيذ الأمر في الوقت المحدد")
                return False
                
        except Exception as e:
            error_msg = f"خطأ في تنفيذ أمر الخيار: {e}"
            self.logger.error(error_msg)
            log_func(error_msg)
            return False
    
    def _calculate_nearest_strike(self, price):
        """حساب سعر الإضراب الأقرب (مضاعفات 25)"""
        return round(price / 25) * 25
    
    def _create_option_contract(self, option_type, strike, right):
        """إنشاء عقد الخيار"""
        return Option(
            symbol='SPXW',
            lastTradeDateOrContractMonth=self.trader.config['expiry'],
            strike=strike,
            right=right,
            exchange='SMART'
        )
    
    def _execute_option_order(self, option):
        """تنفيذ أمر السوق للخيار"""
        order = MarketOrder('BUY', self.trader.config['qty'])
        return self.ib.placeOrder(option, order)
    
    def _wait_for_order_execution(self, trade, timeout):
        """انتظار تنفيذ الأمر مع تحديد وقت قصوى"""
        start_time = time.time()
        while not trade.fills and (time.time() - start_time) < timeout:
            time.sleep(1)
        return bool(trade.fills)
    
    def _handle_successful_trade(self, trade, option_type, strike, log_func):
        """معالجة الصفقة الناجحة"""
        entry_price = trade.fills[0].execution.price
        log_func(f"✅ تم تنفيذ صفقة {option_type} عند Strike {strike} - السعر {entry_price:.2f}")
        
        # حساب مستويات TP/SL
        target, stop = self._calculate_tp_sl(entry_price)
        
        # حفظ الصفقة
        self._record_trade(
            trade=trade,
            option_type=option_type,
            strike=strike,
            entry_price=entry_price,
            target=target,
            stop=stop
        )
        
        return True
    
    def _calculate_tp_sl(self, entry_price):
        """حساب مستويات جني الربح ووقف الخسارة"""
        target = entry_price * (1 + self.trader.config['tp_pct'] / 100)
        stop = entry_price * (1 - self.trader.config['sl_pct'] / 100)
        return target, stop
    
    def _record_trade(self, trade, option_type, strike, entry_price, target, stop):
        """تسجيل الصفقة في النظام"""
        trade_id = f"{option_type}_{strike}_{time.time()}"
        
        self.current_trades[trade_id] = {
            'trade': trade,
            'entry': entry_price,
            'target': target,
            'stop': stop,
            'option': trade.contract,
            'status': 'open'
        }
        
        save_trade_to_file(
            symbol='SPX',
            option_type=option_type,
            strike=strike,
            qty=self.trader.config['qty'],
            entry=entry_price,
            tp=target,
            sl=stop,
            expiry=self.trader.config['expiry']
        )
