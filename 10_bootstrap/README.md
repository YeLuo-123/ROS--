# 环境初始化与恢复

## 1. 目录职责

记录教材写作环境和ROS代码验证环境的初始化方法。

## 2. AI读取规则

在新电脑恢复项目、安装依赖或准备ROS运行验证前读取。

## 3. 当前环境基线

- Windows写作与静态检查：PowerShell、`D:\Miniconda\envs\py312\python.exe`
- ROS 2验证：Ubuntu 22.04、ROS 2 Humble、Python 3、colcon
- ROS 1迁移验证：Ubuntu 20.04、ROS 1 Noetic、catkin

## 4. 禁止事项

- 不使用WSL、Docker或Dev Container作为教材统一环境。
- 不把Windows静态检查写成ROS运行验证。
- 不在未确认时安装依赖或修改系统环境变量。

## 5. 维护规则

安装方法、依赖版本或验证环境变化时更新，并同步`130_verification/`。
