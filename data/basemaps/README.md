# Basemap Assets

Place locally authorized basemap images here.

- `modern.jpg` / `modern.png` / `modern.jpeg` / `modern.webp` / `modern.svg`
  - Recommended source: 自然资源部/天地图“标准地图服务系统”
  - URL: https://bzdt.tianditu.gov.cn/
  - Direct use should keep the map approval number visible or otherwise marked.
  - For an interactive modern basemap instead of a static image, configure 高德 Web JS API:
    - `AMAP_JS_API_KEY`
    - `AMAP_SECURITY_JSCODE`
- `qin-han-liuhou.jpg` / `qin-han-liuhou.png` / `qin-han-liuhou.jpeg` / `qin-han-liuhou.webp` / `qin-han-liuhou.svg`
  - Recommended source: 谭其骧主编《中国历史地图集》第二册秦汉相关图幅
  - Intended use: 张良/《留侯世家》相关的秦末汉初轨迹底图
  - Use only images you are authorized to use.

Use period- or project-specific names for future historical basemaps instead of a generic `historical.*`.
Examples: `warring-states.*`, `western-han.*`, `tang-changan.*`.

Large image files are ignored by Git by default. They are local research assets.
