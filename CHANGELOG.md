# Changelog

## v0.1.0 (2026-04-03)
- 使用 `uv` 管理库。
- 核心能力加固：在 `mapstory.py` 中补充输入校验与错误处理（event 必填、坐标范围、priority 合法性、limit/范围参数检查），并统一将数据库异常转为可读报错。
- 时间排序增强：新增 `time_month`、`time_day`、`time_sort_bucket` 字段与索引，支持“精确时间 > 模糊时间 > 冲突时间 > 空时间”的稳定排序；对历史数据执行回填。
- 查询行为改进：`list/search` 改为基于时间分桶排序；`search` 支持经纬度区间自动归一化（反向输入自动纠正）。
- 交互体验改进：CLI 与交互模式新增输入/存储/检索/更新失败提示，避免异常直接中断。
- 测试补充：新增 `tests/test_stage_a.py`，覆盖阶段 A 关键路径（必填校验、坐标校验、时间排序、更新时间字段重算、检索区间归一化）。
- 文档与规划更新：移动 `USAGE.md` 到 `docs/`，新增 `docs/plan.md`、`docs/api-proposal.md`、`docs/user-preferences.md`，并更新 README 功能规划条目。
- 工程维护：`.gitignore` 新增 `__pycache__/`，并新增 `uv.lock` 以固定当前依赖解析结果。

## v0.0.1 (2026-03-12)
- 初始 CLI（add / update / list / search）基于 SQLite 存储事件。
- 事件字段支持时间、经纬度、地点备注、人物列表、优先级、备注。
- 修正列表/检索输出列名，避免打印报错。
- 新增使用说明文档 USAGE.md。
- 提供批量导入示例脚本 mystory.sh（使用 mystory.db）。

## v.0.0.2 (2026-03-21)
- full data test ，修正数据输入输出格式问题。
- 实现交互式 IO 。
- update 前显示现有条目。
- 将公元前纪年统一为负数标准格式：公元0年即公元前1年、-1年即前2年、-2年即前3年、以此类推。