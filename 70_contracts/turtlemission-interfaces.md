# TurtleMission接口契约

## 核心Topic

| 名称 | 类型 | 生产者 | 消费者 |
|---|---|---|---|
| `turtle1/pose` | `turtlesim/msg/Pose` | turtlesim | 控制器、安全守卫、记录器 |
| `turtle_goal/cmd_vel_raw` | `geometry_msgs/msg/Twist` | 目标/绘图控制器 | 安全守卫、记录器 |
| `turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | 安全守卫 | turtlesim、记录器 |
| `turtle_guard/status` | `std_msgs/msg/String` | 安全守卫 | 记录器、观察工具 |
| `mission/status` | `std_msgs/msg/String` | 任务运行器 | 记录器、观察工具 |

## Service

- `turtle_guard/enable`：`std_srvs/srv/SetBool`
- `turtle1/set_pen`：`turtlesim/srv/SetPen`

## Action

- 名称：`turtle_painter/draw_shape`
- 类型：`turtle_painter/action/DrawShape`
- Goal：`shape_name`、`size`、`start_x`、`start_y`、`speed`
- Feedback：`progress`、`current_segment`、`remaining_distance`
- Result：`success`、`total_time`、`position_error`、`message`

## 命名规则

第6至8章Demo可能使用绝对名称；第9章通过Launch重映射为相对名称并放入默认`/mission`命名空间。改变旧接口时必须同时检查第9章重映射。
