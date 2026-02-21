from typing import Union

from PySide6.QtCore import Qt, Property, Signal, QSize
from PySide6.QtGui import (
    QPainter,
    QPixmap,
    QImage,
    QPainterPath,
    QImageReader,
    QMovie,
)
from PySide6.QtWidgets import QLabel, QWidget


class ImageLabel(QLabel):
    clicked = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.image = QImage()
        self.setBorderRadius(0, 0, 0, 0)
        self._postInit()

    def _postInit(self):
        pass

    def _onFrameChanged(self, index: int):
        self.image = self.movie().currentImage()
        self.update()

    def setBorderRadius(
        self, topLeft: int, topRight: int, bottomLeft: int, bottomRight: int
    ):
        self._topLeftRadius = topLeft
        self._topRightRadius = topRight
        self._bottomLeftRadius = bottomLeft
        self._bottomRightRadius = bottomRight
        self.update()

    def setImage(self, image: Union[str, QPixmap, QImage] = None):
        self.image = image or QImage()

        if isinstance(image, str):
            reader = QImageReader(image)
            if reader.supportsAnimation():
                self.setMovie(QMovie(image))
            else:
                self.image = reader.read()
        elif isinstance(image, QPixmap):
            self.image = image.toImage()

        self.setFixedSize(self.image.size())
        self.update()

    def scaledToWidth(self, width: int):
        if self.isNull():
            return

        h = int(width / self.image.width() * self.image.height())
        self.setFixedSize(width, h)

        if self.movie():
            self.movie().setScaledSize(QSize(width, h))

    def scaledToHeight(self, height: int):
        if self.isNull():
            return

        w = int(height / self.image.height() * self.image.width())
        self.setFixedSize(w, height)

        if self.movie():
            self.movie().setScaledSize(QSize(w, height))

    def setScaledSize(self, size: QSize):
        if self.isNull():
            return

        self.setFixedSize(size)

        if self.movie():
            self.movie().setScaledSize(size)

    def isNull(self):
        return self.image.isNull()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setPixmap(self, pixmap: QPixmap):
        self.setImage(pixmap)

    def pixmap(self) -> QPixmap:
        return QPixmap.fromImage(self.image)

    def setMovie(self, movie: QMovie):
        super().setMovie(movie)
        self.movie().start()
        self.image = self.movie().currentImage()
        self.movie().frameChanged.connect(self._onFrameChanged)

    def paintEvent(self, e):
        if self.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        w, h = self.width(), self.height()
        path.moveTo(self.topLeftRadius, 0)
        path.lineTo(w - self.topRightRadius, 0)
        d = self.topRightRadius * 2
        path.arcTo(w - d, 0, d, d, 90, -90)
        path.lineTo(w, h - self.bottomRightRadius)
        d = self.bottomRightRadius * 2
        path.arcTo(w - d, h - d, d, d, 0, -90)
        path.lineTo(self.bottomLeftRadius, h)
        d = self.bottomLeftRadius * 2
        path.arcTo(0, h - d, d, d, -90, -90)
        path.lineTo(0, self.topLeftRadius)
        d = self.topLeftRadius * 2
        path.arcTo(0, 0, d, d, -180, -90)
        image = self.image.scaled(
            self.size() * self.devicePixelRatioF(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        )
        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)
        painter.drawImage(self.rect(), image)
