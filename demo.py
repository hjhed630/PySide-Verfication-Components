# coding: utf-8
import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
)

from src.basicSliderVerification import VerificationFlyout


# 普通滑动验证码
class Demo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("验证码示例")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        button = QPushButton()
        button.clicked.connect(self.showFlyout)
        layout.addWidget(button)

    def showFlyout(self):

        a = VerificationFlyout.create(target=self.sender(), parent=self)
        a.success.connect(lambda: print("成功"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec())
