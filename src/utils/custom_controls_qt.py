"""Qt 专属公共控件。"""

from PySide6.QtWidgets import QPushButton, QTabWidget


class ThemedButton(QPushButton):
    """保留 wx 版本同名按钮的轻量 Qt 实现。"""


class ThemedNotebook(QTabWidget):
    """支持可关闭标签的 Qt 标签页。"""

    def __init__(self, *args, closable=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDocumentMode(True)
        self.setTabsClosable(closable)
