# 项目交接文档

## 当前负责人

- 内容总审查：郄龙飞
- 其他教师分工：待确定

## 当前架构

项目由需求与培养方案、教材文档、决策记录、ROS配套源码、自定义Skill、验证记录和输出归档组成。第一册代码按四个递进里程碑保存。

## 已完成

- 三册定位、书名、读者、课程映射和版本策略已经确定。
- 第一册三级目录已经形成。
- TurtleGoal、TurtleGuard、TurtlePainter和TurtleMission ROS 2 Humble Demo已经编写。
- 自定义`ros-textbook-author` Skill已建立并同步主要项目决策。
- 2026版培养方案已纳入需求依据。

## 尚未完成

- 4个Demo尚未在Ubuntu 22.04 + ROS 2 Humble端到端运行。
- 第一册各章正文、习题、Technical English和教师资源尚待编写。
- ROS 1 Noetic关键案例分支尚待编写与验证。
- 第二册和第三册尚未进入完整写作阶段。
- 项目尚未初始化Git及远程GitHub仓库。

## 接手顺序

1. 阅读`00_AI_INDEX.md`和`01_AGENTS.md`。
2. 阅读`30_state/CURRENT_STATUS.md`与`60_decisions/`。
3. 查看第一册目录和4个Demo README。
4. 若准备运行代码，先依据`10_bootstrap/README.md`建立Ubuntu环境。
5. 所有运行结论写入`130_verification/`，不要只在聊天中报告。

## 风险提示

- 参考PDF和ZIP不是项目原创材料，不能直接复制进教材正文或重新授权。
- DOCX渲染页面属于检查输出，不是正式教材图像。
- Demo之间存在依赖：第9章需要第7章`turtle_guard`和第8章`turtle_painter`包。
