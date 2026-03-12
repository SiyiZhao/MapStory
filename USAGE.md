# MapStory 使用方法（CLI）

## 运行环境
- Python 3（系统自带即可）
- SQLite（Python 标准库内置 sqlite3，无需额外安装）

默认数据库文件：`mapstory.db`（可用 `--db` 自定义）。在项目根目录执行以下命令。

## 创建/写入事件
```bash
python mapstory.py add \
  --event "统一六国" \
  --time "-221" \
  --time-note "秦王政二十六年" \
  --lat 34.3 --lon 108.7 \
  --location-note "咸阳" \
  --persons "嬴政" \
  --priority fact \
  --remark "《史记·秦始皇本纪》"
```

## 更新事件（按 ID）
```bash
python mapstory.py update 1 --event "新的描述" --priority doubt
```

## 查看最近事件
```bash
python mapstory.py list --limit 50
```

## 条件检索
支持时间段、经纬度范围、人物子串、事件描述、地点备注过滤。
```bash
python mapstory.py search \
  --start-year -221 --end-year -210 \
  --lat-range 30 40 --lon-range 100 110 \
  --person "嬴政" \
  --location "咸阳"
```

## 参数说明
- `--event`：事件描述（必填）
- `--time`：公元纪年或近似 ISO 日期字符串，前缀可带负号表示公元前年份（可空）
- `--time-note`：历史纪年法注记（可空）
- `--lat`/`--lon`：经纬度（可空）
- `--location-note`：历史地名/现代行政区划等描述（可空）
- `--persons`：人物列表，逗号或分号分隔，内部会标准化为逗号+空格（可空）
- `--priority`：优先级枚举 `fact`（史实）、`doubt`（史实存疑）、`fanon`（自设）、`abridged_fact`（史实删减）（可空）
- `--remark`：出处、原文或其他备注（可空）
- `--db`：自定义 SQLite 路径，默认 `mapstory.db`

## 小提示
- 搜索时，任何未提供的过滤条件都会被忽略。
- 年份搜索使用 `--start-year` / `--end-year`，内部基于提取的前导年份整数。
- CLI 输出为简单表格，便于终端查看；可结合重定向导出结果。
