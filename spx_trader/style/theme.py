# style.py
import tkinter as tk
from tkinter import ttk

def apply_3d_style(root):
    """تطبيق استايل ثلاثي الأبعاد مع خلفية رمادية وخطوط سوداء"""
    root.configure(bg='#E0E0E0')  # خلفية رمادية فاتحة للنافذة الرئيسية
    
    # إنشاء أنماط ttk
    style = ttk.Style()
    
    # ألوان أساسية
    BG_COLOR = '#D3D3D3'  # رمادي فاتح للخلفيات
    FG_COLOR = '#000000'  # أسود للنصوص
    ACCENT_COLOR = '#3498DB'  # أزرق للعناصر التفاعلية
    
    # تخصيص دفتر التبويبات
    style.configure('TNotebook', background=BG_COLOR)
    style.configure('TNotebook.Tab', 
                   background=BG_COLOR,
                   foreground=FG_COLOR,
                   font=('Helvetica', 12, 'bold'),
                   padding=[12, 5])
    style.map('TNotebook.Tab', 
              background=[('selected', ACCENT_COLOR)],
              foreground=[('selected', 'white')])
    
    # تخصيص الأزرار (رمادي مع خط أسود)
    style.configure('TButton', 
                   background=BG_COLOR,
                   foreground=FG_COLOR,
                   font=('Helvetica', 12, 'bold'),
                   borderwidth=3,
                   relief='raised')
    style.map('TButton', 
              background=[('active', '#B0B0B0'), ('pressed', '#909090')])
    
    # تخصيص إطارات المجموعة
    style.configure('TLabelframe', 
                   background=BG_COLOR,
                   foreground=FG_COLOR,
                   font=('Helvetica', 12, 'bold'),
                   borderwidth=2,
                   relief='groove')
    style.configure('TLabelframe.Label', 
                   background=BG_COLOR,
                   foreground=FG_COLOR)
    
    # تخصيص حقول الإدخال
    style.configure('TEntry', 
                   fieldbackground='white',
                   foreground=FG_COLOR,
                   insertcolor=FG_COLOR,
                   bordercolor=ACCENT_COLOR,
                   lightcolor=ACCENT_COLOR,
                   darkcolor=ACCENT_COLOR)
    
    # تخصيص التسميات
    style.configure('TLabel', 
                   background=BG_COLOR,
                   foreground=FG_COLOR,
                   font=('Helvetica', 12))
    
    # تخصيص شريط التمرير
    style.configure('Vertical.TScrollbar', 
                   background=ACCENT_COLOR,
                   troughcolor=BG_COLOR)
    
    # تخصيص الـ Checkbutton
    style.configure('TCheckbutton',
                   background=BG_COLOR,
                   foreground=FG_COLOR,
                   font=('Helvetica', 12))
    
    return {
        'notebook': {'style': 'TNotebook'},
        'button': {'style': 'TButton'},
        'frame': {'style': 'TLabelframe'},
        'label': {'style': 'TLabel'},
        'entry': {'style': 'TEntry'},
        'scrollbar': {'style': 'Vertical.TScrollbar'},
        'checkbutton': {'style': 'TCheckbutton'}
    }
