from typing import Optional, Union

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)

from PySide6.QtCore import Qt

from PySide6.QtCore import (
    QTimer,
    Signal,
    QPoint,
)
from src.components.flyout import (
    Flyout,
    FlyoutView,
    PullUpFlyoutAnimationManager,
)

from .url_image import VerificationImage


class VerificationCard(QWidget):

    verificationSuccess = Signal()
    verificationFailed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:

        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)

        self.verifyImage: VerificationImage = VerificationImage(self)

        self.tipLabel = QLabel("点击: 加载中...", self)
        self.tipLabel.setFixedHeight(30)
        self.tipLabel.setAlignment(Qt.AlignCenter)

        self.vBoxLayout.addWidget(self.verifyImage)
        self.vBoxLayout.addWidget(self.tipLabel)

        self.verifyImage.verificationComplete.connect(self.verify)


        if hasattr(self.verifyImage, 'networkManager'):
            self.verifyImage.networkManager.finished.connect(self.onImageLoaded)

    def onImageLoaded(self):

        self.tipLabel.setText(self.verifyImage.verificationText)

    def verify(self, success: bool, correct: list) -> None:

        if success:
            self.verificationSuccess.emit()
        else:
            self.verificationFailed.emit()
            self.verifyImage.refreshImage()

            QTimer.singleShot(100, self.onImageLoaded)

    def showEvent(self, event):
        super().showEvent(event)

        self.tipLabel.setText(self.verifyImage.verificationText)


class VerificationFlyoutView(FlyoutView):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.card: VerificationCard = VerificationCard(self)

        while self.widgetLayout.count():
            item = self.widgetLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.widgetLayout.addWidget(self.card)

        self.widgetLayout.setContentsMargins(10, 10, 10, 10)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.adjustSize()


class VerificationFlyout(Flyout):

    success = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        view = VerificationFlyoutView()
        super().__init__(view, parent, isDeleteOnClose=False)
        self.view: VerificationFlyoutView = view
        self.view.card.verificationSuccess.connect(self.closeWindow)

    @classmethod
    def create(
        cls,
        target: Optional[Union[QWidget, QPoint]] = None,
        parent: Optional[QWidget] = None,
    ) -> "VerificationFlyout":

        flyout = cls(parent)
        if target is None:
            return flyout

        flyout.show()
        if isinstance(target, QWidget):
            pos = PullUpFlyoutAnimationManager(flyout).position(target)
        else:
            pos = target

        flyout.exec(pos)
        return flyout

    def closeWindow(self) -> None:
        self.success.emit()
        QTimer.singleShot(300, self.fadeOut)
