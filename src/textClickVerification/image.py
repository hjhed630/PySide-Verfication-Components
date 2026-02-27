import sys
import random
from random import randint
from typing import List, Tuple, Optional

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
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
)
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QPen,
    QPainterPath,
    QMouseEvent,
    QBrush,
)


class VerificationImage(QWidget):
    clickSignal = Signal(int, int)
    verificationComplete = Signal(bool, list)

    def __init__(self, imageList: List[QPixmap] = [], parent=None):
        super().__init__(parent=parent)
        self.imageList = imageList

        self._width = 300
        self._height = 169
        self.setFixedSize(self._width, self._height)

        self.characters = "一二三四五六七八九十甲乙丙丁戊己庚辛壬癸"
        self.font_size_range = (20, 35)
        self.font_colors = [
            QColor(0, 0, 0),
            QColor(255, 0, 0),
            QColor(0, 255, 0),
            QColor(0, 0, 255),
            QColor(255, 255, 0),
            QColor(255, 0, 255),
            QColor(0, 255, 255),
        ]

        self.target_chars = []
        self.target_positions = []
        self.user_clicks = []
        self.verification_text = ""

        self.generateImage()

    def generateImage(self):
        self.currentImage = QPixmap(self._width, self._height)
        self.currentImage.fill(QColor(240, 240, 240))

        painter = QPainter(self.currentImage)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        char_positions = []
        displayed_chars = []
        attempts = 0
        max_attempts = 100

        while len(char_positions) < 12 and attempts < max_attempts:
            attempts += 1
            char = random.choice(self.characters)

            if char in displayed_chars:
                continue

            font_size = randint(*self.font_size_range)
            font = QFont("SimHei", font_size)
            painter.setFont(font)

            char_width = painter.boundingRect(
                0, 0, 100, 100, Qt.AlignmentFlag.AlignLeft, char
            ).width()
            char_height = painter.boundingRect(
                0, 0, 100, 100, Qt.AlignmentFlag.AlignTop, char
            ).height()

            x = randint(10, self._width - char_width - 10)
            y = randint(10, self._height - char_height - 10)

            rect = QRect(x, y, char_width, char_height)
            overlap = False
            for existing_rect in char_positions:
                if rect.intersects(existing_rect):
                    overlap = True
                    break

            if not overlap:
                char_positions.append(rect)
                displayed_chars.append(char)
                color = random.choice(self.font_colors)
                painter.setPen(QPen(color))

                painter.save()

                rotation = randint(-15, 15)
                painter.translate(x + char_width / 2, y + char_height / 2)
                painter.rotate(rotation)
                painter.translate(-(x + char_width / 2), -(y + char_height / 2))

                opacity = random.uniform(0.7, 1.0)
                painter.setOpacity(opacity)

                painter.drawText(x, y + char_height - 5, char)

                painter.restore()

        painter.end()

        if char_positions:
            
            target_count = min(3, len(displayed_chars))
            
            self.target_chars = random.sample(displayed_chars, target_count)
            self.target_positions = []

            
            for char in self.target_chars:
                if char in displayed_chars:
                    char_index = displayed_chars.index(char)
                    if char_index < len(char_positions):
                        self.target_positions.append(
                            char_positions[char_index].center()
                        )

            
            if len(self.target_positions) != len(self.target_chars):
                
                self.target_chars = self.target_chars[: len(self.target_positions)]

            self.verification_text = "点击: " + " ".join(self.target_chars)
        else:
            self.target_chars = []
            self.target_positions = []
            self.verification_text = "点击: 无"

        self.user_clicks = []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        rect = QRectF(0, 0, self._width, self._height)
        path.addRoundedRect(rect, 5, 5)
        painter.setClipPath(path)
        painter.drawPixmap(QPoint(0, 0), self.currentImage)

        for i, pos in enumerate(self.user_clicks):
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setBrush(QBrush(QColor(255, 0, 0, 50)))
            painter.drawEllipse(pos, 10, 10)
            painter.drawText(pos.x() + 15, pos.y() + 5, str(i + 1))

        super().paintEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            self.user_clicks.append(pos)
            self.update()

            if len(self.user_clicks) == len(self.target_chars):
                self.verify()

    def verify(self):
        if len(self.user_clicks) != len(self.target_positions):
            self.verificationComplete.emit(False, [])
            return

        tolerance = 20
        correct = []
        for i, (user_pos, target_pos) in enumerate(
            zip(self.user_clicks, self.target_positions)
        ):
            distance = (
                (user_pos.x() - target_pos.x()) ** 2
                + (user_pos.y() - target_pos.y()) ** 2
            ) ** 0.5
            if distance <= tolerance:
                correct.append(i)

        success = len(correct) == len(self.target_chars)
        self.verificationComplete.emit(success, correct)

    def reset(self):
        self.generateImage()

    def refreshImage(self):
        if (
            hasattr(self, "animation")
            and self.animation.state() == QPropertyAnimation.State.Running
        ):
            self.animation.stop()
            self.animation.deleteLater()
            delattr(self, "animation")
        self.generateImage()



if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("文字点选验证码测试")
    layout = QVBoxLayout(window)

    v_image = VerificationImage()
    layout.addWidget(v_image)

    def on_verification_complete(success, correct):
        print(f"验证结果: {'成功' if success else '失败'}")
        print(f"正确点击: {correct}")

    v_image.verificationComplete.connect(on_verification_complete)

    window.show()
    sys.exit(app.exec())
