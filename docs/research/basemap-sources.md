# 权威底图来源与放置方式

MapStory 的轨迹页优先读取本地授权图片底图：

- 现代图：`data/basemaps/modern.jpg`、`.png`、`.jpeg`、`.webp` 或 `.svg`
- 张良/《留侯世家》秦汉历史图：`data/basemaps/qin-han-liuhou.jpg`、`.png`、`.jpeg`、`.webp` 或 `.svg`

若文件不存在，页面会回退到内置的临时矢量参照层。

## 现代图

推荐来源：自然资源部/天地图“标准地图服务系统”。

- 入口：https://bzdt.tianditu.gov.cn/
- 自然资源部说明：标准地图可免费浏览、下载；直接使用标准地图时需要标注审图号。
- 适合下载 JPG 或 EPS 版本。若只用于本地研究展示，可先保存为 `data/basemaps/modern.jpg`。

## 历史图

推荐来源：谭其骧主编《中国历史地图集》第二册（秦·西汉·东汉时期）。

这套图集是出版物，网上第三方扫描通常不能确认授权；不要把来历不明的扫描图提交进仓库。若你有合法取得的张良/《留侯世家》相关秦汉图幅图片，可放为 `data/basemaps/qin-han-liuhou.jpg`，MapStory 后续会将其作为“当时地理图”底图加载。

可考虑的相关数据源：

- CHGIS：https://chgis.fas.harvard.edu/
- 《中国历史地图集》条目信息：https://zh.wikipedia.org/wiki/中国历史地图集
