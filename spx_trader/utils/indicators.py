# utils/indicators.py
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from config import config
from utils.logger import Logger

class TechnicalIndicators:
    def __init__(self):
        self.logger = Logger()
        
    def calculate_rsi(self, prices: pd.Series, period: int = None) -> pd.Series:
        """
        حساب مؤشر القوة النسبية (RSI)
        
        Args:
            prices (pd.Series): سلسلة أسعار الإغلاق
            period (int): فترة الحساب (اختياري)
            
        Returns:
            pd.Series: سلسلة قيم RSI
        """
        try:
            period = period or config.get('rsi_period', 14)
            delta = prices.diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            self.logger.error(f"خطأ في حساب RSI: {e}")
            return pd.Series()

    def calculate_ma(self, prices: pd.Series, period: int = None) -> pd.Series:
        """
        حساب المتوسط المتحرك البسيط (MA)
        
        Args:
            prices (pd.Series): سلسلة الأسعار
            period (int): فترة الحساب (اختياري)
            
        Returns:
            pd.Series: سلسلة المتوسط المتحرك
        """
        try:
            period = period or config.get('ma_period', 50)
            return prices.rolling(window=period).mean()
        except Exception as e:
            self.logger.error(f"خطأ في حساب المتوسط المتحرك: {e}")
            return pd.Series()

    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series]:
        """
        حساب عصابات بولينجر
        
        Args:
            prices (pd.Series): سلسلة الأسعار
            period (int): فترة الحساب
            std_dev (int): عدد الانحرافات المعيارية
            
        Returns:
            Tuple: (النطاق العلوي، النطاق السفلي)
        """
        try:
            ma = self.calculate_ma(prices, period)
            std = prices.rolling(window=period).std()
            upper_band = ma + (std * std_dev)
            lower_band = ma - (std * std_dev)
            return upper_band, lower_band
        except Exception as e:
            self.logger.error(f"خطأ في حساب بولينجر: {e}")
            return pd.Series(), pd.Series()

    def identify_reversal_candles(self, df: pd.DataFrame) -> Optional[str]:
        """
        تحديد الشموع الانعكاسية مع تصفية بواسطة المؤشرات
        
        Args:
            df (pd.DataFrame): بيانات الشموع
            
        Returns:
            Optional[str]: 'reversal_up' أو 'reversal_down' أو None
        """
        try:
            if len(df) < 3:
                return None
                
            # حساب المؤشرات
            df['rsi'] = self.calculate_rsi(df['close'])
            df['ma'] = self.calculate_ma(df['close'])
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            before_prev = df.iloc[-3]

            # تحديد الاتجاه
            trend = 'down' if prev['close'] < before_prev['close'] else 'up'
            
            # تحليل الشمعة
            body = abs(last['close'] - last['open'])
            candle_range = last['high'] - last['low']
            
            if candle_range == 0:
                return None
                
            upper_shadow = last['high'] - max(last['close'], last['open'])
            lower_shadow = min(last['close'], last['open']) - last['low']

            # تطبيق الفلاتر
            rsi_ok = not config.get('use_rsi', True) or (
                (trend == 'down' and df['rsi'].iloc[-1] <= config.get('rsi_oversold', 30)) or
                (trend == 'up' and df['rsi'].iloc[-1] >= config.get('rsi_overbought', 70))
                
            ma_ok = not config.get('use_ma', True) or (
                (last['close'] < df['ma'].iloc[-1] and trend == 'up') or
                (last['close'] > df['ma'].iloc[-1] and trend == 'down'))

            # تحديد الانعكاس
            if (trend == 'down' and lower_shadow > 2 * body and 
                body < candle_range * 0.3 and rsi_ok and ma_ok):
                return 'reversal_up'
                
            elif (trend == 'up' and upper_shadow > 2 * body and 
                  body < candle_range * 0.3 and rsi_ok and ma_ok):
                return 'reversal_down'
                
            return None
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديد الشموع الانعكاسية: {e}")
            return None

    def calculate_macd(self, prices: pd.Series, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Tuple[pd.Series, pd.Series]:
        """
        حساب مؤشر MACD
        
        Args:
            prices (pd.Series): سلسلة الأسعار
            fast_period (int): فترة المتوسط السريع
            slow_period (int): فترة المتوسط البطيء
            signal_period (int): فترة خط الإشارة
            
        Returns:
            Tuple: (MACD, خط الإشارة)
        """
        try:
            fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
            slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
            macd_line = fast_ema - slow_ema
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            return macd_line, signal_line
        except Exception as e:
            self.logger.error(f"خطأ في حساب MACD: {e}")
            return pd.Series(), pd.Series()
