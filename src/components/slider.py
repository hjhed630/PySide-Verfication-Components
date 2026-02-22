
import time
from math import sqrt
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    Signal,
    QRect,
    Property,
    QTimer,
    QPoint,
    QPointF,
)
from PySide6.QtGui import QPainter, QColor, QPen


class VerificationSlider(QWidget):
    

    resultSignal = Signal(dict)
    valueChanged = Signal(int)  
    sliderPressed = Signal()  
    sliderReleased = Signal()  

    NORMAL_PEN = QColor(201, 204, 207)
    NORMAL_BRUSH = QColor(255, 255, 255)
    HOVER_PEN = QColor(25, 145, 250)
    HOVER_BRUSH = QColor(255, 255, 255)
    PRESSED_PEN = QColor(25, 145, 250)
    PRESSED_BRUSH = QColor(25, 145, 250)
    ERROR_PEN = QColor(245, 122, 122)
    ERROR_BRUSH = QColor(245, 122, 122)
    SUCCESS_PEN = QColor(82, 204, 186)
    SUCCESS_BRUSH = QColor(82, 204, 186)

    NORMAL_GROOVE_PEN = QColor(25, 145, 250)
    NORMAL_GROOVE_BRUSH = QColor(209, 232, 254)
    SUCCESS_GROOVE_PEN = QColor(117, 212, 199)
    SUCCESS_GROOVE_BRUSH = QColor(210, 244, 239)
    ERROR_GROOVE_PEN = QColor(245, 122, 122)
    ERROR_GROOVE_BRUSH = QColor(252, 225, 225)

    def __init__(self, parent=None):
        super(VerificationSlider, self).__init__(parent)
        self.setFixedSize(300, 40)
        self.setMouseTracking(True)

        self.isPressed = False
        self.isHover = False
        self.isError = False
        self.isSuccess = False
        self._value = 0

        self.minimum = 0
        self.maximum = 300

        self.grooveRect = QRect(1, 1, 300, 32)
        self.sliderRect = QRect(1, 1, 32, 32)

        self._sliderPenColor = self.NORMAL_PEN
        self._sliderBrushColor = self.NORMAL_BRUSH

        self._groovePenColor = self.NORMAL_GROOVE_PEN
        self._grooveBrushColor = self.NORMAL_GROOVE_BRUSH

        self.arrowColor = QColor(100, 106, 116)

        self.penColorAnimation = QPropertyAnimation(self, b"sliderPenColor")
        self.penColorAnimation.setDuration(200)
        self.penColorAnimation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.brushColorAnimation = QPropertyAnimation(self, b"sliderBrushColor")
        self.brushColorAnimation.setDuration(200)
        self.brushColorAnimation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.moveTrack = []  
        self.startTime = 0  
        self.endTime = 0  
        self.isBot = False  

        self.resultDict = {"result": True, "value": 0, "endTime": 0, "msg": []}

    def getSliderPenColor(self):
        return self._sliderPenColor

    def setSliderPenColor(self, color):
        self._sliderPenColor = color
        self.update()

    sliderPenColor = Property(QColor, getSliderPenColor, setSliderPenColor)

    def getSliderBrushColor(self):
        return self._sliderBrushColor

    def setSliderBrushColor(self, color):
        self._sliderBrushColor = color
        self.update()

    sliderBrushColor = Property(QColor, getSliderBrushColor, setSliderBrushColor)

    def _updateStateColors(self):

        self.penColorAnimation.stop()
        self.brushColorAnimation.stop()

        if self.isError:
            target_pen = self.ERROR_PEN
            target_brush = self.ERROR_BRUSH
            self._groovePenColor = self.ERROR_GROOVE_PEN
            self._grooveBrushColor = self.ERROR_GROOVE_BRUSH
            self.arrowColor = QColor(255, 255, 255)
        elif self.isPressed:
            target_pen = self.PRESSED_PEN
            target_brush = self.PRESSED_BRUSH
            self.arrowColor = QColor(255, 255, 255)
        elif self.isHover:
            target_pen = self.HOVER_PEN
            target_brush = self.HOVER_BRUSH
            self.arrowColor = QColor(100, 106, 116)
        elif self.isSuccess:
            self.isHover = False
            self.isPressed = False
            target_pen = self.SUCCESS_PEN
            target_brush = self.SUCCESS_BRUSH
            self._groovePenColor = self.SUCCESS_GROOVE_PEN
            self._grooveBrushColor = self.SUCCESS_GROOVE_BRUSH
            self.arrowColor = QColor(255, 255, 255)
        else:
            target_pen = self.NORMAL_PEN
            target_brush = self.NORMAL_BRUSH
            self._groovePenColor = self.NORMAL_GROOVE_PEN
            self._grooveBrushColor = self.NORMAL_GROOVE_BRUSH
            self.arrowColor = QColor(100, 106, 116)

        self.penColorAnimation.setStartValue(self._sliderPenColor)
        self.penColorAnimation.setEndValue(target_pen)
        self.brushColorAnimation.setStartValue(self._sliderBrushColor)
        self.brushColorAnimation.setEndValue(target_brush)

        self.penColorAnimation.start()
        self.brushColorAnimation.start()

    def setError(self, error=True):
        if self.isError != error:
            self.isError = error
            if error:
                self.isSuccess = False
            self._updateStateColors()

    def setSuccess(self, success=True):
        if self.isSuccess != success:
            self.isSuccess = success
            if success:

                self.isPressed = False
                self.isHover = False
                self.isError = False
            self._updateStateColors()

    def mousePressEvent(self, event):
        if self.isSuccess or self.isError:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            handleX = self.grooveRect.left() + self._value
            handleX = max(
                self.grooveRect.left() + 1,
                min(handleX, self.grooveRect.right() - 32 + 1),
            )
            handleRect = QRect(int(handleX), 0, 32, 32)
            if handleRect.contains(event.position().toPoint()):
                self.isPressed = True
                self._updateStateColors()
                self.sliderPressed.emit()

                self.startTime = time.time()
                self.moveTrack = [(event.position().x(), time.time())]
        super(VerificationSlider, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.isSuccess or self.isError:
            return
        if event.button() == Qt.MouseButton.LeftButton and self.isPressed:
            self.isPressed = False

            self.endTime = time.time()

            self.analyzeBehavior()
            self.moveTrack = []

            self.sliderReleased.emit()
            self._updateStateColors()
            if not self.isSuccess:
                self.resetAnimation()

        super(VerificationSlider, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.isSuccess or self.isError:
            return
        handleX = self.grooveRect.left() + self._value
        handleX = max(
            self.grooveRect.left(), min(handleX, self.grooveRect.right() - 32)
        )
        handleRect = QRect(int(handleX), 0, 32, 32)

        if self.isPressed:
            new_x = max(
                16,
                min(
                    event.position().x() - self.grooveRect.left(),
                    self.grooveRect.width() - 18,
                ),
            )
            new_x -= 16
            self.setValue(int(new_x))
            self.moveTrack.append((event.position().x(), time.time()))
        else:
            hover = handleRect.contains(event.position().toPoint())
            if hover != self.isHover:
                self.isHover = hover
                self._updateStateColors()
        super(VerificationSlider, self).mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self.isSuccess or self.isError:
            return
        if self.isHover:
            self.isHover = False
            self._updateStateColors()
        super(VerificationSlider, self).leaveEvent(event)

    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = max(self.minimum, min(self.maximum, value))
        self.update()
        mapped_value = int(self._value * 300.0 / 266.0)
        self.valueChanged.emit(mapped_value)

    value = Property(int, getValue, setValue)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(247, 249, 250))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.grooveRect, 5, 5)

        if self._value > 0:
            filled_width = self._value
            filled_rect = self.grooveRect.adjusted(
                0, 0, filled_width - self.grooveRect.width() + 5, 0
            )
            painter.setPen(QPen(self._groovePenColor, 1))
            painter.setBrush(self._grooveBrushColor)
            painter.drawRoundedRect(filled_rect, 3, 3)

        painter.setPen(QPen(self._sliderPenColor, 1))
        painter.setBrush(self._sliderBrushColor)
        self.sliderRect = QRect(1 + self._value, 1, 32, 32)
        painter.drawRoundedRect(self.sliderRect, 3, 3)
        if not self.sliderRect.isNull() and not self.isError and not self.isSuccess:

            center = self.sliderRect.center()

            arrow_length = 9
            shaft_length = 9
            shaft_width = 1.7
            head_length = 3

            shaft_start_x = center.x() - arrow_length // 2.5
            shaft_end_x = shaft_start_x + shaft_length
            shaft_y = center.y()

            arrow_color = self.arrowColor
            painter.setPen(QPen(arrow_color, shaft_width, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)

            painter.drawLine(
                QPointF(shaft_start_x, shaft_y), QPointF(shaft_end_x, shaft_y)
            )
            painter.drawLine(
                QPointF(shaft_end_x, shaft_y),
                QPointF(shaft_end_x - head_length, shaft_y - head_length),
            )
            painter.drawLine(
                QPointF(shaft_end_x, shaft_y),
                QPointF(shaft_end_x - head_length, shaft_y + head_length),
            )

        if not self.sliderRect.isNull() and self.isError:
            center = self.sliderRect.center()

            cross_size = 4
            line_width = 1.7

            cross_color = QColor(255, 255, 255)
            painter.setPen(QPen(cross_color, line_width, Qt.SolidLine, Qt.RoundCap))

            painter.drawLine(
                center.x() - cross_size + 1,
                center.y() - cross_size,
                center.x() + cross_size + 1,
                center.y() + cross_size,
            )

            painter.drawLine(
                center.x() - cross_size + 1,
                center.y() + cross_size,
                center.x() + cross_size + 1,
                center.y() - cross_size,
            )
        if not self.sliderRect.isNull() and self.isSuccess:
            center = self.sliderRect.center()
            line_width = 1.7

            check_color = QColor(255, 255, 255)
            painter.setPen(QPen(check_color, line_width, Qt.SolidLine, Qt.RoundCap))

            p1 = QPointF(center.x() - 3.5, center.y() - 0.5)
            p2 = QPointF(center.x(), center.y() + 3)
            p3 = QPointF(center.x() + 6.3, center.y() - 3)

            
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)

    def resetAnimation(self):
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(800)
        self.animation.setStartValue(self._value)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuint)
        self.animation.start()
        QTimer.singleShot(900, lambda: self.setError(False))
        QTimer.singleShot(905, self._setHoverFalse)

    def _setHoverFalse(self):
        self.isHover = False

    def analyzeBehavior(self):

        self.isBot = False
        track = self.moveTrack

        if len(track) < 15:
            self.isBot = True
            self.resultDict["result"] = False
            self.resultDict["msg"] = "滑动轨迹过短"
            self.resultSignal.emit(self.resultDict)
            return False

        xs = [p[0] for p in track]
        ts = [p[1] for p in track]
        start_time = ts[0]
        end_time = ts[-1]
        total_time = end_time - start_time

        total_distance = abs(xs[-1] - xs[0])
        if total_distance < 5:
            self.isBot = True
            self.resultDict["result"] = False
            self.resultDict["msg"] = "滑动距离过短"
            self.resultSignal.emit(self.resultDict)
            return False

        if total_time < 0.3 or total_time > 5.0:
            self.isBot = True
            self.resultDict["result"] = False
            self.resultDict["msg"] = "滑动时间异常"
            self.resultSignal.emit(self.resultDict)
            return False

        backward_moves = 0
        for i in range(1, len(xs)):
            if xs[i] < xs[i - 1]:
                backward_moves += 1
        if backward_moves > 0:
            self.isBot = True

            self.resultDict["result"] = False
            self.resultDict["msg"] = ["回退滑动异常"]
            self.resultSignal.emit(self.resultDict)

        speeds = []
        for i in range(1, len(track)):
            dt = ts[i] - ts[i - 1]
            if dt > 0:
                dx = abs(xs[i] - xs[i - 1])
                speeds.append(dx / dt)
            else:
                speeds.append(0)

        accelerations = []
        for i in range(1, len(speeds)):
            dt = ts[i] - ts[i - 1]
            if dt > 0:
                acc = (speeds[i] - speeds[i - 1]) / dt
                accelerations.append(acc)
            else:
                accelerations.append(0)

        jerks = []
        for i in range(1, len(accelerations)):
            dt = ts[i + 1] - ts[i]
            if dt > 0:
                jerk = (accelerations[i] - accelerations[i - 1]) / dt
                jerks.append(jerk)
            else:
                jerks.append(0)

        avg_speed = total_distance / total_time if total_time > 0 else 0

        if len(speeds) > 1:
            speed_mean = sum(speeds) / len(speeds)
            speed_var = sum((s - speed_mean) ** 2 for s in speeds) / (len(speeds) - 1)
            speed_std = sqrt(speed_var) if speed_var > 0 else 0
        else:
            speed_std = 0

        if len(accelerations) > 1:
            acc_mean = sum(accelerations) / len(accelerations)
            acc_var = sum((a - acc_mean) ** 2 for a in accelerations) / (
                len(accelerations) - 1
            )
            acc_std = sqrt(acc_var) if acc_var > 0 else 0
        else:
            acc_std = 0

        if len(jerks) > 1:
            jerk_mean = sum(jerks) / len(jerks)
            jerk_var = sum((j - jerk_mean) ** 2 for j in jerks) / (len(jerks) - 1)
            jerk_std = sqrt(jerk_var) if jerk_var > 0 else 0
        else:
            jerk_std = 0

        speed_changes = [abs(speeds[i] - speeds[i - 1]) for i in range(1, len(speeds))]
        abrupt_changes = sum(1 for change in speed_changes if change > avg_speed * 0.5)

        pauses = 0
        for i in range(1, len(track)):
            dt = ts[i] - ts[i - 1]
            dx = abs(xs[i] - xs[i - 1])
            if dt > 0.1 and dx < 2:
                pauses += 1

        if total_distance > 0:
            deviations = []
            for i, x in enumerate(xs):
                t_ratio = (ts[i] - start_time) / total_time if total_time > 0 else 0
                expected_x = xs[0] + (xs[-1] - xs[0]) * t_ratio
                dev = abs(x - expected_x)
                deviations.append(dev)
            avg_deviation = sum(deviations) / len(deviations)
        else:
            avg_deviation = 0

        speed_std_threshold = 10 + total_distance / 50
        acc_std_threshold = 50 + total_distance / 10
        jerk_std_threshold = 200 + total_distance / 5
        pause_threshold = 1 + total_distance / 100
        avg_dev_threshold = 2 + total_distance / 30

        reasons = []
        if speed_std < speed_std_threshold:
            reasons.append(f"速度变化异常")
        if acc_std < acc_std_threshold:
            reasons.append(f"加速度变化异常")
        if jerk_std < jerk_std_threshold:
            reasons.append(f"加加速度变化异常")
        if pauses < pause_threshold:
            reasons.append(f"停顿次数异常")
        if avg_deviation < avg_dev_threshold:
            reasons.append(f"轨迹异常")
        if abrupt_changes < 2:
            reasons.append(f"速度突变异常")

        if len(reasons) >= 3:
            self.isBot = True

            self.resultDict["result"] = False
            self.resultDict["msg"] = reasons

            self.resultSignal.emit(self.resultDict)

        
        if total_time < 0.8 and avg_deviation < 1 and speed_std < 5:
            self.isBot = True

            self.resultDict["result"] = False
            self.resultDict["msg"] = "极速滑动异常"

            self.resultSignal.emit(self.resultDict)

        
        if not self.isBot:
            self.resultDict["result"] = True
            self.resultDict["value"] = self._value * 300 // 266
            self.resultDict["endTime"] = self.endTime
            self.resultDict["msg"] = ""
            self.resultSignal.emit(self.resultDict)
        return True
