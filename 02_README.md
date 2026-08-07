# 机器人操作系统与智能机器人开发教材项目

## 项目简介

本项目用于规划、编写、审校和维护三册高校ROS系列教材及其配套代码、教学PPT、实验指导书和项目任务书。

三册教材为：

1. 《机器人操作系统与智能机器人开发——基础篇：ROS核心原理与程序设计》
2. 《机器人操作系统与智能机器人开发——应用篇：建模、感知、规划与控制》
3. 《机器人操作系统与智能机器人开发——项目篇：生产实习、课程设计与竞赛案例》

## 当前重点

当前优先完成第一册。第一册采用TurtleMission单乌龟自主任务系统贯穿，第6至9章分别设置TurtleGoal、TurtleGuard、TurtlePainter和TurtleMission阶段案例。

## 技术基线

- ROS 2 Humble、Ubuntu 22.04、rclpy、colcon
- ROS 1 Noetic、Ubuntu 20.04、rospy、catkin（迁移对照）
- Markdown正文，允许LaTeX
- 原创教材内容CC BY 4.0，原创代码Apache-2.0

## 快速导航

- 最新目录：`50_docs/manuscript/volume-1/第一册三级目录.md`
- 配套Demo：`90_src/volume-1/demos/`
- 当前状态：`30_state/CURRENT_STATUS.md`
- 项目决策：`60_decisions/`
- 自定义Skill：`180_skills/ros-textbook-author/`

## 注意

项目当前尚未建立Git仓库。Windows工作区完成的检查不等同于ROS 2 Humble运行验证。
