"""Flask Web UI。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from flask import Blueprint, Flask, jsonify, redirect, render_template, request, url_for
from jinja2 import DictLoader

from ..constants import DEFAULT_DB_PATH, DEFAULT_TIMEZONE, PRIORITY_CHOICES, PRIORITY_LABELS
from ..errors import InputValidationError, NotFoundError
from ..store import EventStore
from ..time_utils import format_date_for_display
from ..validators import normalize_optional_text, normalize_persons, validate_priority

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

    @media (max-width: 860px) {
      .hero { grid-template-columns: 1fr; }
      .shell { width: min(100vw - 20px, 1180px); padding-top: 16px; }
      .hero-card, .sidebar, .card, .toolbar { padding: 16px; }
      .detail-grid.five-col { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
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
        <span>{{ event.time_display or '未填写时间' }}</span>
        <span>{{ event.location_display or '未填写地点' }}</span>
        <span class="badge{% if event.priority and event.priority != '史实' %} warning{% endif %}">{{ event.priority or '未设置优先级' }}</span>
      </div>
      <h3><a href="{{ url_for('web.event_detail', event_id=event.id) }}">{{ event.event }}</a></h3>
      <p class="muted">{{ event.persons_display or '未填写人物' }}</p>
      {% if event.time_note or event.location_note or event.remark %}
      <p class="muted">{{ event.time_note or event.location_note or event.remark }}</p>
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
    <label>事件描述
      <textarea name="event" required>{{ form.event or '' }}</textarea>
    </label>
    <div class="detail-grid">
      <label>时间
        <input name="time_iso" value="{{ form.time_iso or '' }}" placeholder="2024-01-15">
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
      <label>备注 / 来源
        <input name="remark" value="{{ form.remark or '' }}" placeholder="出处、链接或补充说明">
      </label>
    </div>
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
        TIMEZONE=DEFAULT_TIMEZONE,
    )
    if test_config:
        app.config.update(test_config)

    app.jinja_loader = DictLoader(
        {
            "base.html": BASE_TEMPLATE,
            "events/list.html": LIST_TEMPLATE,
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
    return {
        "q": normalize_optional_text(args.get("q")),
        "person": normalize_optional_text(args.get("person")),
        "location": normalize_optional_text(args.get("location")),
        "priority": priority,
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
    if not partial or "time_iso" in mapping:
        payload["time_iso"] = normalize_optional_text(mapping.get("time_iso"))
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
    payload["time_display"] = format_date_for_display(payload["time_iso"], tz=timezone) if payload.get("time_iso") else ""
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
        "time_iso": row["time_iso"],
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
        "time_iso": row["time_iso"],
        "time_note": row["time_note"],
        "lat": row["lat"],
        "lon": row["lon"],
        "location_note": row["location_note"],
        "persons": row["persons"],
        "event": row["event"],
        "priority": row["priority"],
        "remark": row["remark"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "time_display": format_date_for_display(row["time_iso"], tz=timezone) if row["time_iso"] else "",
        "persons_display": row["persons"],
        "location_display": row["location_note"],
    }
