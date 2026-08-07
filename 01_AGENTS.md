# AI协作规则

## 1. 开始任务前

必须依次读取：

1. `00_AI_INDEX.md`
2. `30_state/CURRENT_STATUS.md`
3. `03_PROJECT_HANDOVER.md`

涉及教材结构、ROS版本、课程映射或贯穿案例时，还必须读取`60_decisions/`。涉及ROS接口时读取`70_contracts/`。

## 2. 本机执行规则

- 所有本机Python任务使用`D:\Miniconda\envs\py312\python.exe`。
- 不自动安装第三方库；先说明缺失库、原因和安装命令，得到确认后再安装。
- 不修改Conda base环境和系统环境变量。
- 优先使用PowerShell。
- 不删除文件。
- 覆盖文件、批量移动、安装软件和修改Git历史前必须获得确认。

## 3. 教材规则

- 保持三册边界和已批准书名。
- 中文正文、英文术语，每章设置Technical English。
- 不使用软件截图；使用文字步骤或原创示意图。
- 正文、代码和第三方材料分别遵守各自许可。
- 未实际运行的代码必须标记“静态审查”或“待验证”。

## 4. 代码规则

- ROS 2主环境为Ubuntu 22.04 + Humble + Python/rclpy。
- ROS 1对照环境为Ubuntu 20.04 + Noetic + Python/rospy。
- 修改接口时同步更新`70_contracts/`、README和验证材料。
- Demo代码放在`90_src/`，生成输出不得混入源码目录。

## 5. 修改完成后

- 更新`30_state/CURRENT_STATUS.md`。
- 有重要变化时更新`05_CHANGELOG.md`。
- 新的重大决策使用ADR记录在`60_decisions/`。
- 记录实际完成、仅静态检查和仍待验证的边界。
