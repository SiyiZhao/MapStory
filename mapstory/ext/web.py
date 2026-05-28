"""Flask Web UI。"""

from __future__ import annotations

import os
import math
from pathlib import Path
from typing import Any, Optional

from flask import Blueprint, Flask, abort, jsonify, redirect, render_template, request, send_file, url_for
from jinja2 import DictLoader

from ..constants import DEFAULT_DB_PATH, DEFAULT_TIMEZONE, PRIORITY_CHOICES, PRIORITY_LABELS
from ..errors import InputValidationError, NotFoundError
from ..store import EventStore
from ..time import build_sort_key, format_structured_time, structured_time_from_parts
from ..validators import normalize_optional_text, normalize_persons, validate_priority

BASEMAP_LAYERS: dict[str, dict[str, Any]] = {
    "modern": {
        "title": "现代行政规划图",
        "description": "优先使用自然资源部/天地图标准地图服务下载的中国地图；未放入本地图片时显示临时矢量参照。",
        "source": "自然资源部/天地图标准地图服务系统",
        "source_url": "https://bzdt.tianditu.gov.cn/",
        "asset_hint": "data/basemaps/modern.jpg",
        "asset_key": "modern",
        "land": [
            (40.7, 105.5),
            (40.3, 108.0),
            (39.7, 110.7),
            (40.2, 113.8),
            (38.9, 116.9),
            (38.3, 121.4),
            (35.7, 120.8),
            (34.7, 121.6),
            (32.8, 120.9),
            (31.2, 119.5),
            (30.5, 116.8),
            (31.0, 113.4),
            (31.9, 110.5),
            (32.4, 107.2),
            (34.1, 105.5),
            (37.0, 105.0),
        ],
        "regions": [
            {"label": "陕西", "points": [(32.7, 105.9), (34.2, 106.1), (36.2, 106.8), (38.2, 108.0), (39.5, 109.5), (38.6, 111.1), (36.2, 110.6), (34.3, 110.2), (33.2, 108.8)]},
            {"label": "河南", "points": [(31.7, 111.0), (33.0, 110.8), (34.2, 111.4), (35.7, 112.2), (36.6, 114.0), (35.8, 116.3), (34.4, 116.8), (32.4, 115.5), (31.6, 113.5)]},
            {"label": "山西", "points": [(34.7, 110.5), (36.1, 110.7), (38.4, 111.3), (40.4, 112.1), (40.0, 114.5), (37.9, 114.2), (35.5, 113.6), (34.8, 112.0)]},
            {"label": "山东", "points": [(34.8, 115.6), (36.2, 116.1), (37.7, 117.0), (38.5, 119.2), (37.2, 121.0), (35.5, 119.7), (34.8, 118.1)]},
            {"label": "苏皖", "points": [(30.8, 116.4), (32.7, 115.7), (34.5, 116.1), (35.0, 118.2), (34.3, 120.7), (32.0, 120.6), (30.8, 119.0)]},
        ],
        "lines": [
            {
                "label": "黄河",
                "kind": "river",
                "points": [(36.4, 106.6), (36.5, 109.2), (35.6, 111.4), (34.9, 113.6), (35.2, 116.0), (36.5, 118.7)],
            },
            {
                "label": "淮河",
                "kind": "river",
                "points": [(32.6, 113.0), (32.9, 115.2), (32.7, 117.6), (33.0, 119.0)],
            },
            {
                "label": "秦岭",
                "kind": "ridge",
                "points": [(33.7, 106.4), (34.0, 108.5), (33.9, 110.5), (33.8, 112.1)],
            },
        ],
        "labels": [
            {"text": "关中平原", "lat": 34.5, "lon": 108.8, "major": True},
            {"text": "中原", "lat": 34.7, "lon": 113.5, "major": True},
            {"text": "淮泗", "lat": 33.4, "lon": 117.6, "major": False},
            {"text": "汉中盆地", "lat": 33.1, "lon": 106.9, "major": False},
        ],
    },
    "historical": {
        "title": "当时地理图",
        "description": "优先使用谭其骧主编《中国历史地图集》第二册秦汉相关图幅；未放入本地图片时显示临时矢量参照。",
        "source": "谭其骧主编《中国历史地图集》第二册（秦·西汉·东汉时期）",
        "source_url": "https://zh.wikipedia.org/wiki/%E4%B8%AD%E5%9B%BD%E5%8E%86%E5%8F%B2%E5%9C%B0%E5%9B%BE%E9%9B%86",
        "asset_hint": "data/basemaps/qin-han-liuhou.jpg",
        "asset_key": "qin-han-liuhou",
        "land": [
            (40.7, 105.5),
            (40.0, 108.7),
            (39.2, 111.6),
            (39.7, 114.4),
            (38.2, 117.4),
            (38.0, 120.6),
            (36.3, 121.5),
            (34.5, 120.9),
            (33.0, 119.9),
            (31.2, 119.0),
            (30.7, 116.4),
            (31.5, 112.4),
            (32.6, 108.2),
            (34.0, 105.7),
            (37.1, 105.2),
        ],
        "regions": [
            {"label": "秦关中", "points": [(33.6, 106.2), (34.6, 106.4), (35.6, 107.4), (35.8, 109.2), (35.0, 110.6), (34.0, 110.2), (33.6, 108.3)]},
            {"label": "韩故地", "points": [(33.4, 111.0), (34.1, 110.6), (35.0, 111.2), (35.8, 112.5), (35.4, 114.4), (34.2, 114.9), (33.4, 113.8)]},
            {"label": "魏地", "points": [(34.1, 114.0), (35.0, 113.8), (36.1, 114.4), (36.5, 115.8), (35.9, 117.1), (34.5, 116.9), (33.9, 115.4)]},
            {"label": "齐地", "points": [(35.3, 116.5), (36.7, 116.8), (38.2, 118.0), (38.4, 119.8), (37.0, 120.5), (35.7, 119.3)]},
            {"label": "楚地", "points": [(31.2, 112.1), (32.2, 113.0), (33.5, 114.4), (34.5, 116.4), (34.0, 119.1), (32.5, 119.7), (31.3, 118.0)]},
            {"label": "汉中", "points": [(32.5, 105.7), (33.2, 105.8), (34.0, 106.7), (33.6, 108.0), (32.7, 108.2), (32.3, 106.9)]},
        ],
        "lines": [
            {
                "label": "函谷-武关道",
                "kind": "road",
                "points": [(34.7, 110.9), (34.1, 110.2), (33.7, 109.1), (33.5, 110.8)],
            },
            {
                "label": "鸿沟、荥阳前线",
                "kind": "frontier",
                "points": [(35.0, 113.0), (34.8, 114.1), (34.7, 115.2), (34.5, 116.1)],
            },
            {
                "label": "黄河",
                "kind": "river",
                "points": [(36.4, 106.6), (36.5, 109.2), (35.6, 111.4), (34.9, 113.6), (35.2, 116.0), (36.5, 118.7)],
            },
        ],
        "labels": [
            {"text": "秦", "lat": 34.7, "lon": 108.7, "major": True},
            {"text": "韩故地", "lat": 34.7, "lon": 113.2, "major": True},
            {"text": "楚", "lat": 32.9, "lon": 117.4, "major": True},
            {"text": "齐", "lat": 36.8, "lon": 118.4, "major": True},
            {"text": "下邳", "lat": 34.3, "lon": 118.0, "major": False},
            {"text": "留", "lat": 34.7, "lon": 116.9, "major": False},
        ],
    },
}

BASEMAP_OPTIONS = [(key, layer["title"]) for key, layer in BASEMAP_LAYERS.items()]

BASE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4efe8;
      --panel: #fffaf2;
      --panel-strong: #fff4e4;
      --text: #24201a;
      --muted: #6c6257;
      --border: #e2d5c5;
      --accent: #1f5f4a;
      --accent-soft: #d7efe7;
      --danger: #9b3d2d;
      --shadow: 0 18px 48px rgba(41, 27, 16, 0.12);
      --radius: 18px;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(31, 95, 74, 0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(155, 61, 45, 0.10), transparent 24%),
        linear-gradient(180deg, #f9f3ea 0%, #f4efe8 100%);
      min-height: 100vh;
    }

    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    .shell {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }

    .hero {
      display: grid;
      gap: 18px;
      grid-template-columns: 1.5fr 0.8fr;
      align-items: stretch;
      margin-bottom: 18px;
    }

    .hero-card, .card {
      background: rgba(255, 250, 242, 0.88);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    .hero-card, .card, .toolbar { padding: 18px; }
    .hero-card { padding: 26px; }

    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 12px;
      color: var(--muted);
      margin: 0 0 10px;
    }

    h1, h2, h3, p { margin-top: 0; }
    h1 {
      font-size: clamp(30px, 4vw, 52px);
      line-height: 1.03;
      margin-bottom: 14px;
    }

    .summary-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      margin-top: 20px;
    }

    .stat {
      padding: 14px 16px;
      border-radius: 14px;
      background: var(--accent-soft);
      border: 1px solid rgba(31, 95, 74, 0.18);
    }

    .stat strong {
      display: block;
      font-size: 24px;
      margin-top: 4px;
    }

    .actions, .detail-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }

    .button, button {
      border: 0;
      border-radius: 999px;
      padding: 11px 16px;
      font-weight: 700;
      cursor: pointer;
      background: var(--accent);
      color: white;
      box-shadow: 0 12px 24px rgba(31, 95, 74, 0.18);
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .button.secondary, button.secondary {
      background: white;
      color: var(--accent);
      border: 1px solid rgba(31, 95, 74, 0.22);
      box-shadow: none;
    }

    .button.danger, button.danger {
      background: var(--danger);
      box-shadow: 0 12px 24px rgba(155, 61, 45, 0.16);
    }

    .sidebar {
      display: grid;
      gap: 14px;
      align-content: start;
    }

    .sidebar .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(31, 95, 74, 0.08);
      color: var(--accent);
      font-size: 14px;
    }

    .toolbar form {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      align-items: end;
    }

    label {
      display: grid;
      gap: 6px;
      font-size: 14px;
      color: var(--muted);
    }

    input, textarea, select {
      width: 100%;
      padding: 11px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.92);
      color: var(--text);
      font: inherit;
    }

    textarea { min-height: 120px; resize: vertical; }
    .textarea-remark { min-height: 120px; }

    .cards {
      display: grid;
      gap: 14px;
    }

    .event-card {
      padding: 18px;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.82);
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 12px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 5px 10px;
      border-radius: 999px;
      background: rgba(31, 95, 74, 0.10);
      color: var(--accent);
      font-size: 13px;
    }

    .badge.custom { background: rgba(38, 96, 198, 0.14); color: #1f4f9b; }
    .badge.warning { background: rgba(155, 61, 45, 0.12); color: var(--danger); }

    .detail-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      margin: 16px 0;
    }

    .detail-grid.five-col {
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }

    .detail-item {
      padding: 14px 16px;
      border-radius: 14px;
      background: var(--panel-strong);
      border: 1px solid var(--border);
    }

    .detail-item span {
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 6px;
    }

    .muted { color: var(--muted); }
    .empty-state {
      padding: 28px;
      text-align: center;
      border: 1px dashed var(--border);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.55);
    }

    .map-panel {
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.55fr);
      align-items: start;
    }

    .route-map {
      width: 100%;
      min-height: 520px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background:
        linear-gradient(rgba(31, 95, 74, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(31, 95, 74, 0.08) 1px, transparent 1px),
        #fdf8ef;
      background-size: 48px 48px;
    }

    .interactive-map {
      width: 100%;
      min-height: 560px;
      border: 1px solid var(--border);
      border-radius: 16px;
      overflow: hidden;
      background: #eef3ed;
    }

    .map-notice {
      padding: 18px;
      border: 1px dashed var(--border);
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.72);
    }

    .map-stack {
      display: grid;
      gap: 12px;
    }

    .basemap-region {
      fill: rgba(214, 196, 154, 0.28);
      stroke: rgba(107, 93, 70, 0.34);
      stroke-width: 1.4;
    }

    .basemap-land {
      fill: rgba(246, 237, 216, 0.80);
      stroke: rgba(95, 84, 66, 0.38);
      stroke-width: 2.2;
    }

    .basemap-raster {
      opacity: 0.72;
    }

    .basemap-historical .basemap-region {
      fill: rgba(155, 61, 45, 0.13);
      stroke: rgba(155, 61, 45, 0.30);
    }

    .basemap-historical .basemap-land {
      fill: rgba(246, 232, 206, 0.82);
      stroke: rgba(126, 84, 55, 0.42);
    }

    .basemap-line {
      fill: none;
      stroke-width: 2.2;
      stroke-linecap: round;
      stroke-linejoin: round;
      opacity: 0.78;
    }

    .basemap-line.river { stroke: #547b99; }
    .basemap-line.ridge { stroke: rgba(86, 94, 62, 0.58); stroke-dasharray: 7 6; }
    .basemap-line.road { stroke: rgba(123, 77, 45, 0.62); stroke-dasharray: 6 5; }
    .basemap-line.frontier { stroke: rgba(155, 61, 45, 0.52); stroke-dasharray: 4 5; }

    .basemap-label {
      fill: rgba(93, 80, 62, 0.78);
      font-size: 15px;
      font-weight: 700;
      text-anchor: middle;
      paint-order: stroke;
      stroke: rgba(253, 248, 239, 0.78);
      stroke-width: 4px;
      stroke-linejoin: round;
    }

    .basemap-label.minor {
      font-size: 12px;
      font-weight: 600;
      fill: rgba(93, 80, 62, 0.62);
    }

    .basemap-caption {
      fill: rgba(108, 98, 87, 0.76);
      font-size: 13px;
    }

    .route-line {
      fill: none;
      stroke: var(--accent);
      stroke-width: 3.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .route-point {
      fill: #fffaf2;
      stroke: var(--danger);
      stroke-width: 2.5;
    }

    .route-marker {
      cursor: pointer;
      outline: none;
    }

    .route-marker:hover .route-point,
    .route-marker:focus .route-point,
    .route-marker.active .route-point {
      fill: var(--accent-soft);
      stroke-width: 4;
    }

    .route-offset-line {
      stroke: rgba(155, 61, 45, 0.42);
      stroke-width: 1.5;
      stroke-dasharray: 3 3;
    }

    .route-number {
      fill: var(--text);
      font-size: 12px;
      font-weight: 700;
      text-anchor: middle;
      dominant-baseline: middle;
    }

    .route-list {
      display: grid;
      gap: 10px;
      max-height: 560px;
      overflow: auto;
      padding-right: 4px;
    }

    .route-item {
      display: grid;
      gap: 6px;
      padding: 12px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.78);
      transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
      cursor: pointer;
    }

    .route-item.active {
      border-color: rgba(31, 95, 74, 0.56);
      background: rgba(215, 239, 231, 0.54);
      box-shadow: 0 0 0 3px rgba(31, 95, 74, 0.12);
    }

    .route-item header {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .route-index {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: var(--accent);
      color: white;
      font-weight: 700;
      flex: 0 0 auto;
    }

    @media (max-width: 860px) {
      .hero { grid-template-columns: 1fr; }
      .shell { width: min(100vw - 20px, 1180px); padding-top: 16px; }
      .hero-card, .sidebar, .card, .toolbar { padding: 16px; }
      .detail-grid.five-col { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
      .map-panel { grid-template-columns: 1fr; }
      .route-map { min-height: 380px; }
      .interactive-map { min-height: 420px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
"""

LIST_TEMPLATE = """
{% extends 'base.html' %}
{% block content %}
<section class="hero">
  <article class="hero-card">
    <p class="eyebrow">MapStory Web UI</p>
    <h1>时间、地点与人物，放进一个可浏览的故事面板里。</h1>
    <p class="muted">这个界面直接复用现有事件库，支持新增、筛选、查看、编辑和删除，也提供同样语义的 JSON API。</p>
    <div class="actions">
      <a class="button" href="{{ url_for('web.new_event') }}">新增事件</a>
      <a class="button secondary" href="{{ url_for('web.list_events') }}">刷新列表</a>
      <a class="button secondary" href="{{ url_for('web.event_map', person='张良') }}">张良轨迹</a>
      <a class="button secondary" href="{{ url_for('web.api_events') }}">查看 API</a>
    </div>
    <div class="summary-grid">
      <div class="stat"><span class="muted">当前记录</span><strong>{{ total }}</strong></div>
      <div class="stat"><span class="muted">时间排序</span><strong>开启</strong></div>
      <div class="stat"><span class="muted">默认时区</span><strong>{{ timezone }}</strong></div>
    </div>
  </article>
  <aside class="hero-card sidebar">
    <div class="pill">Web MVP</div>
    <p><strong>适合本地自托管</strong></p>
    <p class="muted">支持浏览器访问，桌面和手机都能操作；底层仍然使用同一套 SQLite 存储。</p>
    <p class="muted">列表页的筛选项与 API 查询参数保持一致，便于脚本和页面同时使用。</p>
  </aside>
</section>

<section class="card toolbar">
  <form method="get">
    <label>关键词
      <input name="q" value="{{ filters.q or '' }}" placeholder="事件">
    </label>
    <label>地点
      <input name="location" value="{{ filters.location or '' }}" placeholder="武汉、武昌、长安">
    </label>
    <label>人物
      <input name="person" value="{{ filters.person or '' }}" placeholder="张三, 李四">
    </label>
    <label>优先级
      <select name="priority">
        <option value="">全部</option>
        {% for label in priority_labels %}
        <option value="{{ label }}" {% if filters.priority == label %}selected{% endif %}>{{ label }}</option>
        {% endfor %}
      </select>
    </label>
    <label>排序
      <select name="order">
        <option value="time" {% if filters.order != 'created' %}selected{% endif %}>时间</option>
        <option value="created" {% if filters.order == 'created' %}selected{% endif %}>创建时间</option>
      </select>
    </label>
    <label>结果数
      <input name="limit" type="number" min="1" max="200" value="{{ filters.limit }}">
    </label>
    <button type="submit">筛选</button>
  </form>
</section>

<section class="cards">
  {% if events %}
    {% for event in events %}
    <article class="event-card">
      <div class="meta">
        <span class="badge">#{{ event.id }}</span>
        <span>{{ event.time_display or '未填写时间' }}{% if event.time_note %} · {{ event.time_note }}{% endif %}</span>
        <span>{{ event.location_display or '未填写地点' }}</span>
        <span class="badge{% if event.priority == '自设' %} custom{% elif event.priority and event.priority != '史实' %} warning{% endif %}">{{ event.priority or '未设置优先级' }}</span>
      </div>
      <h3><a href="{{ url_for('web.event_detail', event_id=event.id) }}">{{ event.event }}</a></h3>
      <p class="muted">{{ event.persons_display or '未填写人物' }}</p>
      {% if event.remark %}
      <p class="muted">{{ event.remark }}</p>
      {% endif %}
    </article>
    {% endfor %}
  {% else %}
    <div class="empty-state">
      <h3>当前没有匹配的事件</h3>
      <p class="muted">可以先新增一条事件，或者放宽筛选条件。</p>
    </div>
  {% endif %}
</section>
{% endblock %}
"""

MAP_TEMPLATE = """
{% extends 'base.html' %}
{% block content %}
<section class="hero">
  <article class="hero-card">
    <p class="eyebrow">MapStory Map</p>
    <h1>{{ filters.person or '全部人物' }}的地理轨迹</h1>
    <p class="muted">按结构化时间排序，连接所有带经纬度的事件地点；可用筛选项切换人物、地点或年份范围。</p>
    <div class="actions">
      <a class="button secondary" href="{{ url_for('web.list_events') }}">返回列表</a>
      <a class="button secondary" href="{{ url_for('web.api_events', person=filters.person, order='time', limit=filters.limit) }}">查看 API</a>
    </div>
  </article>
  <aside class="hero-card sidebar">
    <div class="pill">轨迹点 {{ map_data.points|length }}</div>
    <div class="pill">{{ map_data.basemap.title }}</div>
    <p><strong>{{ map_data.bounds_label }}</strong></p>
    <p class="muted">{{ map_data.basemap.description }}</p>
    <p class="muted">来源：<a href="{{ map_data.basemap.source_url }}" target="_blank" rel="noreferrer">{{ map_data.basemap.source }}</a></p>
    {% if map_data.basemap.image_url %}
    <p class="muted">当前使用本地权威图片底图。</p>
    {% else %}
    <p class="muted">尚未找到 {{ map_data.basemap.asset_hint }}，当前显示临时矢量参照。</p>
    {% endif %}
    <p class="muted">同一地点的重复事件会按时间保留，方便观察停留与回返。</p>
  </aside>
</section>

<section class="card toolbar">
  <form method="get">
    <label>人物
      <input name="person" value="{{ filters.person or '' }}" placeholder="张良">
    </label>
    <label>关键词
      <input name="q" value="{{ filters.q or '' }}" placeholder="事件">
    </label>
    <label>地点
      <input name="location" value="{{ filters.location or '' }}" placeholder="下邳、咸阳、留">
    </label>
    <label>起始年
      <input name="start_year" type="number" value="{{ filters.start_year if filters.start_year is not none else '' }}">
    </label>
    <label>结束年
      <input name="end_year" type="number" value="{{ filters.end_year if filters.end_year is not none else '' }}">
    </label>
    <label>结果数
      <input name="limit" type="number" min="1" max="200" value="{{ filters.limit }}">
    </label>
    <label>底图
      <select name="basemap">
        {% for key, label in basemap_options %}
        <option value="{{ key }}" {% if filters.basemap == key %}selected{% endif %}>{{ label }}</option>
        {% endfor %}
      </select>
    </label>
    <button type="submit">绘制</button>
  </form>
</section>

<section class="card map-panel">
  {% if map_data.points %}
  {% if map_data.interactive.enabled %}
  <div id="amap-container" class="interactive-map" aria-label="高德互动地图"></div>
  {% else %}
  <div class="map-stack">
    {% if filters.basemap == 'modern' %}
    <div class="map-notice">
      <h3>现代互动底图需要高德 Web JS API 配置</h3>
      <p class="muted">设置环境变量 `AMAP_JS_API_KEY` 和 `AMAP_SECURITY_JSCODE` 后重启服务，即可在这里显示可缩放、可拖拽的高德底图。</p>
      <p class="muted">当前继续显示临时矢量参照。</p>
    </div>
    {% endif %}
    <svg class="route-map" viewBox="0 0 {{ map_data.width }} {{ map_data.height }}" role="img" aria-label="{{ filters.person or '事件' }}轨迹地图">
      <g class="basemap basemap-{{ filters.basemap }}">
        {% if map_data.basemap.image_url %}
        <image class="basemap-raster" href="{{ map_data.basemap.image_url }}" x="0" y="0" width="{{ map_data.width }}" height="{{ map_data.height }}" preserveAspectRatio="xMidYMid meet">
          <title>{{ map_data.basemap.title }}</title>
        </image>
        {% endif %}
        <path class="basemap-land" d="{{ map_data.basemap.land_path_d }}">
          <title>{{ map_data.basemap.title }}</title>
        </path>
        {% for region in map_data.basemap.regions %}
        <path class="basemap-region" d="{{ region.path_d }}">
          <title>{{ region.label }}</title>
        </path>
        {% endfor %}
        {% for line in map_data.basemap.lines %}
        <path class="basemap-line {{ line.kind }}" d="{{ line.path_d }}">
          <title>{{ line.label }}</title>
        </path>
        {% endfor %}
        {% for label in map_data.basemap.labels %}
        <text class="basemap-label{% if not label.major %} minor{% endif %}" x="{{ label.x }}" y="{{ label.y }}">{{ label.text }}</text>
        {% endfor %}
        <text class="basemap-caption" x="24" y="{{ map_data.height - 24 }}">底图：{{ map_data.basemap.title }}</text>
      </g>
      <path class="route-line" d="{{ map_data.path_d }}"></path>
      {% for point in map_data.points %}
      <g class="route-marker" data-route-index="{{ loop.index }}" tabindex="0" role="button" aria-label="查看第 {{ loop.index }} 个事件">
        {% if point.offset %}
        <line class="route-offset-line" x1="{{ point.base_x }}" y1="{{ point.base_y }}" x2="{{ point.x }}" y2="{{ point.y }}"></line>
        {% endif %}
        <circle class="route-point" cx="{{ point.x }}" cy="{{ point.y }}" r="13">
          <title>{{ point.time_display }} {{ point.location_note }}：{{ point.event }}</title>
        </circle>
        <text class="route-number" x="{{ point.x }}" y="{{ point.y }}">{{ loop.index }}</text>
      </g>
      {% endfor %}
    </svg>
  </div>
  {% endif %}
  <aside class="route-list">
    {% for point in map_data.points %}
    <article class="route-item" id="route-item-{{ loop.index }}" data-route-index="{{ loop.index }}" tabindex="0" role="button" aria-label="定位第 {{ loop.index }} 个地图点">
      <header>
        <span class="route-index">{{ loop.index }}</span>
        <strong>{{ point.time_display or '未填写时间' }}</strong>
      </header>
      <div>{{ point.event }}</div>
      <div class="muted">{{ point.location_display }}</div>
      {% if point.time_note %}
      <div class="muted">{{ point.time_note }}</div>
      {% endif %}
    </article>
    {% endfor %}
  </aside>
  {% else %}
  <div class="empty-state">
    <h3>没有可绘制的坐标事件</h3>
    <p class="muted">请确认事件包含经纬度，或放宽人物、地点和年份筛选。</p>
  </div>
  {% endif %}
</section>
{% if map_data.points %}
<script>
  function setActiveRoute(index, options = {}) {
    document.querySelectorAll(".route-item.active").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".route-marker.active").forEach((marker) => marker.classList.remove("active"));
    const item = document.getElementById(`route-item-${index}`);
    const marker = document.querySelector(`.route-marker[data-route-index="${index}"]`);
    if (item) {
      item.classList.add("active");
      if (options.scrollList !== false) {
        item.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
    if (marker) {
      marker.classList.add("active");
      if (options.focusMarker) {
        marker.focus({ preventScroll: true });
      }
    }
  }

  function focusRouteItem(index) {
    setActiveRoute(index, { scrollList: true });
  }

  document.querySelectorAll(".route-marker").forEach((marker) => {
    const index = marker.dataset.routeIndex;
    marker.addEventListener("click", () => setActiveRoute(index, { scrollList: true }));
    marker.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setActiveRoute(index, { scrollList: true });
      }
    });
  });

  document.querySelectorAll(".route-item").forEach((item) => {
    const index = item.dataset.routeIndex;
    item.addEventListener("click", () => setActiveRoute(index, { scrollList: false, focusMarker: true }));
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setActiveRoute(index, { scrollList: false, focusMarker: true });
      }
    });
  });
</script>
{% endif %}
{% if map_data.interactive.enabled %}
<script>
  window._AMapSecurityConfig = { securityJsCode: "{{ map_data.interactive.security_jscode }}" };
</script>
<script src="https://webapi.amap.com/loader.js"></script>
<script>
  const mapStoryPoints = {{ map_data.points|tojson }};
  const mapStoryKey = "{{ map_data.interactive.key }}";

  function transformLat(x, y) {
    let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
    ret += (20.0 * Math.sin(6.0 * x * Math.PI) + 20.0 * Math.sin(2.0 * x * Math.PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(y * Math.PI) + 40.0 * Math.sin(y / 3.0 * Math.PI)) * 2.0 / 3.0;
    ret += (160.0 * Math.sin(y / 12.0 * Math.PI) + 320 * Math.sin(y * Math.PI / 30.0)) * 2.0 / 3.0;
    return ret;
  }

  function transformLon(x, y) {
    let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
    ret += (20.0 * Math.sin(6.0 * x * Math.PI) + 20.0 * Math.sin(2.0 * x * Math.PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(x * Math.PI) + 40.0 * Math.sin(x / 3.0 * Math.PI)) * 2.0 / 3.0;
    ret += (150.0 * Math.sin(x / 12.0 * Math.PI) + 300.0 * Math.sin(x / 30.0 * Math.PI)) * 2.0 / 3.0;
    return ret;
  }

  function wgs84ToGcj02(lon, lat) {
    const a = 6378245.0;
    const ee = 0.00669342162296594323;
    let dLat = transformLat(lon - 105.0, lat - 35.0);
    let dLon = transformLon(lon - 105.0, lat - 35.0);
    const radLat = lat / 180.0 * Math.PI;
    let magic = Math.sin(radLat);
    magic = 1 - ee * magic * magic;
    const sqrtMagic = Math.sqrt(magic);
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * Math.PI);
    dLon = (dLon * 180.0) / (a / sqrtMagic * Math.cos(radLat) * Math.PI);
    return [lon + dLon, lat + dLat];
  }

  AMapLoader.load({
    key: mapStoryKey,
    version: "2.0",
    plugins: ["AMap.Scale", "AMap.ToolBar"],
  }).then((AMap) => {
    const path = mapStoryPoints.map((point) => wgs84ToGcj02(point.lon, point.lat));
    const map = new AMap.Map("amap-container", {
      viewMode: "2D",
      zoom: 6,
      center: path[Math.floor(path.length / 2)],
      mapStyle: "amap://styles/normal",
    });
    map.addControl(new AMap.Scale());
    map.addControl(new AMap.ToolBar());

    const polyline = new AMap.Polyline({
      path,
      strokeColor: "#1f5f4a",
      strokeOpacity: 0.92,
      strokeWeight: 5,
      lineJoin: "round",
    });
    map.add(polyline);

    mapStoryPoints.forEach((point, index) => {
      const marker = new AMap.Marker({
        position: path[index],
        title: `${index + 1}. ${point.event}`,
        label: {
          content: String(index + 1),
          direction: "center",
        },
      });
      marker.on("click", () => {
        focusRouteItem(index + 1);
        const info = new AMap.InfoWindow({
          content: `<strong>${index + 1}. ${point.time_display || ""}</strong><br>${point.event}<br>${point.location_display || ""}`,
          offset: new AMap.Pixel(0, -30),
        });
        info.open(map, marker.getPosition());
      });
      map.add(marker);
    });
    map.setFitView([polyline], false, [50, 50, 50, 50]);
  }).catch(() => {
    const container = document.getElementById("amap-container");
    if (container) {
      container.innerHTML = "<div class='map-notice'><h3>高德地图加载失败</h3><p class='muted'>请检查网络、AMAP_JS_API_KEY 和 AMAP_SECURITY_JSCODE 配置。</p></div>";
    }
  });
</script>
{% endif %}
{% endblock %}
"""

FORM_TEMPLATE = """
{% extends 'base.html' %}
{% block content %}
<section class="hero">
  <article class="hero-card">
    <p class="eyebrow">{{ title }}</p>
    <h1>{{ heading }}</h1>
    <p class="muted">{{ description }}</p>
  </article>
  <aside class="hero-card sidebar">
    <div class="pill">填写提示</div>
    <p class="muted">时间支持 `YYYY`、`YYYY-MM`、`YYYY-MM-DD`。</p>
    <p class="muted">人物可用逗号或分号分隔。</p>
    <p class="muted">坐标超出范围时会返回校验错误。</p>
  </aside>
</section>

<section class="card">
  <form method="post">
    <div class="detail-grid">
      <label>事件描述
        <input name="event" required value="{{ form.event or '' }}" placeholder="输入事件描述">
      </label>
      <label>时间
        <input name="time" value="{{ form.time or '' }}" placeholder="2024-01-15 或 2024-01-15 08:30">
      </label>
      <label>时间备注
        <input name="time_note" value="{{ form.time_note or '' }}" placeholder="历史纪年、原始标记等">
      </label>
      <label>纬度
        <input name="lat" value="{{ form.lat or '' }}" placeholder="30.6">
      </label>
      <label>经度
        <input name="lon" value="{{ form.lon or '' }}" placeholder="114.3">
      </label>
      <label>地点备注
        <input name="location_note" value="{{ form.location_note or '' }}" placeholder="武汉 / 武昌">
      </label>
      <label>人物
        <input name="persons" value="{{ form.persons or '' }}" placeholder="张三, 李四">
      </label>
      <label>优先级
        <select name="priority">
          <option value="">未设置</option>
          {% for key, label in priority_choices %}
          <option value="{{ key }}" {% if form.priority == key or form.priority == label %}selected{% endif %}>{{ label }}</option>
          {% endfor %}
        </select>
      </label>
    </div>
    <label>备注 / 来源
      <textarea class="textarea-remark" name="remark" placeholder="出处、链接或补充说明">{{ form.remark or '' }}</textarea>
    </label>
    {% if error %}
    <p class="badge warning">{{ error }}</p>
    {% endif %}
    <div class="detail-actions">
      <button type="submit">保存</button>
      <a class="button secondary" href="{{ url_for('web.list_events') }}">返回列表</a>
    </div>
  </form>
</section>
{% endblock %}
"""

DETAIL_TEMPLATE = """
{% extends 'base.html' %}
{% block content %}
<section class="hero">
  <article class="hero-card">
    <p class="eyebrow">事件详情</p>
    <h1>{{ event.event }}</h1>
    <p class="muted">记录编号 #{{ event.id }}，更新时间 {{ event.updated_at or '未知' }}</p>
    <div class="actions">
      <a class="button" href="{{ url_for('web.edit_event', event_id=event.id) }}">编辑</a>
      <a class="button secondary" href="{{ url_for('web.list_events') }}">返回列表</a>
    </div>
  </article>
  <aside class="hero-card sidebar">
    <div class="pill">API</div>
    <p class="muted">{{ api_url }}</p>
    <p class="muted">JSON 与页面共用同一条数据记录。</p>
  </aside>
</section>

<section class="card">
  <div class="detail-grid five-col">
    <div class="detail-item"><span>时间</span>{{ event.time_display or '未填写' }}</div>
    <div class="detail-item"><span>时间备注</span>{{ event.time_note or '未填写' }}</div>
    <div class="detail-item"><span>地点</span>{{ event.location_display or '未填写' }}</div>
    <div class="detail-item"><span>人物</span>{{ event.persons_display or '未填写' }}</div>
    <div class="detail-item"><span>优先级</span>{{ event.priority or '未设置' }}</div>
  </div>
  <div class="event-card">
    <h3>备注 / 来源</h3>
    <p>{{ event.remark or '未填写' }}</p>
  </div>
  <div class="detail-actions">
    <form method="post" action="{{ url_for('web.delete_event', event_id=event.id) }}" onsubmit="return confirm('确定删除这条事件吗？');">
      <button class="danger" type="submit">删除</button>
    </form>
    <a class="button secondary" href="{{ api_url }}">查看 JSON</a>
  </div>
</section>
{% endblock %}
"""


def create_app(db_path: Optional[str | Path] = None, *, test_config: Optional[dict[str, Any]] = None) -> Flask:
    """创建 Web 应用。"""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="mapstory-web",
        DB_PATH=str(db_path or DEFAULT_DB_PATH),
        BASEMAP_DIR="data/basemaps",
        AMAP_JS_API_KEY=os.environ.get("AMAP_JS_API_KEY"),
        AMAP_SECURITY_JSCODE=os.environ.get("AMAP_SECURITY_JSCODE"),
        TIMEZONE=DEFAULT_TIMEZONE,
    )
    if test_config:
        app.config.update(test_config)

    app.jinja_loader = DictLoader(
        {
            "base.html": BASE_TEMPLATE,
            "events/list.html": LIST_TEMPLATE,
            "events/map.html": MAP_TEMPLATE,
            "events/form.html": FORM_TEMPLATE,
            "events/detail.html": DETAIL_TEMPLATE,
        }
    )

    web = Blueprint("web", __name__)

    @app.before_request
    def _attach_store() -> None:
        """为当前请求创建数据库访问对象。"""
        app.extensions["mapstory_store"] = EventStore(Path(app.config["DB_PATH"]))

    @app.teardown_request
    def _close_store(_exc: Optional[BaseException]) -> None:
        """关闭请求级数据库连接。"""
        store = app.extensions.pop("mapstory_store", None)
        if store is not None:
            store.conn.close()

    @app.errorhandler(InputValidationError)
    def _handle_validation_error(exc: InputValidationError):
        """返回输入校验失败响应。"""
        return _api_error("VALIDATION_ERROR", str(exc), 400)

    @app.errorhandler(NotFoundError)
    def _handle_not_found_error(exc: NotFoundError):
        """返回资源不存在响应。"""
        return _api_error("NOT_FOUND", str(exc), 404)

    @app.errorhandler(RuntimeError)
    def _handle_runtime_error(exc: RuntimeError):
        """返回数据库错误响应。"""
        return _api_error("DATABASE_ERROR", str(exc), 500)

    @app.route("/")
    def home():
        """首页重定向到事件列表。"""
        return redirect(url_for("web.list_events"))

    @web.route("/events")
    def list_events():
        """渲染事件列表页。"""
        store = _get_store(app)
        filters = _parse_filters(request.args)
        rows = store.search_events(
            start_year=filters["start_year"],
            end_year=filters["end_year"],
            lat_range=filters["lat_range"],
            lon_range=filters["lon_range"],
            person_contains=filters["person"],
            event_contains=filters["q"],
            location_contains=filters["location"],
            priority=filters["priority"],
            limit=filters["limit"],
            offset=filters["offset"],
            order=filters["order"],
        )
        events = [_decorate_row(row, app.config["TIMEZONE"]) for row in rows]
        return render_template(
            "events/list.html",
            title="MapStory Web",
            total=len(events),
            timezone=app.config["TIMEZONE"],
            filters=filters,
            events=events,
            priority_labels=sorted(PRIORITY_LABELS),
        )

    @web.route("/events/map")
    def event_map():
        """渲染按时间连接的事件地理轨迹。"""
        store = _get_store(app)
        filters = _parse_filters(request.args)
        if not filters["person"] and not request.args:
            filters["person"] = "张良"
        rows = store.search_events(
            start_year=filters["start_year"],
            end_year=filters["end_year"],
            lat_range=filters["lat_range"],
            lon_range=filters["lon_range"],
            person_contains=filters["person"],
            event_contains=filters["q"],
            location_contains=filters["location"],
            priority=filters["priority"],
            limit=filters["limit"],
            offset=filters["offset"],
            order="time",
        )
        events = [_decorate_row(row, app.config["TIMEZONE"]) for row in rows]
        return render_template(
            "events/map.html",
            title="MapStory 轨迹地图",
            filters=filters,
            map_data=_build_map_data(
                events,
                filters["basemap"],
                image_url=url_for("web.basemap_image", key=filters["basemap"])
                if _find_basemap_image(app, filters["basemap"])
                else None,
                interactive=_interactive_map_config(app, filters["basemap"]),
            ),
            basemap_options=BASEMAP_OPTIONS,
        )

    @web.route("/basemaps/<key>")
    def basemap_image(key: str):
        """提供本地权威底图图片。"""
        path = _find_basemap_image(app, key)
        if path is None:
            abort(404)
        return send_file(path)

    @web.route("/events/new", methods=["GET", "POST"])
    def new_event():
        """渲染并处理新增事件页面。"""
        if request.method == "POST":
            store = _get_store(app)
            payload = _event_payload_from_mapping(request.form, partial=False)
            event_id = store.create_event(**payload)
            return redirect(url_for("web.event_detail", event_id=event_id))
        return render_template(
            "events/form.html",
            title="新增事件",
            heading="新增一条事件",
            description="把时间、地点、人物和备注一次写清楚。",
            form={},
            error=None,
            priority_choices=PRIORITY_CHOICES.items(),
        )

    @web.route("/events/<int:event_id>")
    def event_detail(event_id: int):
        """渲染事件详情页。"""
        store = _get_store(app)
        row = store.get_event(event_id)
        event = _decorate_row(row, app.config["TIMEZONE"])
        return render_template(
            "events/detail.html",
            title=event["event"],
            event=event,
            api_url=url_for("web.api_event_detail", event_id=event_id),
        )

    @web.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
    def edit_event(event_id: int):
        """渲染并处理编辑事件页面。"""
        store = _get_store(app)
        row = store.get_event(event_id)
        if request.method == "POST":
            payload = _event_payload_from_mapping(request.form, partial=True)
            updated = store.update_event(event_id, **payload)
            if updated == 0:
                raise NotFoundError(f"事件不存在或无变化: {event_id}")
            return redirect(url_for("web.event_detail", event_id=event_id))
        return render_template(
            "events/form.html",
            title="编辑事件",
            heading=f"编辑事件 #{event_id}",
            description="只修改需要变更的字段即可。",
            form=_row_to_form(row),
            error=None,
            priority_choices=PRIORITY_CHOICES.items(),
        )

    @web.route("/events/<int:event_id>/delete", methods=["POST"])
    def delete_event(event_id: int):
        """删除事件后回到列表页。"""
        store = _get_store(app)
        store.delete_event(event_id)
        return redirect(url_for("web.list_events"))

    @web.route("/api/events", methods=["GET", "POST"])
    def api_events():
        """事件集合 API。"""
        store = _get_store(app)
        if request.method == "POST":
            payload = _event_payload_from_json(request.get_json(silent=True) or {}, partial=False)
            event_id = store.create_event(**payload)
            row = store.get_event(event_id)
            return _api_success(_row_to_payload(row, app.config["TIMEZONE"]), 201)

        filters = _parse_filters(request.args)
        rows = store.search_events(
            start_year=filters["start_year"],
            end_year=filters["end_year"],
            lat_range=filters["lat_range"],
            lon_range=filters["lon_range"],
            person_contains=filters["person"],
            event_contains=filters["q"],
            location_contains=filters["location"],
            priority=filters["priority"],
            limit=filters["limit"],
            offset=filters["offset"],
            order=filters["order"],
        )
        return _api_success([_row_to_payload(row, app.config["TIMEZONE"]) for row in rows])

    @web.route("/api/events/<int:event_id>", methods=["GET", "PATCH", "DELETE"])
    def api_event_detail(event_id: int):
        """单条事件 API。"""
        store = _get_store(app)
        if request.method == "GET":
            row = store.get_event(event_id)
            return _api_success(_row_to_payload(row, app.config["TIMEZONE"]))
        if request.method == "PATCH":
            payload = _event_payload_from_json(request.get_json(silent=True) or {}, partial=True)
            updated = store.update_event(event_id, **payload)
            if updated == 0:
                raise NotFoundError(f"事件不存在或无变化: {event_id}")
            row = store.get_event(event_id)
            return _api_success(_row_to_payload(row, app.config["TIMEZONE"]))
        store.delete_event(event_id)
        return _api_success({"deleted": True})

    app.register_blueprint(web)
    return app


def _get_store(app: Flask) -> EventStore:
    """获取请求级数据库对象。"""
    store = app.extensions.get("mapstory_store")
    if store is None:
        store = EventStore(Path(app.config["DB_PATH"]))
        app.extensions["mapstory_store"] = store
    return store


def _find_basemap_image(app: Flask, key: str) -> Optional[Path]:
    """查找本地权威底图图片。"""
    if key not in BASEMAP_LAYERS:
        return None
    basemap_dir = Path(app.config["BASEMAP_DIR"])
    if not basemap_dir.is_absolute():
        basemap_dir = basemap_dir.resolve()
    asset_key = BASEMAP_LAYERS[key].get("asset_key", key)
    for suffix in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        candidate = basemap_dir / f"{asset_key}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def _interactive_map_config(app: Flask, basemap: str) -> dict[str, Any]:
    """返回现代互动地图配置。"""
    key = app.config.get("AMAP_JS_API_KEY")
    security_jscode = app.config.get("AMAP_SECURITY_JSCODE")
    enabled = basemap == "modern" and bool(key) and bool(security_jscode)
    return {
        "enabled": enabled,
        "provider": "amap" if basemap == "modern" else None,
        "key": key if enabled else "",
        "security_jscode": security_jscode if enabled else "",
    }


def _api_success(data: Any, status_code: int = 200):
    """构造 JSON 成功响应。"""
    return jsonify({"ok": True, "data": data}), status_code


def _api_error(code: str, message: str, status_code: int):
    """构造 JSON 错误响应。"""
    return jsonify({"ok": False, "error": {"code": code, "message": message}}), status_code


def _parse_filters(args):
    """解析列表和搜索参数。"""
    limit = _coerce_int(args.get("limit"), default=20, minimum=1, maximum=200)
    offset = _coerce_int(args.get("offset"), default=0, minimum=0)
    start_year = _coerce_int(args.get("start_year"), allow_none=True)
    end_year = _coerce_int(args.get("end_year"), allow_none=True)
    lat_range = _coerce_range(args.get("lat_min"), args.get("lat_max"))
    lon_range = _coerce_range(args.get("lon_min"), args.get("lon_max"))
    priority = normalize_optional_text(args.get("priority"))
    if priority:
        priority = validate_priority(priority)
    basemap = args.get("basemap") or "modern"
    if basemap not in BASEMAP_LAYERS:
        basemap = "modern"
    return {
        "q": normalize_optional_text(args.get("q")),
        "person": normalize_optional_text(args.get("person")),
        "location": normalize_optional_text(args.get("location")),
        "priority": priority,
        "basemap": basemap,
        "order": args.get("order", "time") if args.get("order", "time") in {"time", "created"} else "time",
        "limit": limit,
        "offset": offset,
        "start_year": start_year,
        "end_year": end_year,
        "lat_range": lat_range,
        "lon_range": lon_range,
    }


def _coerce_int(value, *, default: Optional[int] = None, minimum: Optional[int] = None, maximum: Optional[int] = None, allow_none: bool = False):
    """把字符串参数转换为整数。"""
    if value in (None, ""):
        return None if allow_none else default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"无法解析整数: {value}") from exc
    if minimum is not None and number < minimum:
        raise InputValidationError(f"数值不能小于 {minimum}")
    if maximum is not None and number > maximum:
        raise InputValidationError(f"数值不能大于 {maximum}")
    return number


def _coerce_float(value):
    """把字符串参数转换为浮点数。"""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"无法解析数值: {value}") from exc


def _coerce_range(min_value, max_value):
    """把字符串参数转换为二元区间。"""
    if min_value in (None, "") and max_value in (None, ""):
        return None
    return (_coerce_float(min_value), _coerce_float(max_value))


def _event_payload_from_form(form, *, partial: bool = False):
    """从表单构造数据库写入参数。"""
    return _event_payload_from_mapping(form, partial=partial)


def _event_payload_from_json(data, *, partial: bool = False):
    """从 JSON 构造数据库写入参数。"""
    return _event_payload_from_mapping(data, partial=partial)


def _event_payload_from_mapping(mapping, *, partial: bool = False):
    """从通用映射构造数据库写入参数。"""
    payload = {}
    if not partial or "time" in mapping or "time_iso" in mapping:
        payload["time"] = normalize_optional_text(mapping.get("time") if "time" in mapping else mapping.get("time_iso"))
    if not partial or "time_note" in mapping:
        payload["time_note"] = normalize_optional_text(mapping.get("time_note"))
    if not partial or "location_note" in mapping:
        payload["location_note"] = normalize_optional_text(mapping.get("location_note"))
    if not partial or "remark" in mapping:
        payload["remark"] = normalize_optional_text(mapping.get("remark"))
    if not partial or "lat" in mapping:
        payload["lat"] = _coerce_float(mapping.get("lat"))
    if not partial or "lon" in mapping:
        payload["lon"] = _coerce_float(mapping.get("lon"))
    if not partial or "persons" in mapping:
        payload["persons"] = normalize_persons(mapping.get("persons"))
    if not partial or "priority" in mapping:
        priority = normalize_optional_text(mapping.get("priority"))
        payload["priority"] = validate_priority(priority) if priority else None
    if not partial or "event" in mapping:
        payload["event"] = mapping.get("event", "")
    return payload


def _decorate_row(row, timezone: str):
    """给数据库行补充展示字段。"""
    payload = _row_to_payload(row, timezone)
    payload["time_display"] = _row_time_text(payload)
    if payload.get("lat") is not None and payload.get("lon") is not None:
        location_text = f"{payload['lat']:.4f}, {payload['lon']:.4f}"
        if payload.get("location_note"):
            location_text = f"{location_text} · {payload['location_note']}"
        payload["location_display"] = location_text
    else:
        payload["location_display"] = payload["location_note"]
    payload["persons_display"] = payload["persons"]
    return payload


def _row_to_form(row):
    """将数据库行转成表单初始值。"""
    return {
        "event": row["event"],
        "time": _row_time_text(row),
        "time_note": row["time_note"],
        "lat": row["lat"],
        "lon": row["lon"],
        "location_note": row["location_note"],
        "persons": row["persons"],
        "priority": row["priority"],
        "remark": row["remark"],
    }


def _row_to_payload(row, timezone: str):
    """将数据库行转成 JSON 负载。"""
    return {
        "id": row["id"],
        "time": _row_time_text(row),
        "time_note": row["time_note"],
        "time_year": row["time_year"],
        "time_month": row["time_month"],
        "time_day": row["time_day"],
        "time_hour": row["time_hour"],
        "time_minute": row["time_minute"],
        "lat": row["lat"],
        "lon": row["lon"],
        "location_note": row["location_note"],
        "persons": row["persons"],
        "event": row["event"],
        "priority": row["priority"],
        "remark": row["remark"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "time_display": _row_time_text(row),
        "persons_display": row["persons"],
        "location_display": row["location_note"],
    }


def _row_time_text(row) -> str:
    """从记录或负载生成展示时间。"""
    value = structured_time_from_parts(
        year=row.get("time_year") if hasattr(row, "get") else row["time_year"],
        month=row.get("time_month") if hasattr(row, "get") else row["time_month"],
        day=row.get("time_day") if hasattr(row, "get") else row["time_day"],
        hour=row.get("time_hour") if hasattr(row, "get") else row["time_hour"],
        minute=row.get("time_minute") if hasattr(row, "get") else row["time_minute"],
    )
    return format_structured_time(value)


def _build_map_data(
    events: list[dict[str, Any]],
    basemap: str = "modern",
    *,
    image_url: Optional[str] = None,
    interactive: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """将事件坐标投影到内联 SVG 轨迹图。"""
    basemap_layer = BASEMAP_LAYERS.get(basemap, BASEMAP_LAYERS["modern"])
    points = sorted(
        [event for event in events if event.get("lat") is not None and event.get("lon") is not None],
        key=_map_event_sort_key,
    )
    width = 860
    height = 560
    padding = 54
    if not points:
        return {
            "width": width,
            "height": height,
            "points": [],
            "path_d": "",
            "bounds_label": "暂无坐标范围",
            "basemap": _project_basemap_layer(basemap_layer, lambda _lat, _lon: (0.0, 0.0), image_url=image_url),
            "interactive": interactive or {"enabled": False},
        }

    basemap_coords = _basemap_coordinate_pairs(basemap_layer)
    lats = [float(point["lat"]) for point in points] + [lat for lat, _lon in basemap_coords]
    lons = [float(point["lon"]) for point in points] + [lon for _lat, lon in basemap_coords]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    if min_lat == max_lat:
        min_lat -= 0.5
        max_lat += 0.5
    if min_lon == max_lon:
        min_lon -= 0.5
        max_lon += 0.5

    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    drawable_width = width - padding * 2
    drawable_height = height - padding * 2

    def project(lat: float, lon: float) -> tuple[float, float]:
        x = padding + (lon - min_lon) / lon_span * drawable_width
        y = padding + (max_lat - lat) / lat_span * drawable_height
        return round(x, 2), round(y, 2)

    projected = []
    cluster_counts: dict[tuple[int, int], int] = {}
    for index, point in enumerate(points):
        base_x, base_y = project(float(point["lat"]), float(point["lon"]))
        cluster_key = (round(float(point["lat"]), 2), round(float(point["lon"]), 2))
        cluster_index = cluster_counts.get(cluster_key, 0)
        cluster_counts[cluster_key] = cluster_index + 1
        if cluster_index:
            angle = (cluster_index - 1) * 1.9
            radius = 24 + min(cluster_index, 3) * 5
            x = round(base_x + radius * math.cos(angle), 2)
            y = round(base_y + radius * math.sin(angle), 2)
        else:
            x, y = base_x, base_y
        projected.append(
            {
                **point,
                "base_x": base_x,
                "base_y": base_y,
                "x": x,
                "y": y,
                "offset": cluster_index > 0,
                "label_x": round(min(x + 18, width - padding), 2),
                "label_y": round(max(y - 16, padding / 2), 2),
            }
        )

    path_d = " ".join(
        f"{'M' if index == 0 else 'L'} {point['x']} {point['y']}"
        for index, point in enumerate(projected)
    )
    bounds_label = f"{min_lat:.2f}°N-{max_lat:.2f}°N，{min_lon:.2f}°E-{max_lon:.2f}°E"
    return {
        "width": width,
        "height": height,
        "points": projected,
        "path_d": path_d,
        "bounds_label": bounds_label,
        "basemap": _project_basemap_layer(basemap_layer, project, image_url=image_url),
        "interactive": interactive or {"enabled": False},
    }


def _basemap_coordinate_pairs(layer: dict[str, Any]) -> list[tuple[float, float]]:
    """取出底图层所有经纬度坐标，用于计算投影范围。"""
    coords: list[tuple[float, float]] = [(float(lat), float(lon)) for lat, lon in layer.get("land", [])]
    for region in layer["regions"]:
        coords.extend((float(lat), float(lon)) for lat, lon in region["points"])
    for line in layer["lines"]:
        coords.extend((float(lat), float(lon)) for lat, lon in line["points"])
    for label in layer["labels"]:
        coords.append((float(label["lat"]), float(label["lon"])))
    return coords


def _project_basemap_layer(layer: dict[str, Any], project, *, image_url: Optional[str] = None) -> dict[str, Any]:
    """把底图图层投影到 SVG 坐标。"""
    land_points = [project(float(lat), float(lon)) for lat, lon in layer.get("land", [])]
    land_path_d = " ".join(
        f"{'M' if index == 0 else 'L'} {x} {y}"
        for index, (x, y) in enumerate(land_points)
    )

    regions = []
    for region in layer["regions"]:
        projected_points = [project(float(lat), float(lon)) for lat, lon in region["points"]]
        path_d = " ".join(
            f"{'M' if index == 0 else 'L'} {x} {y}"
            for index, (x, y) in enumerate(projected_points)
        )
        regions.append({"label": region["label"], "path_d": f"{path_d} Z"})

    lines = []
    for line in layer["lines"]:
        projected_points = [project(float(lat), float(lon)) for lat, lon in line["points"]]
        path_d = " ".join(
            f"{'M' if index == 0 else 'L'} {x} {y}"
            for index, (x, y) in enumerate(projected_points)
        )
        lines.append({"label": line["label"], "kind": line["kind"], "path_d": path_d})

    labels = []
    for label in layer["labels"]:
        x, y = project(float(label["lat"]), float(label["lon"]))
        labels.append({"text": label["text"], "major": label["major"], "x": x, "y": y})

    return {
        "title": layer["title"],
        "description": layer["description"],
        "source": layer["source"],
        "source_url": layer["source_url"],
        "asset_hint": layer["asset_hint"],
        "image_url": image_url,
        "land_path_d": f"{land_path_d} Z" if land_path_d else "",
        "regions": regions,
        "lines": lines,
        "labels": labels,
    }


def _map_event_sort_key(event: dict[str, Any]) -> tuple[tuple[int, int, int, int, int, int, int], int]:
    """地图同时间事件按创建顺序连接，保留导入时的叙事顺序。"""
    structured = structured_time_from_parts(
        year=event.get("time_year"),
        month=event.get("time_month"),
        day=event.get("time_day"),
        hour=event.get("time_hour"),
        minute=event.get("time_minute"),
        time_note=event.get("time_note"),
    )
    return build_sort_key(structured), int(event.get("id") or 0)
