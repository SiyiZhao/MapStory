# MapStory 设计文档

## 项目概述

MapStory 是一个历史事件数据库管理工具，用于记录和管理历史事件、世界线设定、日常事务或虚构故事。核心数据结构为事件条目，包含时间、地点、人物、事件描述和优先级等信息。

---

## 核心数据模型

### Event（事件）
```
{
  id: int (primary key)
  time: {
    iso: str              # ISO 8601 格式 (e.g., "2024-01-15T10:30:00Z")
    year: int             # 公元纪年法年份
    month: int            # 月 (1-12)
    day: int              # 日 (1-31)
    sort_bucket: int      # 排序用的时间粒度（用于未指定具体时间的事件）
    note: str             # 可选的时间备注或历史纪年法标注
  }
  location: {
    lat: float            # 纬度 (-90 到 90)
    lon: float            # 经度 (-180 到 180)
    location_note: str    # 地名或行政区划补充信息
  }
  persons: list[str]      # 相关人物列表
  event: str              # 事件描述（必需）
  priority: str           # 优先级：史实 > 史实(存疑) > 自设 > 史实(删减)
  source: str             # 出处（文献/链接）或原文备注
  created_at: datetime    # 创建时间
  updated_at: datetime    # 更新时间
}
```

---

## 代码架构

### 1. 数据存储层 (Store Layer)
**文件**: `mapstory_store.py`

**责任**:
- SQLite 数据库的 CRUD 操作
- 事件表的创建与迁移
- 原始查询和索引管理

**核心接口**:
```python
class EventStore:
    def create(event: Event) -> int
    def read(event_id: int) -> Event
    def update(event: Event) -> None
    def delete(event_id: int) -> None
    def query_by_time_range(start: datetime, end: datetime) -> List[Event]
    def query_by_location(lat: float, lon: float, radius_km: float) -> List[Event]
    def query_by_persons(persons: List[str]) -> List[Event]
    def query_by_priority(priority: str) -> List[Event]
    def list_all(sort_by: str = "time") -> List[Event]
```

---

### 2. 验证层 (Validation Layer)
**文件**: `mapstory_validators.py`

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
**文件**: `mapstory_time_utils.py`

**责任**:
- 时间解析和格式化
- 时间范围查询支持
- 为扩展功能预留接口

**核心函数**:
```python
def parse_time_components(year, month, day, sort_bucket) -> dict
def utc_now_iso() -> str
def to_iso_format(year: int, month: int, day: int) -> str
def from_iso_format(iso_str: str) -> tuple[int, int, int]
def get_sort_bucket(year: int, month: int, day: int) -> int
```

---

### 4. CLI 交互层 (CLI Layer)
**文件**: `mapstory_cli.py`, `mapstory_interactive.py`

**责任**:
- 命令行参数解析
- 交互式输入流程
- 用户交互提示和验证

**核心命令**:
```
mapstory add           # 添加事件
mapstory query         # 查询事件（时间/地点/人物）
mapstory list          # 列表显示
mapstory edit          # 编辑事件
mapstory delete        # 删除事件
mapstory sort          # 按时间排序
mapstory review        # 审核优先级（扩展功能）
```

---

### 5. 输出层 (Output Layer)
**文件**: `mapstory_output.py`

**责任**:
- 格式化输出（CLI 表格、JSON 等）
- 事件展示逻辑
- 为导出功能预留接口

**核心函数**:
```python
def format_event_table(events: List[Event]) -> str
def format_event_detail(event: Event) -> str
def to_json(events: List[Event]) -> str
def to_export_format(events: List[Event], format: str) -> str  # 预留导出接口
```

---

### 6. 错误处理层 (Errors Layer)
**文件**: `mapstory_errors.py`

**责任**:
- 自定义异常定义
- 错误分类

**异常类**:
```python
class MapStoryError(Exception)          # 基础异常
class InputValidationError(MapStoryError)
class NotFoundError(MapStoryError)
class DatabaseError(MapStoryError)
class TimeFormatError(MapStoryError)
```

---

### 7. 常量定义层 (Constants Layer)
**文件**: `mapstory_constants.py`

**责任**:
- 配置常量
- 优先级定义
- 数据库路径等

---

## 功能实现计划

### 第一阶段：核心功能完善
**状态**: 部分完成 ✓

#### 1.1 时间排序功能 ✗
- **目标**: 实现按时间排序的查询输出
- **实现**: 在 `mapstory_store.py` 中添加 `list_all(sort_by="time")` 方法
- **测试**: `tests/test_sorting.py`
- **优先级**: 高

---

### 第二阶段：时间处理扩展
**状态**: 未开始

#### 2.1 历史纪年法转换 ✗
- **目标**: 支持农历、干支纪年等历史纪年法
- **实现**:
  - 在 `mapstory_time_utils.py` 中添加转换函数
  - 使用开源农历库（如 `lunarcalendar`）
  - 在事件的 `time.note` 字段存储历史纪年法标注
- **文档**: 
  - 参考资料: https://ytliu0.github.io/ChineseCalendar/table_period_chinese.html
- **测试**: `tests/test_time_conversion.py`
- **优先级**: 中

#### 2.2 年号数据库 ✗
- **目标**: 内置中国历史年号数据库
- **实现**:
  - 创建 `data/dynasties.json` 或 `data/reign_periods.csv`
  - 在 `mapstory_time_utils.py` 中创建年号查询接口
  - 支持按年号查询所对应的公元纪年
- **文档**: 参考`docs/era-reference.md`
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
  - 创建 `mapstory_excel.py` 模块
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
  - 创建 `mapstory_text_parser.py` 模块
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
  - 创建 `mapstory_wikipedia_crawler.py` 模块
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
  - 创建 `mapstory_tui.py` 模块（TUI = Text User Interface）
  - 使用 `curses` 库构建菜单、表格、输入框
  - 支持：查看事件列表、编辑、删除、搜索等操作
- **优先级**: 低（当前基础 CLI 可用）

---

### 第六阶段：Web UI
**状态**: 未开始

#### 6.1 基于 Flask 的 Web 界面 ✗
- **目标**: 提供易用的 Web 应用
- **实现**:
  - 创建 `mapstory_web.py` 模块
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

- **API 文档**: 在各模块中通过 docstring 维护
- **用户文档**: 更新 `docs/USAGE.md` 和 `docs/user-preferences.md`
- **变更日志**: 持续更新 `CHANGELOG.md`
- **示例数据**: 在 `tests/` 中维护示例数据用于演示
