from collections import namedtuple
from datetime import date, datetime
from calendar import monthrange
from zoneinfo import ZoneInfo

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_

from app import db
from app.models.water_reading import WaterReading

bp = Blueprint("water", __name__, url_prefix="/water")

Loc = namedtuple("Loc", "code name has_meter has_tds")
LOCATIONS = [
    Loc("p1", "Press 1", True, True),
    Loc("p5", "Press 5", True, True),
    Loc("ch", "Cast House", True, True),
    Loc("city", "City Water", False, True),
    Loc("anodize", "Anodize R/O", True, True),
    Loc("waste", "Waste Water", True, False),
]
MEETING_ORDER = ["p1", "p5", "ch", "city", "anodize"]
DAILY_ORDER = ["p1", "p5", "ch", "city", "anodize"]
MONTHLY_METER_ORDER = ["p1", "p5", "ch", "anodize"]


def chicago_today():
    return datetime.now(ZoneInfo("America/Chicago")).date()


def loc_by_code(code):
    for loc in LOCATIONS:
        if loc.code == code:
            return loc
    return None


def parse_int(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace(" ", "")
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def fmt_int(n):
    if n is None:
        return ""
    return f"{int(n):,}"


def previous_meter(location, reading_date):
    row = (
        WaterReading.query.filter(
            WaterReading.location == location,
            WaterReading.reading_date < reading_date,
            WaterReading.meter.isnot(None),
        )
        .order_by(WaterReading.reading_date.desc())
        .first()
    )
    return row.meter if row else None


def last_meter_on_or_before(location, on_date):
    row = (
        WaterReading.query.filter(
            WaterReading.location == location,
            WaterReading.reading_date <= on_date,
            WaterReading.meter.isnot(None),
        )
        .order_by(WaterReading.reading_date.desc())
        .first()
    )
    return row


def last_meter_in_month(location, year, month):
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return (
        WaterReading.query.filter(
            WaterReading.location == location,
            WaterReading.reading_date >= start,
            WaterReading.reading_date <= end,
            WaterReading.meter.isnot(None),
        )
        .order_by(WaterReading.reading_date.desc())
        .first()
    )


def upsert_reading(reading_date, location, meter=None, tds=None, created_by_id=None, is_baseline=False):
    rec = WaterReading.query.filter_by(reading_date=reading_date, location=location).first()
    if rec is None:
        rec = WaterReading(reading_date=reading_date, location=location, created_by_id=created_by_id)
        db.session.add(rec)
    if meter is not None:
        rec.meter = meter
    if tds is not None:
        rec.tds = tds
    if is_baseline:
        rec.is_baseline = True
        rec.usage = None
    elif rec.meter is not None:
        prev = previous_meter(location, reading_date)
        rec.usage = (rec.meter - prev) if prev is not None else None
        rec.is_baseline = False if prev is not None else True
    return rec


def meeting_parts(reading_date):
    rows = {r.location: r for r in WaterReading.query.filter_by(reading_date=reading_date).all()}
    parts = [reading_date.strftime("%-m/%-d/%Y")]
    for code in MEETING_ORDER:
        rec = rows.get(code)
        tds = rec.tds if rec else None
        usage = rec.usage if rec else None
        tds_s = str(tds) if tds is not None else "-"
        if usage is None:
            use_s = "0"
        else:
            use_s = f"{int(usage):,}"
        parts.append(f"{tds_s}/{use_s}")
    return parts


def monthly_usage(location, year, month):
    this = last_meter_in_month(location, year, month)
    if month == 1:
        py, pm = year - 1, 12
    else:
        py, pm = year, month - 1
    prev = last_meter_in_month(location, py, pm)
    if this is None or prev is None:
        return None, this, prev
    return this.meter - prev.meter, this, prev


def is_water_test_pm(pm):
    text = f"{getattr(pm, 'main_equipment', '') or ''} {getattr(pm, 'sub_equipment', '') or ''}".lower()
    return "water" in text


def save_water_from_payload(payload, user_id, reading_date=None):
    if reading_date is None:
        reading_date = chicago_today()
    payload = payload or {}
    saved = []
    for loc in LOCATIONS:
        if loc.code == "waste":
            continue
        meter = parse_int(payload.get(f"{loc.code}_meter")) if loc.has_meter else None
        tds = parse_int(payload.get(f"{loc.code}_tds")) if loc.has_tds else None
        if meter is None and tds is None:
            continue
        upsert_reading(reading_date, loc.code, meter=meter, tds=tds, created_by_id=user_id)
        saved.append(loc.code)
    print("water saved from PM:", saved, "date", reading_date)
    return saved


def staff_only():
    return current_user.role in ("admin", "supervisor", "technician")


@bp.route("/")
@login_required
def index():
    if not staff_only():
        flash("Water Tests is only for maintenance staff.", "danger")
        return redirect(url_for("dashboard.index"))
    day = chicago_today()
    raw = request.args.get("date") or ""
    try:
        if raw:
            day = date.fromisoformat(raw)
    except ValueError:
        pass
    rows = {r.location: r for r in WaterReading.query.filter_by(reading_date=day).all()}
    line_parts = meeting_parts(day)
    line = " | ".join(line_parts)
    return render_template(
        "water/index.html",
        day=day,
        rows=rows,
        locations=[loc_by_code(c) for c in MEETING_ORDER],
        line=line,
        line_parts=line_parts,
        fmt_int=fmt_int,
    )


@bp.route("/daily", methods=["GET", "POST"])
@login_required
def daily():
    if not staff_only():
        flash("Water Tests is only for maintenance staff.", "danger")
        return redirect(url_for("dashboard.index"))
    day = chicago_today()
    raw = request.values.get("reading_date") or request.args.get("date") or ""
    try:
        if raw:
            day = date.fromisoformat(raw)
    except ValueError:
        flash("Date must be YYYY-MM-DD.", "danger")
        day = chicago_today()

    if request.method == "POST":
        saved = 0
        for loc in LOCATIONS:
            if loc.code == "waste":
                continue
            meter = parse_int(request.form.get(f"{loc.code}_meter")) if loc.has_meter else None
            tds = parse_int(request.form.get(f"{loc.code}_tds")) if loc.has_tds else None
            if meter is None and tds is None:
                continue
            upsert_reading(day, loc.code, meter=meter, tds=tds, created_by_id=current_user.id)
            saved += 1
        db.session.commit()
        if saved:
            flash(f"Saved {saved} reading(s) for {day.isoformat()}.", "success")
        else:
            flash("Nothing to save. Enter at least one number.", "warning")
        return redirect(url_for("water.daily", date=day.isoformat()))

    existing = {r.location: r for r in WaterReading.query.filter_by(reading_date=day).all()}
    locs = [loc_by_code(c) for c in DAILY_ORDER]
    return render_template("water/daily.html", day=day, locations=locs, existing=existing, fmt_int=fmt_int)


@bp.route("/seed", methods=["GET", "POST"])
@login_required
def seed():
    if current_user.role != "admin":
        flash("Only admin can seed opening meters.", "danger")
        return redirect(url_for("water.index"))
    day = chicago_today()
    raw = request.values.get("reading_date") or ""
    try:
        if raw:
            day = date.fromisoformat(raw)
    except ValueError:
        flash("Date must be YYYY-MM-DD.", "danger")
        day = chicago_today()

    if request.method == "POST":
        saved = 0
        for loc in LOCATIONS:
            if not loc.has_meter:
                continue
            meter = parse_int(request.form.get(f"{loc.code}_meter"))
            tds = parse_int(request.form.get(f"{loc.code}_tds")) if loc.has_tds else None
            if meter is None:
                continue
            upsert_reading(day, loc.code, meter=meter, tds=tds, created_by_id=current_user.id, is_baseline=True)
            saved += 1
        db.session.commit()
        flash(f"Seeded {saved} opening meter(s) on {day.isoformat()}.", "success")
        return redirect(url_for("water.seed"))

    existing = {r.location: r for r in WaterReading.query.filter_by(reading_date=day).all()}
    meter_locs = [loc for loc in LOCATIONS if loc.has_meter]
    return render_template("water/seed.html", day=day, locations=meter_locs, existing=existing, fmt_int=fmt_int)


@bp.route("/waste", methods=["GET", "POST"])
@login_required
def waste():
    if not staff_only():
        flash("Water Tests is only for maintenance staff.", "danger")
        return redirect(url_for("dashboard.index"))
    day = chicago_today()
    raw = request.values.get("reading_date") or request.args.get("date") or ""
    try:
        if raw:
            day = date.fromisoformat(raw)
    except ValueError:
        flash("Date must be YYYY-MM-DD.", "danger")
        day = chicago_today()

    if request.method == "POST":
        meter = parse_int(request.form.get("waste_meter"))
        if meter is None:
            flash("Enter a waste water meter number.", "danger")
        else:
            upsert_reading(day, "waste", meter=meter, created_by_id=current_user.id)
            db.session.commit()
            flash(f"Saved waste water meter for {day.isoformat()}.", "success")
        return redirect(url_for("water.waste", date=day.isoformat()))

    rec = WaterReading.query.filter_by(reading_date=day, location="waste").first()
    return render_template("water/waste.html", day=day, rec=rec, fmt_int=fmt_int)


@bp.route("/monthly")
@login_required
def monthly():
    if not staff_only():
        flash("Water Tests is only for maintenance staff.", "danger")
        return redirect(url_for("dashboard.index"))
    today = chicago_today()
    year = today.year
    month = today.month
    try:
        if request.args.get("year"):
            year = int(request.args.get("year"))
        if request.args.get("month"):
            month = int(request.args.get("month"))
    except ValueError:
        pass
    year = max(2020, min(year, 2100))
    month = max(1, min(month, 12))

    rows = []
    for code in MONTHLY_METER_ORDER:
        loc = loc_by_code(code)
        usage, this, prev = monthly_usage(code, year, month)
        rows.append({
            "loc": loc,
            "usage": usage,
            "this": this,
            "prev": prev,
        })
    waste_usage, waste_this, waste_prev = monthly_usage("waste", year, month)
    return render_template(
        "water/monthly.html",
        year=year,
        month=month,
        rows=rows,
        waste_usage=waste_usage,
        waste_this=waste_this,
        waste_prev=waste_prev,
        fmt_int=fmt_int,
    )


def map_checklist_item_to_water(item):
    text = f"{item.get('text') or item.get('label') or item.get('title') or ''}".lower()
    if item.get("type") == "title":
        return None
    if "waste" in text:
        return None
    code = None
    if "city" in text:
        code = "city"
    elif "anodize" in text:
        code = "anodize"
    elif "cast" in text:
        code = "ch"
    elif "4-5" in text or "press 5" in text or "press 4" in text:
        code = "p5"
    elif "1-2-3" in text or "press 1" in text or "press 2" in text or "press 3" in text:
        code = "p1"
    if not code:
        return None
    kind = "tds" if "tds" in text else "meter"
    raw = item.get("value")
    if raw in (None, ""):
        return None
    val = parse_int(raw)
    if val is None:
        return None
    return code, kind, val


def save_water_from_checklist(checklist, user_id, reading_date=None):
    if reading_date is None:
        reading_date = chicago_today()
    grouped = {}
    for item in checklist or []:
        mapped = map_checklist_item_to_water(item)
        if not mapped:
            continue
        code, kind, val = mapped
        grouped.setdefault(code, {})[kind] = val
    saved = []
    for code, vals in grouped.items():
        upsert_reading(
            reading_date,
            code,
            meter=vals.get("meter"),
            tds=vals.get("tds"),
            created_by_id=user_id,
        )
        saved.append(code)
    print("water saved from checklist:", saved, "date", reading_date)
    return saved
