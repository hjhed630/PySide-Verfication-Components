# coding: utf-8

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
from .flyout import (
    Flyout,
    FlyoutView,
    FlyoutAnimationType,
    FlyoutAnimationManager,
)
from src.components.slider import VerificationSlider

# from .image import VerificationImage
from .url_image import VerificationImage


class VerificationCard(QWidget):
    """
    滑动验证卡片控件。
    包含验证图片（VerificationImage）和滑动条（VerificationSlider），
    通过滑动条控制图片上的滑块位置，验证用户操作是否与预期位置匹配。
    """

    verificationSuccess = Signal()
    """验证成功信号"""

    verificationFailed = Signal()
    """验证失败信号"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化验证卡片。

        :param parent: 父级控件，默认为None。
        """
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)

        # 验证图片控件
        self.verifyImage: VerificationImage = VerificationImage(self)

        # 滑动条控件
        self.verifySlider: VerificationSlider = VerificationSlider(self)

        self.vBoxLayout.addWidget(self.verifyImage)
        self.vBoxLayout.addWidget(self.verifySlider)

        # 连接滑动条的值变化信号到图片的移动距离
        self.verifySlider.valueChanged.connect(self.verifyImage.setMoveX)
        # 连接滑动条的结果信号到验证方法
        self.verifySlider.resultSignal.connect(self.verify)

        # 允许的误差范围（像素）
        self.tolerance: int = 10

        # 尝试次数限制
        self.attemptCount: int = 0
        self.maxAttempts: int = 5

    def verify(self, value: int) -> None:
        """
        验证当前滑块位置是否正确。

        :param value: 滑动条当前值（无用参数，保留以匹配信号）
        """
        self.pixmapValue = self.verifyImage.getMoveX()
        self.correctValue = self.verifyImage.getCorrectValue()
        # 检查位置是否在容差范围内，并且滑动条行为分析通过
        if (
            abs(self.pixmapValue - self.correctValue) <= self.tolerance
            and self.verifySlider.analyzeBehavior()
        ):
            print("验证成功")
            self.verificationSuccess.emit()
            self.verifySlider.setSuccess(True)
        else:
            print("验证失败")
            self.verificationFailed.emit()
            # 刷新图片（更换背景或滑块位置）
            self.verifyImage.refresh_image()
            self.verifySlider.setSuccess(False)
            self.verifySlider.setError(True)


class VerificationFlyoutView(FlyoutView):
    """自定义浮窗视图，内部包含一个验证卡片（VerificationCard）。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化浮窗视图。

        :param parent: 父级控件，默认为None。
        """
        super().__init__(parent)

        self.card: VerificationCard = VerificationCard(self)

        # 清空父类默认的布局内容（假设父类有一个 widgetLayout）
        while self.widgetLayout.count():
            item = self.widgetLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 将验证卡片添加到布局中
        self.widgetLayout.addWidget(self.card)

        # 设置边距
        self.widgetLayout.setContentsMargins(10, 10, 10, 10)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        # 调整视图大小以适应内容
        self.adjustSize()


class VerificationFlyout(Flyout):
    """可弹出的验证浮窗，包含验证卡片，验证成功后自动关闭。"""

    success = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        初始化验证浮窗。

        :param parent: 父级控件，默认为None。
        """
        view = VerificationFlyoutView()
        super().__init__(view, parent, isDeleteOnClose=False)
        self.view: VerificationFlyoutView = view
        # 验证成功信号连接关闭窗口的方法
        self.view.card.verificationSuccess.connect(self.closeWindow)

    @classmethod
    def create(
        cls,
        target: Optional[Union[QWidget, QPoint]] = None,
        parent: Optional[QWidget] = None,
    ) -> "VerificationFlyout":

        flyout = cls(parent)
        aniType = FlyoutAnimationType.PULL_UP
        if target is None:
            return flyout

        flyout.show()
        if isinstance(target, QWidget):
            # 根据动画类型计算相对于目标控件的位置
            pos = FlyoutAnimationManager.make(aniType, flyout).position(target)
        else:
            pos = target

        flyout.exec(pos, aniType)
        return flyout

    def closeWindow(self) -> None:
        """延迟1秒后执行关闭窗口。"""
        self.success.emit()
        QTimer.singleShot(300, self.fadeOut)
