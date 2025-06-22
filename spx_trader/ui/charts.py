# ui/charts.py
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from config import config
from utils.logger import Logger

class TradingCharts:
    def __init__(self, parent_frame):
        self.logger = Logger()
        self.parent = parent_frame
        self.setup_chart()

    def setup_chart(self):
        """تهيئة الرسم البياني الأساسي"""
        try:
            self.figure = Figure(figsize=(8, 4), dpi=100, facecolor='#2C3E50')
            self.chart = self.figure.add_subplot(111, facecolor='#2C3E50')
            self._apply_chart_style()
            
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
            self.canvas.get_tk_widget().pack_forget()  # مخفي بشكل افتراضي
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة الرسم البياني: {e}")

    def _apply_chart_style(self):
        """تطبيق التنسيق على الرسم البياني"""
        self.chart.grid(True, color='#34495E')
        self.chart.tick_params(colors='#ECF0F1')
        for spine in self.chart.spines.values():
            spine.set_color('#7F8C8D')

    def update_chart(self, df: pd.DataFrame):
        """تحديث الرسم البياني ببيانات جديدة"""
        try:
            if not hasattr(self, 'chart'):
                return

            self.chart.clear()
            
            # رسم خط السعر
            self.chart.plot(df.index, df['close'], 
                          label='السعر', 
                          color='#3498DB',
                          linewidth=1.5)
            
            # رسم المتوسط المتحرك إذا كان مفعلاً
            if config.get('use_ma', False):
                ma_period = config.get('ma_period', 50)
                df['ma'] = df['close'].rolling(window=ma_period).mean()
                self.chart.plot(df.index, df['ma'], 
                              label=f'MA {ma_period}', 
                              color='#E74C3C',
                              linestyle='--',
                              linewidth=1.2)
            
            # تحديد الشموع الانعكاسية
            self._plot_reversal_signals(df)
            
            self._finalize_chart()
            self.canvas.draw()
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الرسم البياني: {e}")

    def _plot_reversal_signals(self, df):
        """رسم إشارات الانعكاس على الرسم البياني"""
        for i in range(2, len(df)):
            candle = df.iloc[i]
            prev = df.iloc[i-1]
            before_prev = df.iloc[i-2]
            
            body = abs(candle['close'] - candle['open'])
            candle_range = candle['high'] - candle['low']
            
            if candle_range == 0:
                continue
                
            upper_shadow = candle['high'] - max(candle['close'], candle['open'])
            lower_shadow = min(candle['close'], candle['open']) - candle['low']
            
            # إشارة شراء (انعكاس صاعد)
            if (prev['close'] < before_prev['close'] and 
                lower_shadow > 2 * body and 
                body < candle_range * 0.3):
                self.chart.plot(i, candle['close'], '^', 
                              markersize=10, 
                              color='#2ECC71',
                              label='إشارة شراء' if i == 2 else "")
            
            # إشارة بيع (انعكاس هابط)
            elif (prev['close'] > before_prev['close'] and 
                  upper_shadow > 2 * body and 
                  body < candle_range * 0.3):
                self.chart.plot(i, candle['close'], 'v', 
                              markersize=10, 
                              color='#E74C3C',
                              label='إشارة بيع' if i == 2 else "")

    def _finalize_chart(self):
        """إعدادات نهائية للرسم البياني"""
        self.chart.set_title("حركة السعر مع إشارات التداول", 
                           color='#ECF0F1',
                           pad=20)
        self.chart.legend(facecolor='#2C3E50',
                        edgecolor='#2C3E50',
                        labelcolor='#ECF0F1')
        self.chart.grid(True, color='#34495E', alpha=0.5)

    def toggle_visibility(self):
        """تبديل عرض/إخفاء الرسم البياني"""
        if self.canvas.get_tk_widget().winfo_ismapped():
            self.canvas.get_tk_widget().pack_forget()
        else:
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, 
                                           expand=True, 
                                           padx=10, 
                                           pady=5)
    def plot_indicators(self, df):
    df['ma'] = self.indicators.calculate_ma(df['close'])
    self.ax.plot(df.index, df['ma'], label='Moving Average')
