# coding: utf-8
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
    """
    自定义滑块组件，支持悬停、按压、错误状态动画，以及滑动值映射。
    内部滑块移动范围为 0-266，发射的信号值被线性映射到 0-300。
    """

    resultSignal = Signal(int)  # 滑块释放时发送最终值（映射后）
    verificationFailed = Signal()  # 验证失败信号（可自定义触发时机）
    valueChanged = Signal(int)  # 值变化时发送映射后的值
    sliderPressed = Signal()  # 滑块按下
    sliderReleased = Signal()  # 滑块释放

    # 状态颜色定义
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
        self.maximum = 300  # 名义最大值，实际鼠标限制为 266

        self.grooveRect = QRect(1, 1, 300, 32)
        self.sliderRect = QRect(1, 1, 32, 32)

        # 动画颜色变量
        self._sliderPenColor = self.NORMAL_PEN
        self._sliderBrushColor = self.NORMAL_BRUSH

        self._groovePenColor = self.NORMAL_GROOVE_PEN
        self._grooveBrushColor = self.NORMAL_GROOVE_BRUSH

        self.arrowColor = QColor(100, 106, 116)

        # 创建颜色动画
        self.penColorAnimation = QPropertyAnimation(self, b"sliderPenColor")
        self.penColorAnimation.setDuration(200)
        self.penColorAnimation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.brushColorAnimation = QPropertyAnimation(self, b"sliderBrushColor")
        self.brushColorAnimation.setDuration(200)
        self.brushColorAnimation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 机器人识别相关属性
        self.moveTrack = []  # 记录滑动轨迹 (x, time)
        self.startTime = 0  # 开始时间
        self.endTime = 0  # 结束时间
        self.isBot = False  # 是否为机器人

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
        """根据当前状态启动颜色过渡动画"""
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
                self.isSuccess = False  # 错误时清除成功状态
            self._updateStateColors()

    def setSuccess(self, success=True):
        if self.isSuccess != success:
            self.isSuccess = success
            if success:
                # 清除可能冲突的状态
                self.isPressed = False
                self.isHover = False
                self.isError = False  # 成功时清除错误状态
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
                # 开始记录轨迹和时间
                self.startTime = time.time()
                self.moveTrack = [(event.position().x(), time.time())]
        super(VerificationSlider, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.isSuccess or self.isError:
            return
        if event.button() == Qt.MouseButton.LeftButton and self.isPressed:
            self.isPressed = False

            # 结束时间记录
            self.endTime = time.time()

            # 进行行为分析
            is_human = self.analyzeBehavior()

            if not is_human:
                # 可能是机器人，触发验证失败
                self.setError(True)
                self.verificationFailed.emit()
                self.resetAnimation()
            else:
                # 可能是人类，发送验证结果
                self.resultSignal.emit(self._value * 300 // 266)  # 映射后发送
                self.sliderReleased.emit()
                self._updateStateColors()
                if not self.isSuccess:
                    self.resetAnimation()

            # 重置轨迹记录，为下一次验证做准备
            self.moveTrack = []
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
            # 将鼠标位置映射到 0~266 范围（滑块实际移动范围）
            new_x = max(
                16,
                min(
                    event.position().x() - self.grooveRect.left(),
                    self.grooveRect.width() - 18,
                ),
            )
            new_x -= 16
            self.setValue(int(new_x))
            # 记录滑动轨迹
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
        """设置内部值（0-266），并发射映射后的值（0-300）"""
        self._value = max(self.minimum, min(self.maximum, value))
        self.update()
        # 映射：内部 0-266  -> 外部 0-300
        mapped_value = int(self._value * 300.0 / 266.0)
        self.valueChanged.emit(mapped_value)

    value = Property(int, getValue, setValue)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制滑槽
        painter.setBrush(QColor(247, 249, 250))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.grooveRect, 5, 5)

        # 绘制已填充部分（用蓝色表示已滑动区域）
        if self._value > 0:
            filled_width = self._value
            filled_rect = self.grooveRect.adjusted(
                0, 0, filled_width - self.grooveRect.width() + 5, 0
            )
            painter.setPen(QPen(self._groovePenColor, 1))
            painter.setBrush(self._grooveBrushColor)
            painter.drawRoundedRect(filled_rect, 3, 3)

        # 绘制滑块
        painter.setPen(QPen(self._sliderPenColor, 1))
        painter.setBrush(self._sliderBrushColor)
        self.sliderRect = QRect(1 + self._value, 1, 32, 32)
        painter.drawRoundedRect(self.sliderRect, 3, 3)
        if not self.sliderRect.isNull() and not self.isError and not self.isSuccess:
            # 获取滑块中心点
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

            # 绘制两条线段组成对号
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

        # 重置机器人状态
        self.isBot = False
        track = self.moveTrack

        # 1. 基本有效性检查
        if len(track) < 15:  # 要求至少10个采样点
            self.isBot = True
            return False

        # 提取坐标和时间序列
        xs = [p[0] for p in track]
        ts = [p[1] for p in track]
        start_time = ts[0]
        end_time = ts[-1]
        total_time = end_time - start_time

        # 总距离（水平位移绝对值）
        total_distance = abs(xs[-1] - xs[0])
        if total_distance < 5:  # 几乎没动
            self.isBot = True
            return False

        # 2. 时间合理性检查（人类滑动一般不会极快或极慢）
        if total_time < 0.3 or total_time > 5.0:
            self.isBot = True
            return False

        # 3. 回退检测：只要出现一次x减小，直接判定为机器人
        backward_moves = 0
        for i in range(1, len(xs)):
            if xs[i] < xs[i - 1]:
                backward_moves += 1
        if backward_moves > 0:
            self.isBot = True
            print("检测到回退滑动，判定为机器人")
            return False

        # 4. 计算速度序列 (像素/秒)
        speeds = []
        for i in range(1, len(track)):
            dt = ts[i] - ts[i - 1]
            if dt > 0:
                dx = abs(xs[i] - xs[i - 1])
                speeds.append(dx / dt)
            else:
                speeds.append(0)

        # 5. 计算加速度序列 (像素/秒²)
        accelerations = []
        for i in range(1, len(speeds)):
            dt = ts[i] - ts[i - 1]
            if dt > 0:
                acc = (speeds[i] - speeds[i - 1]) / dt
                accelerations.append(acc)
            else:
                accelerations.append(0)

        # 6. 计算加加速度 (jerk) 序列 (像素/秒³)
        jerks = []
        for i in range(1, len(accelerations)):
            dt = ts[i + 1] - ts[i]
            if dt > 0:
                jerk = (accelerations[i] - accelerations[i - 1]) / dt
                jerks.append(jerk)
            else:
                jerks.append(0)

        # 7. 统计特征
        avg_speed = total_distance / total_time if total_time > 0 else 0
        max_speed = max(speeds) if speeds else 0
        min_speed = min(speeds) if speeds else 0

        # 速度标准差
        if len(speeds) > 1:
            speed_mean = sum(speeds) / len(speeds)
            speed_var = sum((s - speed_mean) ** 2 for s in speeds) / (len(speeds) - 1)
            speed_std = sqrt(speed_var) if speed_var > 0 else 0
        else:
            speed_std = 0

        # 加速度标准差
        if len(accelerations) > 1:
            acc_mean = sum(accelerations) / len(accelerations)
            acc_var = sum((a - acc_mean) ** 2 for a in accelerations) / (
                len(accelerations) - 1
            )
            acc_std = sqrt(acc_var) if acc_var > 0 else 0
        else:
            acc_std = 0

        # 加加速度标准差
        if len(jerks) > 1:
            jerk_mean = sum(jerks) / len(jerks)
            jerk_var = sum((j - jerk_mean) ** 2 for j in jerks) / (len(jerks) - 1)
            jerk_std = sqrt(jerk_var) if jerk_var > 0 else 0
        else:
            jerk_std = 0

        # 8. 速度突变次数
        speed_changes = [abs(speeds[i] - speeds[i - 1]) for i in range(1, len(speeds))]
        abrupt_changes = sum(1 for change in speed_changes if change > avg_speed * 0.5)

        # 9. 停顿检测
        pauses = 0
        for i in range(1, len(track)):
            dt = ts[i] - ts[i - 1]
            dx = abs(xs[i] - xs[i - 1])
            if dt > 0.1 and dx < 2:
                pauses += 1

        # 10. 轨迹弯曲度
        if total_distance > 0:
            deviations = []
            for i, x in enumerate(xs):
                t_ratio = (ts[i] - start_time) / total_time if total_time > 0 else 0
                expected_x = xs[0] + (xs[-1] - xs[0]) * t_ratio
                dev = abs(x - expected_x)
                deviations.append(dev)
            avg_deviation = sum(deviations) / len(deviations)
            max_deviation = max(deviations)
        else:
            avg_deviation = 0
            max_deviation = 0

        # 11. 动态阈值
        speed_std_threshold = 10 + total_distance / 50
        acc_std_threshold = 50 + total_distance / 10
        jerk_std_threshold = 200 + total_distance / 5
        pause_threshold = 1 + total_distance / 100
        avg_dev_threshold = 2 + total_distance / 30

        # 12. 综合决策（回退已在前面直接返回，这里仅作为额外检查）
        reasons = []
        if speed_std < speed_std_threshold:
            reasons.append(
                f"速度变化太小 (std={speed_std:.2f} < {speed_std_threshold:.2f})"
            )
        if acc_std < acc_std_threshold:
            reasons.append(
                f"加速度变化太小 (std={acc_std:.2f} < {acc_std_threshold:.2f})"
            )
        if jerk_std < jerk_std_threshold:
            reasons.append(
                f"加加速度变化太小 (std={jerk_std:.2f} < {jerk_std_threshold:.2f})"
            )
        if pauses < pause_threshold:
            reasons.append(f"停顿次数太少 ({pauses} < {pause_threshold:.2f})")
        if avg_deviation < avg_dev_threshold:
            reasons.append(
                f"轨迹过于平直 (平均偏离 {avg_deviation:.2f} < {avg_dev_threshold:.2f})"
            )
        if abrupt_changes < 2:
            reasons.append(f"速度突变太少 ({abrupt_changes} < 2)")

        if len(reasons) >= 3:
            self.isBot = True
            print("机器人判定原因:", reasons)
            return False

        # 额外检查：极速直线滑动
        if total_time < 0.8 and avg_deviation < 1 and speed_std < 5:
            self.isBot = True
            print("极速直线滑动，判定为机器人")
            return False

        return True
