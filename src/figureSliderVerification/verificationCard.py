from typing import Optional, Union, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)
from PySide6.QtGui import (
    QPixmap,
)
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
from src.components.slider import VerificationSlider

from .url_image import VerificationImage


class VerificationCard(QWidget):

    verificationSuccess = Signal()

    verificationFailed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)

        self.verifyImage: VerificationImage = VerificationImage(self)

        self.verifySlider: VerificationSlider = VerificationSlider(self)

        self.vBoxLayout.addWidget(self.verifyImage)
        self.vBoxLayout.addWidget(self.verifySlider)

        self.verifySlider.valueChanged.connect(self.verifyImage.setMoveX)
        self.verifySlider.resultSignal.connect(self.verify)

        self.tolerance: int = 10

        self.attemptCount: int = 0
        self.maxAttempts: int = 5

    def verify(self, resultDict: dict) -> None:
        self.pixmapValue = self.verifyImage.getMoveX()
        self.correctValue = self.verifyImage.getCorrectValue()
        if (
            resultDict["result"]
            and abs(self.pixmapValue - self.correctValue) <= self.tolerance
        ):
            self.verificationSuccess.emit()
            self.verifySlider.setSuccess(True)
        else:
            self.verificationFailed.emit()
            self.verifyImage.refresh_image()
            self.verifySlider.setSuccess(False)
            self.verifySlider.setError(True)


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
