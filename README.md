# MapStory

MapStory 是一个历史事件数据库管理工具。方便历史研究者记录和管理历史事件、同人爱好者设计和管理自己的世界线设定，也可以用于日常事务或完全虚构故事的记录和设计。

**说明：** MapStory 为 AI 辅助开发（vibe coding）的工具，除 README 外的文档或代码均由 GitHub Copilot 生成（部分有人工参与）。

核心是一个数据库，每个条目包括以下内容：
- 时间 (Required) 
  - default 为公元纪年法，输入时允许空置
  - Optional：历史纪年法 
- 地点 (Required) 
  - default 为经纬度，输入时允许空置
  - Optional：历史地名、现代行政区划
- 人物 (Required, list) 
- 事件 (Required, str) 
- priority: 史实 > 史实（存疑） > 自设 > 史实（删减）
- 备注：出处（文献名或链接）/原文

## 功能

### 核心功能

- [x] 数据库的输入、储存和更新。
- [x] 特定时间段/地点范围/人物的检索归纳，集中显示。
- [x] 交互式输入输出。
- [ ] 按照时间排序？

### 扩展功能

时间：
- [ ] 历史纪年法与公元纪年法的转换。参考资料：https://ytliu0.github.io/ChineseCalendar/table_period_chinese.html?period=qinhanxin 
- [ ] 内置年号数据库，记录中国历史上每次年号变更的公元纪年日期。
- [ ] 计算人物年龄

导出&导入：
- [ ] 生成年表或月表，对于割据混乱时期，将不同地域的事件并排展示。-> Excel 导出和导入
- [ ] 纯文本导入（需要AI？）
- [ ] 从维基百科上得到某年事件列表并导入（需要爬虫？）

审核：
- [ ] 事件优先级的人工审核和调整。（目前为手动实现，规则是尚未审核确定时间、地点准确性的标注为“史实（存疑）”，审核无误后标注为“史实”。）

图形化界面：
- [ ] 基于 CLI 的交互式界面（如 curses）
- [x] 基于 Web 的界面（Flask MVP）

## Web UI

MapStory 目前提供一个基于 Flask 的本地 Web 界面，支持：
- 事件列表与筛选
- 新增、编辑、删除事件
- 事件详情页
- `/api/events` 与 `/api/events/<id>` JSON 接口

启动方式示例：

```bash
uv run python -c "from mapstory.ext import create_app; app = create_app(); app.run(debug=True)"
```

默认监听 `127.0.0.1:5000`。如需局域网访问，可在启动时传入 `host='0.0.0.0'`。