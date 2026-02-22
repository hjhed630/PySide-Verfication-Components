import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QGridLayout,
)

from src.basicSliderVerification import VerificationFlyout as NormalVerificationFlyout
from src.figureSliderVerification import VerificationFlyout as FigureVerificationFlyout


class Demo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("验证码示例")
        self.setMinimumSize(400, 300)

        layout = QGridLayout(self)

        normalVer = QPushButton("普通滑动验证码", self)
        normalVer.clicked.connect(self.showNormalVer)
        layout.addWidget(normalVer, 0, 0)

        fighureVer = QPushButton("形状滑动验证码", self)
        fighureVer.clicked.connect(self.showFigureVer)
        layout.addWidget(fighureVer, 0, 1)

    def showNormalVer(self):

        a = NormalVerificationFlyout.create(target=self.sender(), parent=self)
        a.success.connect(lambda: print("成功"))

    def showFigureVer(self):

        a = FigureVerificationFlyout.create(target=self.sender(), parent=self)
        a.success.connect(lambda: print("成功"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec())
