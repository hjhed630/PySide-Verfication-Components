# coding:utf-8
from enum import Enum
import sys
from typing import Union

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QPoint,
    QParallelAnimationGroup,
    QEasingCurve,
    QMargins,
    QObject,
    Signal,
    QEvent,
    QRect,
)
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QWidget,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QVBoxLayout,
    QApplication,
)


def getCurrentScreenGeometry():
    """获取当前屏幕的几何区域"""
    screen = QApplication.primaryScreen()
    if screen:
        return screen.geometry()
    return QRect(0, 0, 1920, 1080)


class FlyoutAnimationType(Enum):

    PULL_UP = 0


class FlyoutViewBase(QWidget):
    """Flyout view base class - 支持自定义颜色和圆角"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._bgColor = QColor(255, 255, 255)  # 背景色
        self._borderColor = QColor(0, 0, 0, 50)  # 边框色
        self._borderRadius = 5  # 圆角半径

    def setBackgroundColor(self, color: QColor):
        self._bgColor = color
        self.update()  # 触发重绘

    def backgroundColor(self):
        return self._bgColor

    def setBorderColor(self, color: QColor):
        self._borderColor = color
        self.update()

    def borderColor(self):
        return self._borderColor

    def setBorderRadius(self, radius: int):
        self._borderRadius = radius
        self.update()

    def borderRadius(self):
        return self._borderRadius

    def addWidget(self, widget: QWidget, stretch=0, align=Qt.AlignLeft):
        raise NotImplementedError

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.setBrush(self.backgroundColor())
        painter.setPen(self.borderColor())

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, self.borderRadius(), self.borderRadius())


class FlyoutView(FlyoutViewBase):
    """Flyout view"""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.viewLayout = QHBoxLayout()
        self.widgetLayout = QVBoxLayout()

        self.vBoxLayout.setContentsMargins(1, 1, 1, 1)
        self.vBoxLayout.setSpacing(0)
        self.widgetLayout.setContentsMargins(0, 8, 0, 8)
        self.widgetLayout.setSpacing(0)
        self.viewLayout.setSpacing(4)

        self.vBoxLayout.addLayout(self.viewLayout)
        self.viewLayout.addLayout(self.widgetLayout)

        margins = QMargins(6, 5, 6, 5)
        margins.setLeft(20)
        margins.setRight(20)
        self.viewLayout.setContentsMargins(margins)

    def addWidget(self, widget: QWidget, stretch=0, align=Qt.AlignLeft):
        """添加部件到视图中"""
        self.widgetLayout.addSpacing(8)
        self.widgetLayout.addWidget(widget, stretch, align)

    def showEvent(self, e):
        super().showEvent(e)
        self.adjustSize()


class Flyout(QWidget):

    closed = Signal()

    def __init__(
        self,
        view: FlyoutViewBase,
        parent=None,
        isDeleteOnClose=True,
        isMacInputMethodEnabled=False,
    ):
        super().__init__(parent=parent)
        self.view = view
        self.hBoxLayout = QHBoxLayout(self)
        self.aniManager = None
        self.isDeleteOnClose = isDeleteOnClose
        self.isMacInputMethodEnabled = isMacInputMethodEnabled

        self.hBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.hBoxLayout.addWidget(self.view)

        self._shadowBlurRadius = 80
        self._shadowOffset = (4, 4)
        self._shadowColor = QColor(0, 0, 0, 30)

        self.setShadowEffect()  # 应用默认阴影

        self.setAttribute(Qt.WA_TranslucentBackground)

        if sys.platform != "darwin" or not isMacInputMethodEnabled:
            self.setWindowFlags(
                Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
            )
        else:
            self.setWindowFlags(
                Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
            )
            QApplication.instance().installEventFilter(self)

    def setShadowBlurRadius(self, radius: int):
        """设置阴影模糊半径"""
        self._shadowBlurRadius = radius
        self.setShadowEffect()

    def setShadowOffset(self, dx: int, dy: int):
        """设置阴影偏移量 (x, y)"""
        self._shadowOffset = (dx, dy)
        self.setShadowEffect()

    def setShadowColor(self, color: QColor):
        """设置阴影颜色"""
        self._shadowColor = color
        self.setShadowEffect()

    # -----------------------------------------

    def eventFilter(self, watched, event):
        if sys.platform == "darwin" and self.isMacInputMethodEnabled:
            if self.isVisible() and event.type() == QEvent.MouseButtonPress:
                if not self.rect().contains(self.mapFromGlobal(event.globalPos())):
                    self.close()
        return super().eventFilter(watched, event)

    def setShadowEffect(self, blurRadius=None, offset=None):
        """添加阴影效果（若未提供参数则使用当前存储的属性）"""
        if blurRadius is None:
            blurRadius = self._shadowBlurRadius
        if offset is None:
            offset = self._shadowOffset
        color = self._shadowColor

        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.view.setGraphicsEffect(None)
        self.view.setGraphicsEffect(self.shadowEffect)

    def closeEvent(self, e):
        if self.isDeleteOnClose:
            self.deleteLater()
        super().closeEvent(e)
        self.closed.emit()

    def showEvent(self, e):
        self.activateWindow()
        super().showEvent(e)

    def exec(self, pos: QPoint, aniType=FlyoutAnimationType.PULL_UP):
        """在指定位置显示并运行动画"""
        self.aniManager = FlyoutAnimationManager.make(aniType, self)
        self.show()
        self.aniManager.exec(pos)

    @classmethod
    def make(
        cls,
        view: FlyoutViewBase,
        target: Union[QWidget, QPoint] = None,
        parent=None,
        aniType=FlyoutAnimationType.PULL_UP,
        isDeleteOnClose=True,
        isMacInputMethodEnabled=False,
    ):
        w = cls(view, parent, isDeleteOnClose, isMacInputMethodEnabled)

        if target is None:
            return w

        w.show()
        if isinstance(target, QWidget):
            target = FlyoutAnimationManager.make(aniType, w).position(target)
        w.exec(target, aniType)
        return w

    @classmethod
    def create(
        cls,
        target: Union[QWidget, QPoint] = None,
        parent=None,
        aniType=FlyoutAnimationType.PULL_UP,
        isDeleteOnClose=True,
        isMacInputMethodEnabled=False,
    ):
        view = FlyoutView()
        w = cls.make(
            view, target, parent, aniType, isDeleteOnClose, isMacInputMethodEnabled
        )
        view.closed.connect(w.close)
        return w

    def fadeOut(self):
        """淡出并关闭"""
        self.fadeOutAni = QPropertyAnimation(self, b"windowOpacity", self)
        self.fadeOutAni.finished.connect(self.close)
        self.fadeOutAni.setStartValue(1)
        self.fadeOutAni.setEndValue(0)
        self.fadeOutAni.setDuration(120)
        self.fadeOutAni.start()


class FlyoutAnimationManager(QObject):
    """Flyout动画管理器基类"""

    managers = {}

    def __init__(self, flyout: Flyout):
        super().__init__()
        self.flyout = flyout
        self.aniGroup = QParallelAnimationGroup(self)
        self.slideAni = QPropertyAnimation(flyout, b"pos", self)
        self.opacityAni = QPropertyAnimation(flyout, b"windowOpacity", self)

        self.slideAni.setDuration(187)
        self.opacityAni.setDuration(187)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)

        self.slideAni.setEasingCurve(QEasingCurve.OutQuad)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)
        self.aniGroup.addAnimation(self.slideAni)
        self.aniGroup.addAnimation(self.opacityAni)

    @classmethod
    def register(cls, name):
        """注册动画管理器"""

        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager
            return Manager

        return wrapper

    def exec(self, pos: QPoint):
        """开始动画"""
        raise NotImplementedError

    def _adjustPosition(self, pos):
        rect = getCurrentScreenGeometry()
        w, h = self.flyout.sizeHint().width() + 5, self.flyout.sizeHint().height()
        x = max(rect.left(), min(pos.x(), rect.right() - w))
        y = max(rect.top(), min(pos.y() - 4, rect.bottom() - h + 5))
        return QPoint(x, y)

    def position(self, target: QWidget):
        """返回相对于target的左上角位置"""
        raise NotImplementedError

    @classmethod
    def make(
        cls, aniType: FlyoutAnimationType, flyout: Flyout
    ) -> "FlyoutAnimationManager":
        if aniType not in cls.managers:
            raise ValueError(f"`{aniType}` is an invalid animation type.")
        return cls.managers[aniType](flyout)


@FlyoutAnimationManager.register(FlyoutAnimationType.PULL_UP)
class PullUpFlyoutAnimationManager(FlyoutAnimationManager):
    """向上弹出的动画管理器"""

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint())
        x = pos.x() + target.width() // 2 - w.sizeHint().width() // 2
        y = pos.y() - w.sizeHint().height() + w.layout().contentsMargins().bottom()
        return QPoint(x, y)

    def exec(self, pos: QPoint):
        pos = self._adjustPosition(pos)
        self.slideAni.setStartValue(pos + QPoint(0, 8))
        self.slideAni.setEndValue(pos)
        self.aniGroup.start()
