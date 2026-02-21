import sys
import time
import random
from random import randint
from math import sqrt
from typing import List, Optional

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QSlider,
    QStyle,
    QStyleOptionSlider,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    Signal,
    QPoint,
    QSize,
    QRectF,
    QRect,
    Property,
    QUrl,
    QByteArray,
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QPainterPath
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class VerificationImage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.imageList = imageList  # 保留本地图片列表作为备选

        self._width = 300
        self._height = 169
        self.setFixedSize(self._width, self._height)

        # 初始化网络管理器
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.on_image_downloaded)

        # 当前显示的图片（默认灰色）
        self.currentImage = QPixmap(self._width, self._height)
        self.currentImage.fill(QColor(200, 200, 200))

        self.pixmapX = randint(50, self._width - 35 - 1)
        self.pixmapY = randint(40, self._height - 35 - 1)
        self._moveX = 1

        # 加载状态标志
        self.loading = True

        # 自动从网络加载图片（若需要）
        self.load_image_from_url("https://api.elaina.cat/random/pc")

    def load_image_from_url(self, url: str):
        """异步从指定URL下载图片"""
        self.loading = True  # 开始加载
        self.update()  # 立即显示“加载中”
        request = QNetworkRequest(QUrl(url))
        self.network_manager.get(request)

    def on_image_downloaded(self, reply: QNetworkReply):
        """网络请求完成后的槽函数"""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            print(f"网络错误: {reply.errorString()}，使用本地图片备选")
            self.fallback_to_local_image()
        else:
            # 读取返回的数据
            data = reply.readAll()
            pixmap = QPixmap()
            if not pixmap.loadFromData(data):
                print("图片数据解析失败，使用本地图片备选")
                self.fallback_to_local_image()
            else:
                # 成功加载图片，缩放至合适大小
                self.currentImage = pixmap.scaled(
                    self._width,
                    self._height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                # 重新生成随机缺口位置
                self.pixmapX = randint(50, self._width - 35 - 1)
                self.pixmapY = randint(40, self._height - 35 - 1)
                self.loading = False  # 加载完成
                self.update()  # 触发重绘

        reply.deleteLater()

    def fallback_to_local_image(self):
        """当网络加载失败时，从本地列表随机选图"""
        self.currentImage.fill(QColor(200, 200, 200))
        # 仍然随机生成缺口位置
        self.pixmapX = randint(50, self._width - 35 - 1)
        self.pixmapY = randint(40, self._height - 35 - 1)
        self.loading = False  # 加载失败也视为结束
        self.update()

    def paintEvent(self, event):
        # 原有绘图代码保持不变
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制底图（带圆角裁剪）
        path = QPainterPath()
        rect = QRectF(0, 0, self._width, self._height)
        path.addRoundedRect(rect, 5, 5)
        painter.setClipPath(path)
        painter.drawPixmap(QPoint(0, 0), self.currentImage)

        # 绘制缺口阴影
        shadowPixmap = self.currentImage.copy(self.pixmapX, self.pixmapY, 35, 35)
        shadowPainter = QPainter(shadowPixmap)
        shadowPainter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceAtop
        )
        shadowPainter.fillRect(shadowPixmap.rect(), QColor(0, 0, 0, 150))
        shadowPainter.end()
        painter.drawPixmap(QPoint(self.pixmapX, self.pixmapY), shadowPixmap)

        # 绘制滑块图片
        movePixmap = self.currentImage.copy(self.pixmapX, self.pixmapY, 35, 35)
        movePainter = QPainter(movePixmap)
        movePainter.setPen(QPen(QColor(255, 255, 255), 2))
        movePainter.setBrush(Qt.BrushStyle.NoBrush)
        movePainter.drawRect(0, 0, 34, 34)
        movePainter.end()
        painter.drawPixmap(QPoint(self._moveX, self.pixmapY), movePixmap)

        # 如果正在加载，在最上层绘制加载提示
        if self.loading:
            painter.save()
            # 半透明黑色遮罩
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, self._width, self._height, 5, 5)
            # 白色加载文字
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Microsoft YaHei", 16)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "加载中...")
            painter.restore()

        super().paintEvent(event)

    def setMoveX(self, mapped_value):
        internal_value = int(mapped_value * 266 / 300)
        self._moveX = 1 + internal_value
        self.update()

    def getMoveX(self):
        return self._moveX

    def getCorrectValue(self):
        return self.pixmapX

    value = Property(int, getMoveX, setMoveX)

    def resetAnimation(self):
        """滑块释放后自动滑回起点的动画"""
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(800)
        self.animation.setStartValue(self._moveX)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuint)
        self.animation.start()

    def refresh_image(self):
        """刷新图片（重新从网络加载）"""
        if (
            hasattr(self, "animation")
            and self.animation.state() == QPropertyAnimation.State.Running
        ):
            self.animation.stop()
            self.animation.deleteLater()
            delattr(self, "animation")

        # 重新从网络加载
        self.load_image_from_url("https://api.elaina.cat/random/pc")


# 简单的测试代码（可移除）
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建一个窗口放置 VerificationImage 和一个刷新按钮
    window = QWidget()
    window.setWindowTitle("验证码图片加载测试")
    layout = QVBoxLayout(window)

    v_image = VerificationImage()
    layout.addWidget(v_image)

    # 刷新按钮（用于测试重新加载）
    from PySide6.QtWidgets import QPushButton

    btn_refresh = QPushButton("刷新图片")
    btn_refresh.clicked.connect(v_image.refresh_image)
    layout.addWidget(btn_refresh)

    window.show()
    sys.exit(app.exec())
