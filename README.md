# 🤖 5DOF 机械臂上位机控制软件

这是一个桌面应用程序，用于控制、可视化和编程一个五自由度（5DOF）外加一个夹爪的机械臂。本软件采用现代化UI设计，提供实时3D姿态显示、运动学解算、自动化任务编排和键盘实时控制等多种功能。

![](img\main-windows.png)

## 📂 项目结构

```
.
├── main.py                 # 主程序入口，整合所有模块
├── startup.py              # 启动脚本，检查依赖并运行主程序
├── ui_components.py        # UI界面构建模块 (基于ttkbootstrap)
├── kinematics.py           # 运动学计算模块 (正/逆解，基于ikpy)
├── communication.py        # 串口通信模块
├── automation.py           # 自动化任务控制与路径规划模块
├── visualization.py        # 3D可视化模块 (基于matplotlib)
├── font_setup.py           # 跨平台字体设置模块
├── utils.py                # 工具类模块 (设置/日志/文件管理等)
├── config.py               # 全局配置文件 (常量、物理参数、UI设置)
├── robot_settings.json     # (自动生成) 用户设置的本地存储文件
└── /Wearm                  # 本项目的STM32单片机驱动程序目录
    ├── /Core               # 本项目的STM32单片机驱动程序相关源码
    ├── /Drivers            # STM32CubeMX生成文件
    └── Wearm.ioc           # STM32CubeMX项目入口文件
```

## ✨ 功能特性

  - **现代化图形界面**: 基于 `ttkbootstrap` 构建，界面美观，支持多种主题。
  - **实时3D可视化**: 使用 `Matplotlib` 实时渲染机械臂的3D模型，同步显示当前姿态、目标位置和自动化任务路径。
  - **多种控制模式**:
      - **目标位置控制**: 输入末端执行器的目标三维坐标 (X, Y, Z)，程序通过逆运动学自动解算各关节角度。![](img\coordinate-transform.png)
      - **手动角度微调**: 通过滑块精确调整每一个舵机的角度，并实时在3D视图中预览。![](img\manual-adjustment.png)
      - **键盘实时控制**: 启用后可通过键盘的 `W/A/S/D` 等按键对机械臂末端进行增量式移动和旋转，实现直观的遥操作。
  - **运动学核心**:
      - **正运动学**: 根据各关节角度计算末端执行器的空间位置。
      - **逆运动学**: 基于 `IKPy` 库，为给定的目标位置和姿态找到最优的关节角度解。
  - **自动化任务系统**:
      - **任务点编排**: 可视化地添加、编辑和删除“抓取点”和“放置点”来创建复杂的自动化任务序列。![](img\automation.png)
      - **智能路径规划**: 在自动化任务中，控制器会自动规划平滑的运动轨迹（球面插值或避障圆弧），以避免奇异点和不稳定的移动。
      - **任务管理**: 支持将编排好的任务点和相关参数保存为 `.json` 文件，并能随时加载。
  - **可靠的串口通信**: 稳定处理与下位机硬件的串口指令收发，并实时显示连接状态。
  - **高度可配置**:
      - **持久化设置**: 自动保存用户的窗口大小、串口选择、控制参数等设置。
      - **跨平台字体支持**: 内置字体管理器。
  - **模块化代码结构**: 项目代码结构清晰，各功能（UI、运动学、通信、可视化）高度解耦。

## 🛠️ 技术栈

  - **核心语言**: Python 3
  - **GUI框架**: `tkinter` + `ttkbootstrap`
  - **3D可视化**: `matplotlib`
  - **运动学解算**: `ikpy`
  - **串口通信**: `pyserial`
  - **数值计算**: `numpy`

## 🚀 安装与运行

### 1\. 环境要求

  - Python 3.8 或更高版本
  - pip 包管理器

### 2\. 克隆项目

```bash
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
```

### 3\. 安装依赖

项目启动脚本 `startup.py` 会自动检查依赖。您也可以手动安装所有必需的库：

```bash
pip install ttkbootstrap numpy matplotlib pyserial ikpy
```

### 4\. 运行程序

直接运行 `startup.py` 脚本即可启动应用程序。它会先检查依赖，然后加载主程序。

```bash
python startup.py
```

### 核心模块详解

  - **`main.py`**: 负责初始化所有核心组件（UI、运动学、通信等），连接回调函数，并管理应用的生命周期。
  - **`ui_components.py`**: 定义了 `ModernUI` 类，负责构建整个图形用户界面，包括所有窗口、按钮、滑块和标签页的布局与功能。
  - **`kinematics.py`**: 使用 `ikpy` 库创建了机械臂的运动学链，提供了正解（`forward_kinematics`）和逆解（`inverse_kinematics`）的核心计算方法。
  - **`automation.py`**: 实现了自动化任务的逻辑。它管理任务点列表，并通过一个独立线程按步骤执行抓取-放置流程，包含智能路径规划算法。
  - **`visualization.py`**: 封装了 `matplotlib` 的3D绘图功能，负责将机械臂的连杆、关节和任务点实时绘制在UI中。
  - **`config.py`**: 集中存放所有硬编码的参数，如机械臂连杆长度、舵机限制、默认主题、文件名等，方便快速修改和调整。
  - **`utils.py`**: 提供一系列辅助类，如 `SettingsManager` 用于读写JSON配置文件，`LogManager` 用于记录日志，`MessageHelper` 用于显示标准对话框等，增强了代码的复用性。

## 🤝 贡献

欢迎对本项目进行贡献！如果您有任何想法或改进建议，欢迎提交 Pull Request

## 📄 许可

本项目采用 [GPL-3.0 license](LICENSE) 开源许可。