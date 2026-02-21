<p align="center">
  <img width="15%" align="center" src="https://img.cdn1.vip/i/6999d326d78b4_1771688742.webp" alt="logo">
</p>
  <h1 align="center">
  PySide-Verification-Components
</h1>
<p align="center">
  The verification components based on PySide could be used to verify mechine
</p>

PyQtVerifySlider 是一个基于 PySide6 开发的滑动验证码组件，用于防止机器人恶意操作，保护应用程序的安全。

## 功能特点

- **自定义绘制**：使用 QPainter 实现的自定义滑块，支持悬停、按压、错误状态动画
- **机器人识别**：通过分析滑动轨迹、速度变化、停顿检测等多维度特征，准确识别机器人操作
- **灵活的验证模式**：支持图片验证码与滑块同步移动，确保验证的安全性
- **可拖动的浮动窗口**：将验证组件封装在可拖动的浮动窗口中，提供更好的用户体验、



# 环境要求

- Python 3.10+
- PySide6 6.4.0+

## 使用示例

### 基本使用

```python
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from src.components import VerificationSlider, VerificationImage, VerificationCard

class DemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("滑动验证码示例")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 创建验证卡片
        self.verification_card = VerificationCard(self)
        self.verification_card.resultSignal.connect(self.on_verification_result)
        self.verification_card.verificationFailed.connect(self.on_verification_failed)
        
        # 创建显示验证按钮
        self.show_verify_btn = QPushButton("显示验证", self)
        self.show_verify_btn.clicked.connect(self.verification_card.show)
        
        layout.addWidget(self.show_verify_btn)
        layout.addWidget(self.verification_card)
        
    def on_verification_result(self, value):
        print(f"验证成功！值: {value}")
        # 这里可以处理验证成功后的逻辑
        
    def on_verification_failed(self):
        print("验证失败！")
        # 这里可以处理验证失败后的逻辑

if __name__ == "__main__":
    app = QApplication([])
    demo = DemoApp()
    demo.show()
    app.exec()
```

## 

## 机器人识别算法

本项目使用了多维度的机器人识别算法，包括：

1. **轨迹分析**：分析滑动轨迹的弯曲度和偏离程度
2. **速度变化**：检测速度的突变和分布情况
3. **停顿检测**：区分长停顿和短停顿，识别异常停顿模式
4. **间隔分析**：检测时间间隔是否过于规律
5. **模式检测**：识别极速直线滑动、匀速滑动、阶梯式滑动等机器人特征

算法会综合这些因素，给出一个加权评分，判断操作是否来自机器人。

## 自定义配置

### 调整机器人识别灵敏度

在 `slider.py` 文件中，您可以调整以下参数来修改机器人识别的灵敏度：

- `len(track) < 8`: 调整采样点要求
- `total_time < 0.3 or total_time > 5.0`: 调整时间范围
- `speed_std_threshold = 8 + total_distance / 50`: 调整速度标准差阈值
- `if len(reasons) >= 4 or total_weight >= 5`: 调整综合判断条件

### 

## 许可证

本项目采用 GPLV3 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request，帮助改进这个项目。
