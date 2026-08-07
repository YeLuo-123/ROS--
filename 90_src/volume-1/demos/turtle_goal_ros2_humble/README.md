# TurtleGoal：ROS 2 Humble自主到达目标点Demo

## 1. 案例目标

让`turtle1`根据目标坐标自主转向和前进，并利用位姿反馈持续修正，最终在允许误差内停止。

闭环结构：

`目标点 → 位姿订阅 → 距离/方向误差 → 速度决策 → 速度发布 → 新位姿`

## 2. 适用环境

- Ubuntu 22.04
- ROS 2 Humble
- Python与`rclpy`
- `turtlesim`
- 构建系统：`ament_python`与`colcon`

代码状态：已完成静态语法检查；当前Windows编写环境未安装ROS 2 Humble，尚未完成Ubuntu 22.04运行验证。

## 3. ROS接口

| 方向 | 名称 | 类型 | 用途 |
|---|---|---|---|
| 订阅 | `/turtle1/pose` | `turtlesim/msg/Pose` | 获取乌龟位姿 |
| 发布 | `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | 发布速度指令 |

## 4. 控制规则

1. 根据当前位置和目标点计算距离误差。
2. 使用`atan2`计算目标方向。
3. 将角度误差归一化到`[-pi, pi]`。
4. 方向误差较大时原地转向。
5. 方向基本正确后向前运动并继续修正方向。
6. 距离小于`distance_tolerance`时发布零速度并停止。

这只是服务ROS通信教学的基础比例控制，不作为移动机器人导航算法。

## 5. 放入工作空间

假设工作空间为`~/turtle_ws`：

```bash
mkdir -p ~/turtle_ws/src
cp -r turtle_goal ~/turtle_ws/src/
cd ~/turtle_ws
source /opt/ros/humble/setup.bash
rosdep install -i --from-path src --rosdistro humble -y
colcon build --packages-select turtle_goal
source install/setup.bash
```

如果没有安装turtlesim：

```bash
sudo apt update
sudo apt install ros-humble-turtlesim
```

## 6. 三终端运行

终端1：

```bash
source /opt/ros/humble/setup.bash
ros2 run turtlesim turtlesim_node
```

终端2：

```bash
source /opt/ros/humble/setup.bash
cd ~/turtle_ws
source install/setup.bash
ros2 run turtle_goal turtle_goal_node --ros-args \
  -p target_x:=8.0 \
  -p target_y:=8.0
```

终端3用于观察：

```bash
source /opt/ros/humble/setup.bash
ros2 node info /turtle_goal_controller
ros2 topic echo /turtle1/pose
```

预期现象：乌龟先调整方向，再向目标点运动；到达后终端显示距离误差和耗时，并发布零速度。

## 7. 运行中修改目标点

节点每个控制周期读取目标参数，因此可以在运行中改变目标：

```bash
ros2 param set /turtle_goal_controller target_x 3.0
ros2 param set /turtle_goal_controller target_y 9.0
```

两个参数是分别设置的。第一次设置后节点可能短暂使用“新x＋旧y”，教材正文应提示这一非原子更新现象。

## 8. 参数文件运行

```bash
ros2 run turtle_goal turtle_goal_node --ros-args \
  --params-file ~/turtle_ws/src/turtle_goal/config/turtle_goal.yaml
```

主要参数：

| 参数 | 默认值 | 含义 |
|---|---:|---|
| `target_x` | 8.0 | 目标x坐标 |
| `target_y` | 8.0 | 目标y坐标 |
| `linear_gain` | 1.0 | 线速度比例系数 |
| `angular_gain` | 4.0 | 角速度比例系数 |
| `max_linear_speed` | 2.0 | 最大线速度 |
| `max_angular_speed` | 2.5 | 最大角速度 |
| `distance_tolerance` | 0.05 | 到达距离阈值 |
| `heading_tolerance` | 0.20 | 允许前进的方向误差，单位rad |
| `control_rate` | 20.0 | 控制频率，单位Hz |

## 9. 可选Launch运行

Launch属于第9章内容，本案例当前阶段不要求学生掌握：

```bash
ros2 launch turtle_goal turtle_goal.launch.py
```

## 10. 验收证据

- `/turtle1/pose`能够持续接收。
- `/turtle1/cmd_vel`能够观察到转向、前进和停止指令。
- 到达目标后距离误差不大于`distance_tolerance`。
- 到达后线速度和角速度均为0。
- 学生能说明Topic名称或消息类型错误时为何不能通信。

## 11. 故障诊断

| 现象 | 可能原因 | 检查方法 |
|---|---|---|
| 节点一直等待位姿 | turtlesim未启动或Topic名称错误 | `ros2 topic list`、`ros2 topic info /turtle1/pose` |
| 乌龟不运动 | Publisher未连接或目标已到达 | `ros2 topic info /turtle1/cmd_vel -v` |
| 乌龟持续旋转 | 角度误差或增益设置不合理 | 查看日志中的`heading_error` |
| 目标被拒绝 | 坐标超出允许范围或参数非有限值 | `ros2 param get`检查目标参数 |
| 到达后仍缓慢移动 | 停止条件或零速度发布错误 | `ros2 topic echo /turtle1/cmd_vel` |

## 12. 提高任务

1. 比较“先转向后前进”和“边走边转”两种规则。
2. 记录不同增益下的到达时间和最大位置误差。
3. 为目标参数增加原子更新服务，解决x、y分别设置的问题。
4. 增加超时失败判定，并说明失败后的安全停止策略。

## 13. 许可

本Demo原创代码建议采用Apache-2.0许可。ROS 2、turtlesim及其依赖保持各自原许可证。
