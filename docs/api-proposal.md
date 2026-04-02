# MapStory 新 API 草案（可重写版）

## 1. 术语说明
- API（Application Programming Interface）：程序对外提供的调用方式和规则。
- 在本项目中，主要包含两层：
  - CLI API：命令行命令与参数规则。
  - Web API：后续 Flask 提供的 HTTP 路由和 JSON 结构。

## 2. 设计目标
- 不保留旧 CLI 兼容层，直接采用更清晰的新命令模型。
- 统一领域对象：Event（事件）作为唯一核心资源。
- 为 Web 版预留一致的字段语义，避免 CLI 与 Web 两套标准。

## 3. 事件对象（统一字段）
必填：
- event: string，事件描述。

可选：
- time_iso: string | null，支持 `YYYY` / `YYYY-MM` / `YYYY-MM-DD` / `-221`。
- time_note: string | null，历史纪年等补充说明。
- lat: float | null，范围 [-90, 90]。
- lon: float | null，范围 [-180, 180]。
- location_note: string | null，地名/行政区说明。
- persons: string，内部以逗号分隔存储。
- priority: enum | null，`fact|doubt|fanon|abridged_fact`。
- remark: string | null，来源与备注。

系统字段：
- id: int
- time_year/time_month/time_day/time_sort_bucket（最后一个是什么？）
- created_at/updated_at

## 4. CLI API（建议）
统一入口：`mapstory event <subcommand>`

### 4.1 新增
- 命令：`mapstory event create`
- 示例：
  - `mapstory event create --event "辛亥起义" --time -1911-10-10 --lat 30.6 --lon 114.3 --persons "新军" --priority fact`

### 4.2 查询列表
- 命令：`mapstory event list`
- 参数：`--limit`、`--offset`、`--order time|created` （这些参数都什么意思？）

### 4.3 条件检索
- 命令：`mapstory event search`
- 参数：
  - 时间：`--start-year --end-year`
  - 地理：`--lat-range min max --lon-range min max`
  - 文本：`--person --event --location`
  - 状态：`--priority`

### 4.4 更新
- 命令：`mapstory event update <id>`
- 仅传入需要更新的字段。

### 4.5 删除
- 命令：`mapstory event delete <id>`
- 默认软删除（推荐）：`deleted_at` 非空。（既然有软删除，abridged_fact 是不是可以不用了？）
- 可选硬删除：`--hard`（仅开发环境建议开放）。

### 4.6 查看单条
- 命令：`mapstory event get <id>`

### 4.7 输出格式
- `--format table|json`（默认 table）
- 便于后续 Web/脚本复用。

## 5. Web API（Flask，对齐 CLI）

### 5.1 资源路由
- `POST /api/events` -> create
- `GET /api/events` -> list/search
- `GET /api/events/<id>` -> get
- `PATCH /api/events/<id>` -> update
- `DELETE /api/events/<id>` -> delete

### 5.2 查询参数建议
- `start_year` `end_year`
- `lat_min` `lat_max` `lon_min` `lon_max`
- `person` `event` `location` `priority`
- `limit` `offset` `order`

### 5.3 响应规范（建议）
成功：
- `{ "ok": true, "data": ... }`

失败：
- `{ "ok": false, "error": { "code": "VALIDATION_ERROR", "message": "..." } }`

## 6. 与当前代码的差异
- 当前：`add/list/update/search` 平铺命令。
- 新版：`event create/list/search/update/delete/get` 资源化命令。
- 当前无 delete/get，建议补齐完整 CRUD。

## 7. 迁移计划（不保留旧兼容）
1. 第一步：重构模块结构（store/validators/time_utils/cli）。
2. 第二步：把 CLI 改为 `event <subcommand>`。
3. 第三步：补 delete/get 和 `--format json`。
4. 第四步：按同字段语义实现 Flask Web API。
5. 第五步：更新文档与测试（覆盖新命令）。

## 8. 最小可用里程碑（建议）
- M1：`create/list/search/update` 新命令可用。
- M2：补齐 `get/delete` 与 JSON 输出。
- M3：上线 Flask 的 `POST/GET/PATCH/DELETE /api/events`。
