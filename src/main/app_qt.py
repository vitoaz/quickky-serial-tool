"""QSerial PySide6 / Qt Widgets 启动入口。"""

import os
import sys

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.main_window_qt import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow(); window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
