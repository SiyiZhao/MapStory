# 时间模块实现方案

## 1. 设计决议

基于当前讨论，MapStory 的时间模块采用以下原则：

### 1.1 事件时间和系统时间分离

- 事件时间使用 `StructuredTime` 管理
- 系统时间 `created_at` / `updated_at` 使用标准库 `datetime`
- 系统时间展示时使用 `zoneinfo`

这两套时间不共享同一种语义，也不应共用同一套解析逻辑。

### 1.2 事件时间禁止自动补全

这是最重要的约束。

如果用户输入：

- `1911`
- `1911-10`
- `1911-10-10`
- `1911-10-10 08`
- `1911-10-10 08:30`

系统只记录用户明确提供的精度。

绝不把：

- `1911` 自动补成 `1911-01-01`
- `1911-10` 自动补成 `1911-10-01`
- `1911-10-10` 自动补成 `1911-10-10 00:00`
- `1911-10-10 08` 自动补成 `1911-10-10 08:00`

换句话说：

- 可以为了排序临时构造“比较键”
- 不能把这种补位后的值写回数据库
- 也不能把它当成事件本身的真实时间

### 1.3 事件时间支持到小时和分钟

结构化时间输入允许以下精度：

- `YYYY`
- `YYYY-MM`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH`
- `YYYY-MM-DD HH:MM`

暂不支持秒。

原因：

- 历史事件绝大多数不需要秒级精度
- 小时和分钟足够覆盖现代事件、日常事务和部分虚构设定
- 这样格式更简单，校验和展示也更稳定

### 1.4 `time_note` 保留传统纪年与补充说明

`time_note` 用于保存：

- 年号
- 传统纪年
- 原始史料表述
- 模糊说明

例如：

- `秦王政二十六年`
- `宣统三年八月十九`
- `同治三年冬`
- `约上午`
- `具体日时不详`

`time_note` 不参与结构化排序，只作参考与展示。

## 2. 最终数据模型

建议事件时间统一建模为：

```python
@dataclass(slots=True)
class StructuredTime:
    year: int | None
    month: int | None
    day: int | None
    hour: int | None
    minute: int | None
    time_note: str | None
```
*答：同意。`time_note` 应保留；`raw` 不必作为 `StructuredTime` 的字段单独存在；`precision` 也不必存成独立字段，可以在运行时根据 `year/month/day/hour/minute` 是否为空推断。`year` 也应允许为空，以支持只有 `time_note`、没有可靠公元纪年的记录。*

字段语义：

- `year/month/day/hour/minute`
  - 结构化组件
- `time_note`
  - 传统纪年、原始表述或模糊补充说明

## 3. 数据库字段建议

建议时间相关字段调整为：

- `time_year INTEGER NULL`
- `time_month INTEGER NULL`
- `time_day INTEGER NULL`
- `time_hour INTEGER NULL`
- `time_minute INTEGER NULL`
- `time_note TEXT NULL`


说明：

- `time_year` 可空
  - 用于兼容纯备注型历史记录
- `time_month/time_day/time_hour/time_minute` 可空
  - 用于表达不同精度，缺失部分保持 `NULL`
- `time_note` 可空
  - 用于保存非结构化说明；只有结构化时间时可为空

## 4. 允许的输入格式

### 4.1 合法格式

只允许以下五种：

```text
YYYY
YYYY-MM
YYYY-MM-DD
YYYY-MM-DD HH
YYYY-MM-DD HH:MM
```

示例：

- `1911`
- `1911-10`
- `1911-10-10`
- `1911-10-10 18`
- `1911-10-10 18:30`

### 4.2 非法格式

以下格式建议直接视为非法结构化时间：

- `1911-1`
- `1911-1-1`
- `1911-10-10 8:3`
- `1911-10-10 8`
- `1911/10/10`
- `1911-10-10T08:30`
- `二十六年`
- `宣统三年`

原因：

- 输入格式越统一，后续排序、API、导出越稳定
- `T` 形式虽然接近 ISO，但当前事件时间不是完整 datetime 体系，没必要引入两种等价写法

如果用户输入的是传统纪年或模糊文本，应引导其写入 `time_note`。

## 5. 精度规则

精度与字段必须严格对应：

- `year`
  - 只有 `year`
- `month`
  - 必须有 `year/month`
- `day`
  - 必须有 `year/month/day`
- `hour`
  - 必须有 `year/month/day/hour`
- `minute`
  - 必须有 `year/month/day/hour/minute`

不允许以下情况：

- 有 `day` 但没有 `month`
- 有 `hour` 但没有 `day`
- 有 `minute` 但没有 `hour`

这部分不依赖第三方库，直接由 `StructuredTime` 的校验逻辑保证。

## 6. 解析策略

### 6.1 推荐实现方式

事件时间不要直接交给 `datetime` 或 `dateutil` 作为主模型。

推荐流程：

1. 用正则或显式模式匹配识别精度
2. 校验数值范围
3. 构造 `StructuredTime`
4. 生成数据库所需的拆分字段

建议函数：

- `parse_time(text: str) -> StructuredTime`
- `validate_time(text: str) -> None`
- `format_time(value: StructuredTime) -> str`
- `build_sort_key(value: StructuredTime) -> tuple`

### 6.2 为什么不把 `python-dateutil` 作为主解析器

因为你的约束已经很清楚：

- 不允许自动补全

而 `python-dateutil` 的长处恰恰在于“把多种输入解析成可计算时间对象”。

这对 `created_at` 这类字段很好，对事件时间反而容易模糊边界。

所以这里更推荐：

- 事件时间：自己解析
- 系统时间：标准库管理

`python-dateutil` 如果保留，也更适合用于：

- 非核心工具脚本
- 导入阶段的辅助识别
- 对外部数据源做预处理

而不应成为 `StructuredTime` 的定义基础。

## 7. 排序设计

### 7.1 原则

排序可以使用“临时补位”，但补位只用于比较，不用于存储。

例如：

- `1911` 的比较起点可以临时视作 `1911-01-01 00:00`
- `1911-10` 的比较起点可以临时视作 `1911-10-01 00:00`
- `1911-10-10` 的比较起点可以临时视作 `1911-10-10 00:00`
- `1911-10-10 08` 的比较起点可以临时视作 `1911-10-10 08:00`

但数据库中的结构化字段仍然保持原始精度，不写入补位结果：

- `time_year = 1911, 其余为空`
- `time_year = 1911, time_month = 10`
- `time_year = 1911, time_month = 10, time_day = 10`
- `time_year = 1911, time_month = 10, time_day = 10, time_hour = 8`

### 7.2 推荐排序键
建议排序键为：

```python
(
    year,
    month or 1,
    day or 1,
    hour or 0,
    minute or 0,
    precision_rank,
)
```

其中：

- `year = 1911`
- `month/day/hour/minute` 只在排序时使用默认值
- `precision_rank` 用来区分同一比较起点下的不同精度

建议：

- `year = 0`
- `month = 1`
- `day = 2`
- `hour = 3`
- `minute = 4`

即：

- 年精度排在月精度前
- 月精度排在日精度前
- 日精度排在小时精度前
- 日精度排在分钟精度前

也就是说，在同一比较起点下，精度越低越靠前，精度越高越靠后。

### 7.3 为什么需要 `precision_rank`

因为单纯靠临时补位会导致这些值比较起点相同：

- `1911`
- `1911-01`
- `1911-01-01`
- `1911-01-01 00`
- `1911-01-01 00:00`

如果没有精度权重，它们会被当成完全一样的排序对象。

但业务上它们显然不同。

*答：不是。“依赖排序键”本身就意味着为了比较而做临时补位，只是这种补位只存在于排序过程，不写回数据库，也不改变事件真实记录。换句话说：存储层仍然禁止自动补全；排序层允许技术性补位。*

## 8. 查询设计

建议未来查询分为两类：

### 8.1 精确结构化查询

直接基于字段：

- `time_year`
- `time_month`
- `time_day`
- `time_hour`
- `time_minute`

例如：

- 查询 1911 年内的事件
- 查询 1911 年 10 月的事件
- 查询某一天的事件

### 8.2 模糊说明查询

基于 `time_note LIKE ...`

例如：

- 查找含“宣统三年”的事件
- 查找含“冬”的事件

这样结构化时间和文字说明不会互相污染。

## 9. 系统时间实现

`created_at` 和 `updated_at` 继续采用：

- Python `datetime`
- UTC 存储
- `zoneinfo` 展示

建议保持 ISO 8601 完整时间戳，例如：

- `2026-04-08T12:30:45Z`

这部分和事件时间完全分离，不复用 `StructuredTime`。

## 10. 代码组织建议

建议新增独立模块，例如：

- `mapstory/time_model.py`

其中包含：

- `StructuredTime`
- `TimePrecision`
- `parse_time`
- `format_time`
- `build_sort_key`
- `validate_time`

同时把现有 [time_utils.py](/Users/siyizhao/Mars/MapStory/mapstory/time_utils.py) 的职责拆开：

- 事件时间相关逻辑迁入新模块
- `utc_now_iso()`、时区展示等保留在系统时间工具模块

建议最终形成：

- `mapstory/time_model.py`
  - 事件时间模型
- `mapstory/system_time.py`
  - 系统时间与时区工具

## 11. 数据迁移方案

### 11.1 旧字段到新字段

当前 `time_iso` 迁移为新模型时：

- 若值匹配五种合法格式之一，则直接迁移
- 若值不匹配：
  - 尝试识别是否能规范化
  - 否则转入 `time_note`

### 11.2 迁移策略

建议迁移步骤：

1. 新增字段：
   - `time_year`
   - `time_month`
   - `time_day`
   - `time_hour`
   - `time_minute`
   - `time_note`
2. 编写迁移脚本遍历旧数据
3. 对合法 `time_iso` 进行结构化拆分
4. 对不合法 `time_iso`：
   - 保留原值到 `time_note`
   - 结构化时间字段置空或人工核验
5. 更新代码只读新字段
6. 最后再移除旧字段

## 12. 最终建议

最终建议可以概括为：

1. 事件时间完全交给 `StructuredTime`
2. 结构化时间不允许自动补全
3. 结构化时间支持到分钟
4. `time_note` 保存传统纪年和模糊说明
5. 排序时允许临时补位，但禁止把补位结果写回数据库
6. `created_at/updated_at` 继续使用 `datetime + zoneinfo`

这套方案最大的优点是边界清楚：

- 什么是事件事实
- 什么是排序技术
- 什么是系统元数据

三者不再混在一起。
