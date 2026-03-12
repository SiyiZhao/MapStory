# MapStory

MapStory 是一个历史事件数据库管理工具。方便历史研究者记录和管理历史事件、同人爱好者设计和管理自己的世界线设定，也可以用于日常事务或完全虚构故事的记录和设计。

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

- 数据库的输入、储存和更新。
- 特定时间段/地点范围/人物的检索归纳，集中显示。

### 扩展功能

- 历史纪年法与公元纪年法的转换。参考资料：https://ytliu0.github.io/ChineseCalendar/table_period_chinese.html?period=qinhanxin 
