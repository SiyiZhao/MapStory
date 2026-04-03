# MapStory 设计文档

## 项目概述

MapStory 是一个历史事件数据库管理工具，用于记录和管理历史事件、世界线设定、日常事务或虚构故事。核心数据结构为事件条目，包含时间、地点、人物、事件描述和优先级等信息。

---

## 仓库结构设计

遵循现代Python库的标准结构：

```
MapStory/
├── mapstory/                  # 主包目录
│   ├── __init__.py            # 包初始化，导出公共API
│   ├── store.py               # 数据存储层
│   ├── validators.py          # 验证层
│   ├── time_utils.py          # 时间处理层
│   ├── errors.py              # 异常定义
│   ├── constants.py           # 常量定义
│   ├── models.py              # 数据模型定义 (Event, Location, TimeInfo) ——或许后续也可以考虑添加地点处理层，处理古今地理行政区划的变动
│   ├── cli/                   # CLI 子包
│   │   ├── __init__.py
│   │   ├── main.py            # CLI 入口和命令解析
│   │   ├── interactive.py     # 交互式输入流程
│   │   └── commands.py        # 各类命令实现
│   ├── output/                # 输出子包
│   │   ├── __init__.py
│   │   ├── formatters.py      # 格式化输出（表格、JSON等）
│   │   └── exporter.py        # 导出功能预留
│   ├── import_/               # 导入子包
│   │   ├── __init__.py
│   │   ├── parsers.py         # 各式导入解析器基类
│   │   ├── excel.py           # Excel 导入实现
│   │   ├── text.py            # 纯文本导入实现（预留，暂不实现）
│   │   └── wikipedia.py       # 维基百科导入实现（预留，暂不实现）
│   └── ext/                   # 扩展功能子包 ——比起统一的扩展功能子包，我更想要按照 时间相关处理、空间相关处理、用户交互界面相关 等功能划分为不同的子包
│       ├── __init__.py
│       ├── time_conversion.py # 历史纪年法转换
│       ├── era_database.py    # 年号数据库
│       ├── age_calc.py        # 人物年龄计算
│       ├── tui.py             # 基于 curses 的 TUI（第5阶段）
│       └── web.py             # Flask Web UI（第6阶段）
├── tests/                     # 测试目录
│   ├── __init__.py
│   ├── conftest.py            # pytest 配置
│   ├── test_store.py
│   ├── test_validators.py
│   ├── test_time_utils.py
│   ├── test_sorting.py
│   ├── test_models.py
│   ├── test_cli.py
│   ├── test_output.py
│   ├── test_import/           # 导入测试子目录
│   │   ├── test_excel.py
│   │   ├── test_text.py
│   │   └── test_wikipedia.py
│   ├── test_ext/              # 扩展功能测试子目录
│   │   ├── test_time_conversion.py
│   │   ├── test_era_database.py
│   │   └── test_age_calc.py
│   ├── unit/                  # 单元测试
│   └── integration/           # 端到端测试
│       └── test_workflows.py
├── data/                      # 数据文件
│   └── era_periods.csv        # 中国历史年号数据——我的设想是这个数据库与我们的主数据库一致，将年号变更视为 events 记录
├── docs/                      # 文档
│   ├── design.md              # 本文件：总体设计文档
│   ├── USAGE.md               # 用户使用文档
│   ├── api-proposal.md        # API 设计提案
│   ├── era-reference.md       # 历史纪年法参考
│   ├── dev-preferences.md     # 开发偏好和 AI 指引（原 user-preferences.md）
│   └── ARCHITECTURE.md        # 架构深度说明（可选）
├── examples/                  # 示例数据和脚本
│   ├── sample_events.json     # 示例事件数据
│   └── sample_workflow.py     # 使用示例
├── pyproject.toml             # 项目配置和依赖定义
├── CHANGELOG.md               # 变更日志
├── README.md                  # 项目说明
└── main.py                    # 脚本入口（向后兼容）——这个是什么意思？现在的main.py是uv自动创建的，我其实没想清楚这个文件应该承担什么功能。
```

**关键设计说明**:
- `mapstory/` 为核心库代码，遵循 PEP 420 namespace 包规范
- `cli/` 和 `output/` 等子包便于关注点分离和模块化
- `import_/` 使用下划线避免与 Python 关键字冲突 ——改为import_data语义更清晰？
- `ext/` 存放可选的扩展功能，保持核心库轻量
- `tests/` 结构镜像 `mapstory/` 便于导航

---

## 核心数据模型

### Event（事件）
```
{
  id: int (primary key)
  time: {
    iso: str              # ISO 8601 格式 (e.g., "2024-01-15T10:30:00Z") ——内部储存可以用Z，但是输入输出层我希望用UTC+8
    year: int             # 公元纪年法年份
    month: int            # 月 (1-12)
    day: int              # 日 (1-31)
    sort_bucket: int      # 排序用的时间粒度（用于未指定具体时间的事件）
    t_note: str           # 可选的时间备注或历史纪年法标注
  }
  location: {
    lat: float            # 纬度 (-90 到 90)，可选
    lon: float            # 经度 (-180 到 180)，可选
    loc_note: str         # 地名或行政区划补充信息（现代行政区划或历史地名）
  } ——或许可以用现代行政区划经纬度数据库，若为输入经纬度，则按照数据库自动补全
  persons: list[str]      # 相关人物列表
  event: str              # 事件描述（必需）
  priority: str           # 优先级：史实 > 史实(存疑) > 自设 > 史实(删减)
  source: str             # 出处（文献/链接）或原文备注
  created_at: datetime    # 创建时间
  updated_at: datetime    # 更新时间
}
```

**时区处理**:
- 内部数据库统一使用 UTC (Z 格式)，便于数据一致性
- CLI 输入输出层自动转换为 UTC+8（北京时间），对中文用户友好
- 时间处理函数提供 `to_local_tz()` 和 `from_local_tz()` 接口——这个借口保留以后转化为其它时区输出的可能性？

**位置查询**:
- 支持两种查询方式：
  1. 经纬度范围查询：`query_by_location(lat, lon, radius_km)` - 用于地图应用
  2. 行政区划名查询：`query_by_location_name(region_name)` - 用于历史研究，配合 Nominatim 等地理编码工具
```

---

## 代码架构

### 1. 数据存储层 (Store Layer)
**文件**: `mapstory/store.py`

**责任**:
- SQLite 数据库的 CRUD 操作
- 事件表的创建与迁移
- 原始查询和索引管理

**核心接口**:
```python
class EventStore:
    def create(event: Event) -> int                          # 创建事件，返回ID
    def read(event_id: int) -> Event                         # 读取单个事件
    def update(event_id: int, event: Event) -> None          # 更新事件
    def delete(event_id: int) -> None                        # 删除事件
    def query_by_time_range(start: str, end: str) -> List[Event]      # 时间范围查询
    def query_by_location_coords(lat: float, lon: float, radius_km: float) -> List[Event]
    def query_by_location_name(region_name: str) -> List[Event]       # 按行政区划名查询
    def query_by_persons(persons: List[str], match_all: bool = False) -> List[Event]
    def query_by_priority(priority: str) -> List[Event]
    def list_all(sort_by: str = "time", limit: int = None) -> List[Event]   # 默认按时间排序
    def filter(filters: dict) -> List[Event]                 # 复合条件查询
```

**重要说明**:
- `list_all()` 默认返回按时间升序排列的所有事件
- 支持多种查询方式：经纬度范围（地图应用）、行政区划名（历史研究）
- 返回结果自动包含生成的排序键，用于前端优化

---

### 2. 验证层 (Validation Layer)
**文件**: `mapstory/validators.py`

**责任**:
- 输入验证（格式、范围、类型）
- 规范化数据（清理空白、转换格式）
- 业务规则验证

**核心函数**:
```python
def validate_event(event: dict) -> dict  # 完整事件验证
def validate_coordinates(lat: float, lon: float) -> bool
def validate_event_text(text: str) -> str
def validate_priority(priority: str) -> str
def validate_time_components(year, month, day) -> dict
def normalize_persons(persons: List[str]) -> List[str]
```

---

### 3. 时间处理层 (Time Utils Layer)
**文件**: `mapstory/time_utils.py`

**责任**:
- 时间解析和格式化
- 时间范围查询支持
- 为扩展功能预留接口

**核心函数**:
```python
# 基础时间解析
def parse_time_components(year: int, month: int, day: int) -> dict
    """解析年月日为内部数据结构，包含 ISO 字符串和排序键"""

def to_iso_format(year: int, month: int, day: int) -> str
    """将年月日转换为 ISO 8601 UTC 格式字符串"""

def from_iso_format(iso_str: str) -> tuple[int, int, int]
    """从 ISO 8601 字符串解析出年月日"""

def get_sort_bucket(year: int, month: int = None, day: int = None) -> int
    """根据时间精度返回排序粒度（0=年，1=月，2=日），用于排序未精确指定的事件"""

# 时区转换
def utc_now_iso() -> str
    """返回当前 UTC 时间的 ISO 8601 字符串"""

def to_local_tz(iso_str: str, tz: str = "Asia/Shanghai") -> str
    """将 UTC ISO 字符串转换为指定时区的本地时间字符串"""

def from_local_tz(local_str: str, tz: str = "Asia/Shanghai") -> str
    """将本地时间字符串转换为 UTC ISO 格式"""

# 格式化展示
def format_date_for_display(iso_str: str, tz: str = "Asia/Shanghai", with_time: bool = False) -> str
    """格式化为用户友好的日期字符串（如 "2024-01-15" 或 "2024-01-15 10:30"）"""

# 时间比较
def is_before(iso_str1: str, iso_str2: str) -> bool
    """比较两个时间的先后顺序"""

def time_range_overlaps(range1: tuple[str, str], range2: tuple[str, str]) -> bool
    """检查两个时间范围是否重叠"""
```

---

### 4. CLI 交互层 (CLI Layer)
**文件**: `mapstory/cli.py`, `mapstory/interactive.py`

**责任**:
- 命令行参数解析
- 交互式输入流程
- 用户交互提示和验证

**核心命令**:
```
mapstory add           # 交互式添加事件
mapstory list          # 列表显示所有事件（默认按时间升序）
mapstory query         # 查询事件（可指定时间/地点/人物）
mapstory edit <id>     # 编辑指定ID的事件
mapstory delete <id>   # 删除指定ID的事件
mapstory review        # 审核模式（第4阶段）：按优先级审核
mapstory export        # 导出事件（第3阶段）
mapstory import        # 导入事件（第3阶段）
```

**重要说明**:
- 数据库在创建表时设置 `time_sort_bucket` 和 `time_iso` 的复合索引，确保查询效率
- `list` 命令默认返回按时间升序的所有事件，支持 `--sort` 选项改变排序方式
- `add` 命令完成后自动按时间位置插入数据库，无需手动排序
---

### 5. 输出层 (Output Layer)
**文件**: `mapstory/output/formatters.py`, `mapstory/output/exporter.py`

**责任**:
- 格式化输出（CLI 表格、JSON 等）
- 事件展示逻辑
- 为导出功能预留接口

**核心函数** (`formatters.py`):
```python
def format_event_table(events: List[Event], tz: str = "Asia/Shanghai") -> str
    """格式化为 CLI 表格输出，按时间排序，显示简要信息"""

def format_event_detail(event: Event, tz: str = "Asia/Shanghai") -> str
    """格式化单个事件详情，显示完整信息"""

def to_json(events: List[Event]) -> str
    """序列化为 JSON 格式（使用 UTC 时间）"""

def to_csv(events: List[Event], tz: str = "Asia/Shanghai") -> str
    """导出为 CSV 格式（用于 Excel 等）"""
```

**导出函数** (`exporter.py`):
```python
class Exporter:
    def export(events: List[Event], format: str, output_path: str) -> None
        """通用导出接口，支持 json, csv, excel, md 等格式"""
```

**重要说明**:
- 输出层统一调用 `time_utils.format_date_for_display()` 处理时区
- 导出功能实现在 `mapstory/output/exporter.py` 中，支持可扩展的格式插件
---

### 6. 错误处理层 (Errors Layer)
**文件**: `mapstory/errors.py`

**责任**:
- 自定义异常定义
- 错误分类

**异常类**:
```python
class MapStoryError(Exception)
    """基础异常类，所有 MapStory 相关异常的根类"""

class InputValidationError(MapStoryError)
    """输入数据验证失败：格式错误、范围超界、类型不匹配等
    场景：坐标超出范围、优先级值不合法、事件描述为空等"""

class NotFoundError(MapStoryError)
    """查询目标不存在：指定的事件ID不存在、查询无结果等
    场景：delete/edit 不存在的事件、查询无匹配事件"""

class DatabaseError(MapStoryError)
    """数据库操作失败：连接错误、事务失败、数据损坏等
    场景：磁盘满、数据库被锁定、SQL 执行错误"""

class TimeFormatError(MapStoryError)
    """时间格式处理错误：无效的 ISO 格式、年号转换失败等
    场景：解析非法的时间字符串、年号数据库查询失败"""

class LocationError(MapStoryError)
    """位置处理错误：地理编码失败、坐标无效等
    场景：地名转换失败、Nominatim API 调用异常"""
```
---

### 7. 常量定义层 (Constants Layer)
**文件**: `mapstory/constants.py`

**责任**:
- 配置常量
- 优先级定义
- 默认数据库路径等

**定义内容**:
```python
# 优先级常量
PRIORITY_FACT = "史实"
PRIORITY_QUESTIONABLE = "史实(存疑)"
PRIORITY_CUSTOM = "自设"
PRIORITY_DELETED = "史实(删减)"
PRIORITY_ORDER = [PRIORITY_FACT, PRIORITY_QUESTIONABLE, PRIORITY_CUSTOM, PRIORITY_DELETED]

# 不需要审核状态，我的使用计划是默认优先级为存疑或自设，审核后的存疑更改为史实

# 时间粒度常量
TIME_GRANULARITY_YEAR = 0
TIME_GRANULARITY_MONTH = 1
TIME_GRANULARITY_DAY = 2

# 数据库配置
DEFAULT_DB_PATH = "mapstory.db"
DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_LOCATION_RADIUS = 100  # km

# 分页配置
DEFAULT_PAGE_SIZE = 20
```

### 8. 导入层 (Import Layer)
**文件**: `mapstory/import_/`

**责任**:
- 支持多种格式导入（Excel、TEXT、维基百科）
- 统一导入接口
- 数据验证和转换

**核心设计**:
```python
class ImportParser(ABC):
    """导入解析器基类"""
    def parse(self, source: Union[str, file]) -> List[Event]:
        """解析源数据为 Event 列表"""
        pass

class ExcelParser(ImportParser):
    """Excel 文件导入"""
    pass

class TextParser(ImportParser):
    """纯文本导入（Markdown/自定义格式）"""
    pass

class WikipediaParser(ImportParser):
    """维基百科爬虫导入"""
    pass

class Importer:
    """统一导入管理器"""
    def import_from_file(file_path: str, format: str) -> List[Event]:
        """从文件导入"""
        pass
    
    def import_from_source(source_type: str, **kwargs) -> List[Event]:
        """从外部源导入（如维基百科）"""
        pass
```

**重要说明**:
- 所有导入器返回 Event 列表前必须进行完整的数据验证
- 支持干运行（dry-run）模式，预览导入结果而不实际写入数据库
- 导入失败时生成详细的错误报告，逐行显示问题所在

---

## 功能实现计划

### 第一阶段：核心功能完善
**状态**: 部分完成 ✓

#### 1.1 时间排序功能 ✗
- **目标**: 实现按时间排序的查询输出
- **实现**: 
  - 在 `mapstory/store.py` 中添加 `list_all(sort_by="time")` 方法，默认返回按时间升序的事件
  - 在数据库表中创建 `(time_sort_bucket, time_iso)` 的复合索引优化查询
  - 支持按优先级、创建时间等其他字段排序
- **测试**: `tests/test_sorting.py`
- **优先级**: 高

---

### 第二阶段：时间处理扩展
**状态**: 未开始

#### 2.1 历史纪年法转换 ✗
- **目标**: 支持农历、干支纪年等历史纪年法
- **实现**:
  - 在 `mapstory/time_utils.py` 中添加转换函数
  - 使用开源农历库（如 `lunarcalendar`）
  - 在事件的 `time.t_note` 字段存储历史纪年法标注
- **文档**: 
  - 参考资料: https://ytliu0.github.io/ChineseCalendar/table_period_chinese.html
- **测试**: `tests/test_time_conversion.py`
- **优先级**: 中

#### 2.2 年号数据库 ✗
- **目标**: 内置中国历史年号数据库
- **实现**:
  - 创建 `data/era_periods.csv`，记录每次年号变更的精确日期（包括具体月日）
  - 在 `mapstory/ext/era_database.py` 中创建查询接口
  - 支持两种查询：\(1\) 根据年号查找对应的公元纪年范围和日期；\(2\) 根据公元纪年日期反查该时期的年号
  - 注意处理历史上的年号与公元纪年不完全对齐的情况（如年号变更发生在年中）
- **文档**: 参考 `docs/era-reference.md`
- **优先级**: 中

#### 2.3 人物年龄计算 ✗
- **目标**: 计算人物在某时间点的年龄
- **实现**:
  - 在事件model中可选地添加 `persons_info: dict[str, dict]` 存储生卒日期
  - 在 `mapstory_time_utils.py` 中添加 `calculate_age()` 函数
  - 在事件详情输出中显示相关人物的年龄
- **测试**: `tests/test_age_calculation.py`
- **优先级**: 低

---

### 第三阶段：导入导出功能
**状态**: 未开始

#### 3.1 Excel 导入导出 ✗
- **目标**: 支持 Excel 文件的导入导出，生成年表或月表
- **实现**: 
  - 创建 `mapstory/excel.py` 模块
  - 使用 `openpyxl` 或 `pandas` 库
  - 导出格式：按时间线性排列的"年表"或"月表"
  - 对于割据时期：并排展示不同地域事件
- **CLI命令**: 
  ```
  mapstory export --format excel --output timeline.xlsx
  mapstory import --format excel --file timeline.xlsx
  ```
- **测试**: `tests/test_excel_import_export.py`
- **优先级**: 中

#### 3.2 纯文本导入 ✗
- **目标**: 支持纯文本格式导入（可选AI解析）
- **实现**:
  - 定义纯文本输入格式（如 Markdown 列表或特定格式）
  - 创建 `mapstory/text_parser.py` 模块
  - 可选：接入 OpenAI API 进行自然语言解析
- **格式示例**:
  ```
  Event 1: 某某事件
  Time: 2024-01-15
  Location: 北京
  Persons: 张三, 李四
  Priority: 史实
  ```
- **CLI命令**: `mapstory import --format text --file events.txt`
- **优先级**: 低

#### 3.3 维基百科爬虫导入 ✗
- **目标**: 从维基百科获取某年事件列表并导入
- **实现**:
  - 创建 `mapstory/wikipedia_crawler.py` 模块
  - 使用 `requests` + `BeautifulSoup` 爬取维基百科"X年"页面
  - 自动解析事件信息，映射到 Event 数据模型
- **CLI命令**: `mapstory import --source wikipedia --year 2024`
- **优先级**: 低

---

### 第四阶段：审核功能
**状态**: 未开始

#### 4.1 事件优先级审核 ✗
- **目标**: 支持人工审核和调整事件优先级
- **实现**:
  - 添加事件状态字段：`review_status` (unreviewed, reviewed, disputed)
  - 在交互式界面中添加审核模式
  - 记录审核日期和审核者（可选）
- **CLI命令**: `mapstory review --status unreviewed`
- **测试**: `tests/test_review_workflow.py`
- **优先级**: 中

---

### 第五阶段：CLI 增强
**状态**: 部分完成 ✓

#### 5.1 基于 curses 的交互式界面 ✗
- **目标**: 提升交互体验，支持键盘导航
- **实现**:
  - 创建 `mapstory/tui.py` 模块（TUI = Text User Interface）
  - 使用 `curses` 库构建菜单、表格、输入框
  - 支持：查看事件列表、编辑、删除、搜索等操作
- **优先级**: 低（当前基础 CLI 可用）

---

### 第六阶段：Web UI
**状态**: 未开始

#### 6.1 基于 Flask 的 Web 界面 ✗
- **目标**: 提供易用的 Web 应用
- **实现**:
  - 创建 `mapstory/web.py` 模块
  - 使用 Flask + SQLAlchemy ORM
  - 前端：HTML/CSS/JavaScript（简单表格+地图展示）
  - 地图集成：Leaflet.js 显示事件地理位置
- **功能**:
  - 事件列表（表格视图）
  - 事件地图（地理视图）
  - 事件详情和编辑
  - 高级搜索（时间范围/地点/人物）
- **部署**: 可打包为 Docker 容器
- **优先级**: 低（仅在 CLI 功能完善后）

---

## 依赖管理

### 现有依赖
- Python >= 3.8

### 新增依赖（分阶段）

**第二阶段**:
```
lunarcalendar    # 农历转换
```

**第三阶段**:
```
openpyxl         # Excel 导入导出
```

**第四阶段**:
```
beautifulsoup4   # 网页爬虫
requests         # HTTP 请求
```

**第六阶段**:
```
flask            # Web 框架
sqlalchemy       # ORM
```

---

## 测试策略

### 测试文件结构
```
tests/
  __init__.py
  conftest.py              # pytest 配置和共享 fixture
  test_store.py            # 存储层单元测试
  test_validators.py       # 验证层单元测试
  test_time_utils.py       # 时间处理单元测试
  test_sorting.py          # 排序功能测试
  test_time_conversion.py  # 纪年法转换测试
  test_age_calculation.py  # 年龄计算测试
  test_excel_import_export.py  # Excel 导入导出测试
  test_review_workflow.py  # 审核工作流测试
  integration/
    test_end_to_end.py     # 端到端测试
```

---

## 实现路线图

```
┌─────────────────────────────────────────────────────────────┐
│                    核心功能完善 (Phase 1)                    │
│                    时间排序 (1-2 weeks)                      │
├─────────────────────────────────────────────────────────────┤
│          时间处理扩展 (Phase 2, 2-3 weeks)                   │
│  ├─ 历史纪年法转换                                          │
│  ├─ 年号数据库                                              │
│  └─ 人物年龄计算                                            │
├─────────────────────────────────────────────────────────────┤
│      导入导出功能 (Phase 3, 3-4 weeks)                       │
│  ├─ Excel 导入导出 (优先)                                   │
│  ├─ 纯文本导入 (可选)                                       │
│  └─ 维基百科爬虫 (可选)                                     │
├─────────────────────────────────────────────────────────────┤
│       审核功能 (Phase 4, 1-2 weeks)                          │
│       优先级审核和状态追踪                                   │
├─────────────────────────────────────────────────────────────┤
│      CLI 增强 (Phase 5, 2-3 weeks, 可选)                     │
│      基于 curses 的交互式界面                                │
├─────────────────────────────────────────────────────────────┤
│      Web UI (Phase 6, 4-6 weeks, 最后)                       │
│      Flask 应用 + 地图可视化                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 优先级说明

- **高**: 核心功能补完，应尽快实现 (Phase 1)
- **中**: 提升易用性，中期内完成 (Phase 2, 3, 4)
- **低**: 增强体验，可后期迭代 (Phase 5, 6)

---

## 关键设计决策

1. **模块化**: 按职责划分模块，便于独立测试和扩展
2. **向后兼容**: SQLite 数据库通过迁移脚本支持版本升级
3. **渐进式增强**: 从 CLI 逐步升级到 Web UI，保持功能一致性
4. **数据格式**: 使用 ISO 8601 作为内部时间标准，支持多种展示格式
5. **错误处理**: 通过自定义异常类实现细粒度的错误分类

---

## 维护与文档

- **API 文档**: 在各模块中通过 docstring 维护，遵循 Google 风格的文档字符串
- **用户文档**: 
  - `docs/USAGE.md` - 终端用户的使用手册
  - `docs/dev-preferences.md` - 开发偏好和 AI 指引（原 `user-preferences.md`，建议重命名以明确用途）
- **架构文档**:
  - `docs/design.md` - 本设计文档
  - `docs/ARCHITECTURE.md` - 可选的架构深度说明（日后补充）
  - `docs/api-proposal.md` - API 设计提案
- **参考文档**:
  - `docs/era-reference.md` - 历史纪年法参考
- **变更日志**: 持续更新 `CHANGELOG.md`，遵循 Keep a Changelog 格式
- **示例数据**: 在 `examples/` 中维护示例数据和使用脚本用于演示
