# 时间模块调研与改进方案

## 1. 目标

MapStory 的时间字段希望同时满足两类需求：

- 机器可排序、可查询、可导出。
- 人类可记录历史纪年、模糊时间和传统表述。

你目前提出的目标可以总结为：

- `time`：按公元纪年保存，尽量接近 ISO 风格，但允许只精确到年、月、日。
- `time_note`：保留传统纪年或原始时间说明，例如年号、“二十六年”等，作为参考和溯源字段。

这样做以后，一个字段只承担一种职责，时间模型会清楚很多。

## 2. 结论

### 2.1 Python 有成熟库，但没有“自动替你建模历史模糊日期”的万能库

Python 生态对这些能力支持很好：

- ISO 8601 解析
- 时区转换
- 标准格式输出
- 完整 `datetime` 对象计算与比较

但对下面这个需求，没有单一库能直接替 MapStory 解决：

- 一个字段允许 `YYYY`、`YYYY-MM`、`YYYY-MM-DD`
- 同时还要保留“它原本只精确到年 / 月 / 日”这个事实

这里最容易误解的点是“保留精度语义”。

这句话的意思不是“能不能识别 `YYYY`”。
而是：

- `1911` 的含义是“只知道发生在 1911 年”
- `1911-01-01` 的含义是“明确知道发生在 1911-01-01”

这两个值不能视为同一个事实。

如果一个库把 `1911` 解析成 `1911-01-01`，那它只是为了得到一个可计算对象做了默认补全；它并没有自动替你保存“原始精度是 year”这件事。

所以：

- Python 库能帮你“解析”
- 但 MapStory 仍然要自己保存“精度”

### 2.2 对 MapStory 最合适的策略

推荐方案是：

- 用标准库 `datetime` 处理完整时间戳，例如 `created_at`、`updated_at`
- 用标准库 `zoneinfo` 处理时区
- 用 `python-dateutil` 作为 `time` 的输入校验和补充解析工具
- 项目自己显式保存 `time_precision`

一句话总结：

- 库负责“解析、格式化、时区”。
- MapStory 自己负责“历史场景下的不完整时间语义”。

## 3. Python 标准库能做到什么

### 3.1 `datetime`

标准库 `datetime` 非常成熟，适合做：

- 完整日期时间对象表示
- `isoformat()` 输出
- `fromisoformat()` 解析标准字符串
- 与 UTC 时间戳互转

官方文档：

- `datetime` 文档：https://docs.python.org/3/library/datetime.html

适合 MapStory 的点：

- 官方、稳定、零额外依赖
- `isoformat()` 支持 `timespec` 控制输出粒度
- 很适合处理 `created_at`、`updated_at` 这一类完整时间戳

不足：

- 不适合直接表达“只有年份”或“只有年月”的语义对象
- `date` / `datetime` 本身要求完整合法日期
- `datetime.fromisoformat()` 对 reduced precision ISO 支持有限，官方文档明确写了 reduced precision dates 目前不支持

这意味着：

- `2024-03-01T10:20:30+08:00` 很适合交给 `datetime`
- `2024`、`2024-03` 这种“部分精度日期”不应该强行直接建模成一个普通 `datetime`

### 3.2 `zoneinfo`

从 Python 3.9 起，标准库有 `zoneinfo`，用于 IANA 时区数据库支持。

官方文档：

- `zoneinfo` 文档：https://docs.python.org/3/library/zoneinfo.html

适合 MapStory 的点：

- 标准库内置，推荐替代老式 `pytz`
- 能正确表达 `Asia/Shanghai` 这类时区
- 适合未来支持多地区展示，虽然你当前默认主要是东八区

建议：

- 新代码优先使用 `zoneinfo`
- 不建议新引入 `pytz`

## 4. 常见第三方库调研

### 4.1 `python-dateutil`

这是 Python 时间处理里非常成熟、非常常用的补充库。

官方文档：

- https://dateutil.readthedocs.io/en/stable/parser.html

适合 MapStory 的点：

- `parser.isoparse()` 支持 ISO 8601 解析
- 官方文档明确支持 `YYYY`、`YYYY-MM`、`YYYY-MM-DD`
- 对很多 ISO 变体兼容度更高

但它有一个很重要的限制：

- 它会把不完整日期补成完整日期对象
- 文档明确写明，未指定的组件会使用最低值

这意味着：

- `2024` 会被补成类似 `2024-01-01`
- `2024-03` 会被补成类似 `2024-03-01`

这对“解析”是方便的，但对历史应用来说有风险：

- `2024` 并不等于 `2024-01-01`
- 它只是“精确到年”

所以 `dateutil` 很适合做：

- 输入合法性检查
- 标准格式归一化

但不适合单独承担：

- 你的时间语义模型

### 4.2 Pendulum

Pendulum 是一个体验很好的现代时间库，封装比标准库友好。

官方文档：

- https://pendulum.eustace.io/docs/

适合 MapStory 的点：

- 时区体验很好
- API 比标准库更顺手
- 解析和格式化做得比较完整

但对你的问题，它仍然有同样的核心限制：

- 解析 `2012`、`2012-05` 时，会自动补成完整 datetime
- 它更擅长“完整时间对象”，不是“部分精度日期建模”

所以 Pendulum 更适合：

- 如果项目是日程、任务、日志系统

对 MapStory 这种历史事件系统来说：

- 它可以用，但不是关键问题的决定性解法
- 引入后会增加依赖，却不能替你解决“年/月/日精度”语义

### 4.3 Arrow

Arrow 也是一个常见的时间库，强调易用性。

官方文档：

- https://arrow.readthedocs.io/en/latest/

优点：

- API 友好
- 支持 ISO 8601 输入输出
- 时区处理方便

但和 Pendulum 类似：

- 它主要是“更好用的 datetime”
- 不是“部分精度历史日期”的专门模型

因此它并不比“标准库 + 自定义精度字段”更适合 MapStory。

## 5. 这类历史场景的核心问题，不是库，而是模型

你现在真正要解决的不是“如何解析时间”，而是“如何定义时间数据的语义边界”。

对 MapStory 来说，至少要分开三个层面：

### 5.1 原始表达

用户看到或输入的时间表达，例如：

- `前221年`
- `1911`
- `1911-10`
- `1911-10-10`
- `秦始皇二十六年`
- `同治三年冬`

这部分并不一定都应该放到结构化字段里。

### 5.2 结构化公元时间

用于排序、筛选和 API 传输的规范字段，例如：

- `year = 1911`
- `month = 10`
- `day = 10`
- `precision = day`

这才是程序真正可靠的查询基础。

### 5.3 展示与推断信息

例如：

- `display_time = 1911-10`
- `sort_key`
- 推导出的区间表示，如一年范围、一个月范围

这部分应该由程序计算，而不是直接混在原始输入字段里。

## 6. 推荐的数据设计

### 6.1 字段建议

建议不要继续使用 `time_iso` 这个名字，而改成更明确的一组字段：

- `time_year: INTEGER`
- `time_month: INTEGER NULL`
- `time_day: INTEGER NULL`
- `time_precision: TEXT NOT NULL`
- `time_label: TEXT NOT NULL`
- `t_note: TEXT NULL`

建议语义如下：

- `time_year/month/day`
  - 公元纪年结构化字段，用于排序和检索
- `time_precision`
  - 取值如 `year | month | day`
- `time_label`
  - 对外展示的标准化字符串，例如 `1911`、`1911-10`、`1911-10-10`
- `t_note`
  - 原始纪年说明或补充说明，例如“宣统三年八月十九”“秦王政二十六年”

如果你希望尽量少改动，也可以保留一个兼容字段：

- `time`：替代当前 `time_iso`

其规则是：

- 只允许 `YYYY` / `YYYY-MM` / `YYYY-MM-DD`
- 作为标准化展示值
- 不再允许任意模糊文本直接塞进去

而类似“二十六年”必须进入 `t_note`。

### 6.2 为什么我建议加 `time_precision`

这是整个方案里最关键的一点。

因为：

- `1911` 和 `1911-01-01` 字符串不同，但更本质的差异是“精度不同”
- 如果只靠字符串长度推断精度，代码里到处都要重复逻辑
- 如果解析器把 `1911` 补成 `1911-01-01`，你会丢失“只精确到年”这个事实

所以应该显式保存：

- `year`
- `month`
- `day`
- `precision`

这比单纯依赖某个时间库靠谱得多。

## 7. 推荐库选型

### 7.1 建议结论

对 MapStory，我建议：

- 必选：标准库 `datetime`、`zoneinfo`
- 可选：`python-dateutil`
- 暂不建议作为主依赖：Pendulum、Arrow

### 7.2 原因

`datetime + zoneinfo` 适合负责：

- `created_at`、`updated_at`
- 完整时间戳格式化
- API 时区转换

`python-dateutil` 适合负责：

- 对标准输入 `YYYY` / `YYYY-MM` / `YYYY-MM-DD` 做补充解析
- 必要时处理更复杂 ISO 输入

但真正的“历史日期精度语义”仍建议自己实现一个轻量层。

## 8. MapStory 的改进计划

### 8.1 第一阶段：统一输入边界

目标：

- 让结构化时间字段只接受这三种格式：
  - `YYYY`
  - `YYYY-MM`
  - `YYYY-MM-DD`

规则：

- 非公元纪年、年号、模糊表述，不再写入 `time`
- 全部进入 `t_note`

这一步可以立刻降低混乱度。

### 8.2 第二阶段：重构时间工具模块

建议把当前 [time_utils.py](/Users/siyizhao/Mars/MapStory/mapstory/time_utils.py) 重构为明确的几个函数：

- `parse_structured_time(text) -> StructuredTime`
- `format_structured_time(structured_time) -> str`
- `structured_time_to_sort_key(structured_time) -> tuple`
- `validate_time_precision(year, month, day, precision) -> None`

并新增一个内部 dataclass，例如：

```python
@dataclass(slots=True)
class StructuredTime:
    year: int
    month: int | None
    day: int | None
    precision: Literal["year", "month", "day"]
    label: str
```

这样以后无论 CLI、Web 还是导入模块，都用同一套时间对象。

### 8.3 第三阶段：数据库迁移

建议迁移方向：

- 废弃 `time_iso`
- 新增或确认：
  - `time_year`
  - `time_month`
  - `time_day`
  - `time_precision`
  - `time` 或 `time_label`
  - `t_note`

迁移策略：

- 已有数据中，如果 `time_iso` 是 `YYYY` / `YYYY-MM` / `YYYY-MM-DD`，则结构化迁移
- 其他旧值：
  - 尝试抽取公元年份写入结构化字段
  - 原始字符串保留到 `t_note`
  - 无法可靠转换的，标记为待人工核验

### 8.4 第四阶段：排序与查询规则重写

建议以后不要再依赖“解析字符串推导排序”。

改成明确规则：

- `day` 精度：按具体日期排序
- `month` 精度：按该月起始排序
- `year` 精度：按该年起始排序

同时保留 `time_precision` 参与二级排序，以免：

- `1911`
- `1911-01`
- `1911-01-01`

在排序时语义混乱。

### 8.5 第五阶段：时区职责收缩

历史事件的事件日期本身，通常不需要频繁做时区换算。

建议区分两类时间：

- 事件时间 `time`
  - 主要是日期语义，不做复杂时区换算
- 系统时间 `created_at/updated_at`
  - 使用 UTC 存储
  - 展示时用 `zoneinfo` 转为本地时区

这样模型会更清楚。

## 9. 具体建议

### 9.1 短期最推荐方案

如果希望改动小、收益高，我建议马上执行这套最小方案：

1. 把当前 `time_iso` 重命名为 `time`
2. 明确 `time` 只允许：
   - `YYYY`
   - `YYYY-MM`
   - `YYYY-MM-DD`
3. 新增 `time_precision`
4. 把“二十六年”“宣统三年”等内容只放进 `t_note`
5. `created_at/updated_at` 继续使用标准 UTC ISO 时间戳

### 9.2 不建议的方案

不建议继续让一个字段同时承担这些角色：

- 原始文本
- 标准化日期
- ISO 语义
- 排序依据
- 展示依据

这正是当前混乱的根源。

## 10. 最终判断

对 MapStory 来说，时间模块最合理的方向不是“寻找一个万能时间库”，而是：

- 用成熟库处理完整时间与时区
- 用清晰的数据模型处理历史场景下的不完整日期

一句话总结就是：

- `datetime/zoneinfo` 解决“时间技术问题”
- `time + time_precision + t_note` 解决“历史数据语义问题”

这两层分开之后，时间模块就会稳定很多。

## 11. 参考资料

- Python `datetime` 官方文档：https://docs.python.org/3/library/datetime.html
- Python `zoneinfo` 官方文档：https://docs.python.org/3/library/zoneinfo.html
- python-dateutil parser 文档：https://dateutil.readthedocs.io/en/stable/parser.html
- Pendulum 官方文档：https://pendulum.eustace.io/docs/
- Arrow 官方文档：https://arrow.readthedocs.io/en/latest/
