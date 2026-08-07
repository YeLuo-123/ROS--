# ROS 双语术语规范

## 使用规则

1. 首次出现写作“中文名称（English term，abbreviation）”；无缩写时省略缩写。
2. 后续优先使用批准的中文名称或通用缩写。
3. 命令、功能包、接口、类名、字段名、文件名和代码标识符保持原文。
4. 同一概念不得在“话题/主题”“功能包/程序包”等译法之间切换。
5. 遇到未收录术语，先查官方资料和主流教材，再加入“待审术语”，不得临时创造译名。

## 核心术语表

| 中文名称 | English term | 缩写/标识 | 统一用法 |
|---|---|---|---|
| 机器人操作系统 | Robot Operating System | ROS | 首次出现写全称 |
| 节点 | node | node | 不译为“结点” |
| 计算图 | computation graph | — | 表示运行时连接关系 |
| 话题 | topic | topic | 不使用“主题” |
| 消息 | message | msg | 与话题区分 |
| 发布者 | publisher | pub | 正文用“发布者” |
| 订阅者 | subscriber | sub | 正文用“订阅者” |
| 服务 | service | srv | 表示请求—响应机制 |
| 动作 | action | action | 表示可反馈、可取消的长任务 |
| 参数 | parameter | param | ROS2参数需说明节点归属 |
| 参数服务器 | parameter server | — | 仅用于适用的ROS1语境 |
| 功能包 | package | package | 不使用“程序包” |
| 工作空间 | workspace | — | 说明catkin或colcon语境 |
| 构建系统 | build system | — | 区分catkin、ament等 |
| 启动文件 | launch file | launch | 保留文件格式差异 |
| 坐标系 | coordinate frame | frame | 不与坐标值混淆 |
| 坐标变换 | transform | TF | 体系名称可直接用TF/TF2 |
| 里程计 | odometry | odom | 注意消息与坐标系差异 |
| 同时定位与建图 | Simultaneous Localization and Mapping | SLAM | 首次写全称 |
| 自主导航 | autonomous navigation | navigation | 区分导航框架名称 |
| 代价地图 | costmap | costmap | 保留软件标识符原文 |
| 运动规划 | motion planning | — | MoveIt语境保持一致 |
| 碰撞检测 | collision detection | — | — |
| 服务质量 | Quality of Service | QoS | ROS2核心术语 |
| 数据分发服务 | Data Distribution Service | DDS | ROS2中首次写全称 |
| 仿真 | simulation | — | 不使用“模拟”代替技术语境 |
| 数字孪生 | digital twin | — | 与一般仿真区分 |

## 待项目确认的写法

- Gazebo不同产品/版本的正式名称必须按所用发行版核实，不笼统互换。
- Navigation Stack、Navigation2/Nav2按ROS版本和项目正式名称书写。
- MoveIt、MoveIt 2按实际技术栈区分。
- TF、tf、tf2、TF2按软件包和概念语境核实后使用。

