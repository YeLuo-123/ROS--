# ADR-002：ROS版本基线

- 状态：已接受

## 决定

ROS 2 Humble为主教学版本，环境为Ubuntu 22.04、rclpy和colcon；ROS 1 Noetic作为历史迁移对照，环境为Ubuntu 20.04、rospy和catkin。

## 影响

不得在缺少实际记录时声明兼容其他ROS 2版本。所有关键案例最终都应有可运行的ROS 1对照实现。
