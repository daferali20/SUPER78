# ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from config import config
from utils.logger import Logger
from style import apply_3d_style
from charts import TradingCharts
from trade_history import show_trade_history_window

class MainWindow:
    def __init__(self, trader):
        self.trader = trader
        self.logger = Logger()
        self.running = False
        self.config = trader.config
        self.create_gui()
        
    def create_gui(self):
        """إنشاء واجهة المستخدم الرسومية"""
        self.root = tk.Tk()
        self.root.title("نظام تداول SPX الآلي - الإصدار المحسن")
        self.root.geometry("1000x800")
        
        # تطبيق استايل ثلاثي الأبعاد
        self.style_config = apply_3d_style(self.root)
        
        self._create_notebook()
        self._create_trading_tab()
        self._create_watchlist_tab()
        self._setup_chart()
        
    def _create_notebook(self):
        """إنشاء دفتر التبويبات"""
        self.notebook = ttk.Notebook(self.root, **self.style_config['notebook'])
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
    def _create_trading_tab(self):
        """إنشاء تبويب التداول الرئيسي"""
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text='التداول')
        
        self._create_control_frame()
        self._create_button_frame()
        self._create_log_frame()
        
    def _create_control_frame(self):
        """إنشاء إطار التحكم"""
        control_frame = ttk.LabelFrame(self.main_tab, text="إعدادات التداول", **self.style_config['frame'])
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # حقول الإدخال
        entries = [
            ("📦 الكمية:", "qty", 0),
            ("📅 تاريخ العقد (YYYYMMDD):", "expiry", 1),
            ("🎯 نسبة جني الربح (%):", "tp_pct", 2),
            ("🛑 نسبة وقف الخسارة (%):", "sl_pct", 3)
        ]
        
        for text, config_key, row in entries:
            ttk.Label(control_frame, text=text, **self.style_config['label']).grid(
                row=row, column=0, padx=5, pady=5, sticky='e')
            entry = ttk.Entry(control_frame, **self.style_config['entry'])
            entry.insert(0, str(self.config[config_key]))
            entry.grid(row=row, column=1, padx=5, pady=5)
            setattr(self, f"{config_key}_entry", entry)
        
        # إعدادات المؤشرات الفنية
        self._create_indicators_settings(control_frame)
        
    def _create_indicators_settings(self, parent):
        """إنشاء إعدادات المؤشرات الفنية"""
        ttk.Label(parent, text="📊 إعدادات المؤشرات الفنية:", 
                 **self.style_config['label']).grid(row=0, column=2, columnspan=2, pady=5)
        
        # إعدادات RSI
        self.use_rsi_var = tk.BooleanVar(value=self.config['use_rsi'])
        self.use_rsi_cb = ttk.Checkbutton(
            parent, 
            text="استخدام RSI", 
            variable=self.use_rsi_var
        )
        self.use_rsi_cb.grid(row=1, column=2, padx=5, sticky='w')
        
        ttk.Label(parent, text="فترة RSI:", **self.style_config['label']).grid(
            row=1, column=3, padx=5, sticky='e')
        self.rsi_period_entry = ttk.Entry(parent, width=5, **self.style_config['entry'])
        self.rsi_period_entry.insert(0, str(self.config['rsi_period']))
        self.rsi_period_entry.grid(row=1, column=4, padx=5)
        
        # إعدادات المتوسط المتحرك
        self.use_ma_var = tk.BooleanVar(value=self.config['use_ma'])
        self.use_ma_cb = ttk.Checkbutton(
            parent, 
            text="استخدام المتوسط المتحرك", 
            variable=self.use_ma_var
        )
        self.use_ma_cb.grid(row=2, column=2, padx=5, sticky='w')
        
        ttk.Label(parent, text="فترة المتوسط المتحرك:", **self.style_config['label']).grid(
            row=2, column=3, padx=5, sticky='e')
        self.ma_period_entry = ttk.Entry(parent, width=5, **self.style_config['entry'])
        self.ma_period_entry.insert(0, str(self.config['ma_period']))
        self.ma_period_entry.grid(row=2, column=4, padx=5)
        
    def _create_button_frame(self):
        """إنشاء إطار الأزرار"""
        button_frame = ttk.Frame(self.main_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        buttons = [
            ("✅ بدء المراقبة", self.toggle_monitor, "start_btn"),
            ("💾 حفظ الإعدادات", self.save_settings, None),
            ("📊 عرض الرسم البياني", self.show_chart, None),
            ("📋 سجل الصفقات", self.show_trade_history, None)
        ]
        
        for text, command, attr_name in buttons:
            btn = ttk.Button(
                button_frame, 
                text=text, 
                command=command,
                **self.style_config['button']
            )
            btn.pack(side=tk.LEFT, padx=5)
            if attr_name:
                setattr(self, attr_name, btn)
        
    def _create_log_frame(self):
        """إنشاء منطقة السجل"""
        log_frame = ttk.LabelFrame(self.main_tab, text="سجل الأحداث", **self.style_config['frame'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output = tk.Text(
            log_frame, 
            height=15, 
            wrap=tk.WORD,
            bg='#34495E',
            fg='#ECF0F1',
            insertbackground='white',
            font=('Helvetica', 10))
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, **self.style_config['scrollbar'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar.config(command=self.output.yview)
        self.output.config(yscrollcommand=scrollbar.set)
        
    def _create_watchlist_tab(self):
        """إنشاء تبويب قائمة المتابعة"""
        watchlist_tab = ttk.Frame(self.notebook)
        self.notebook.add(watchlist_tab, text='قائمة المتابعة')
        
        ttk.Label(watchlist_tab, text="قائمة الأسهم للمتابعة (سطر لكل سهم):", 
                 **self.style_config['label']).pack(padx=10, pady=5)
        
        self.watchlist_text = tk.Text(
            watchlist_tab, 
            height=15,
            bg='#34495E',
            fg='#ECF0F1',
            insertbackground='white',
            font=('Helvetica', 10))
        self.watchlist_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Button(
            watchlist_tab, 
            text="حفظ القائمة", 
            command=self.save_watchlist,
            **self.style_config['button']
        ).pack(pady=5)
        
    def _setup_chart(self):
        """إعداد الرسم البياني"""
        self.charts = TradingCharts(self.main_tab)
        
    def toggle_monitor(self):
        """تبديل حالة المراقبة (تشغيل/إيقاف)"""
        if not self.trader.running:
            if not self.trader.connect_ibkr():
                return
                
            self.trader.running = True
            self.start_btn.config(text="⏹ إيقاف المراقبة")
            
            # بدء خيط للمراقبة
            self.monitor_thread = threading.Thread(
                target=self.trader.start_async_monitor,
                daemon=True
            )
            self.monitor_thread.start()
            
            # بدء خيط لمتابعة الصفقات المفتوحة
            self.trade_monitor_thread = threading.Thread(
                target=self.trader.monitor_open_trades,
                args=(self.log_message,),
                daemon=True
            )
            self.trade_monitor_thread.start()
            
            self.log_message("🚀 بدء مراقبة قائمة المتابعة...")
        else:
            self.trader.running = False
            self.start_btn.config(text="✅ بدء المراقبة")
            self.log_message("🛑 توقف مراقبة قائمة المتابعة")
    
    def log_message(self, msg):
        """تسجيل رسالة في سجل الأحداث"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.output.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.output.see(tk.END)
        self.output.update()
        
    def save_settings(self):
        """حفظ الإعدادات من الواجهة إلى ملف التكوين"""
        try:
            self.trader.config.update({
                'qty': int(self.qty_entry.get()),
                'expiry': self.expiry_entry.get().strip(),
                'tp_pct': float(self.tp_entry.get()),
                'sl_pct': float(self.sl_entry.get()),
                'use_rsi': self.use_rsi_var.get(),
                'rsi_period': int(self.rsi_period_entry.get()),
                'use_ma': self.use_ma_var.get(),
                'ma_period': int(self.ma_period_entry.get())
            })
            self.trader.save_config()
            self.log_message("💾 تم حفظ الإعدادات بنجاح")
        except ValueError as e:
            messagebox.showerror("خطأ", f"قيم إدخال غير صالحة: {e}")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل حفظ الإعدادات: {e}")
    
    def save_watchlist(self):
        """حفظ قائمة المتابعة"""
        try:
            content = self.watchlist_text.get('1.0', tk.END).strip()
            with open(config.watchlist_file, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("تم", "تم حفظ قائمة المتابعة بنجاح")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل حفظ القائمة: {e}")
    
    def show_chart(self):
        """إظهار/إخفاء الرسم البياني"""
        self.charts.toggle_visibility()
    
    def show_trade_history(self):
        """عرض سجل الصفقات"""
        show_trade_history_window(self.root, self.style_config)
    
    def update_chart_data(self, data):
        """تحديث بيانات الرسم البياني"""
        self.charts.update_chart(data)
