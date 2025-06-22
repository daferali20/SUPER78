import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# تعديل مسار المشروع
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.trader import SPXTrader
from ui.main_window import MainWindow
from config import config as app_config

def main():
    trader = SPXTrader(app_config)  # تم تعديل SPXTrader ليقبل config
    app = MainWindow(trader)
    app.root.mainloop()

if __name__ == "__main__":
    main()
