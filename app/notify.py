import json
import urllib.request
from datetime import date
from urllib.parse import urlencode

SITE_URL = "https://mymaintenancedesk.com"

def get_setting(key, default=""):
    from app.models.settings import AppSetting
    row = AppSetting.query.get(key)
    return row.value if row and row.value is not None else default

def set_setting(key, value):
    from app import db
    from app.models.settings import AppSetting
    row = AppSetting.query.get(key)
    if row is None:
        db.session.add(AppSetting(key=key, value=value))
    else:
        row.value = value
    db.session.commit()

def _username(user_id):
    if not user_id:
        return "Unassigned"
    from app.models.user import User
    user = User.query.get(user_id)
    return user.username if user else "Unknown"

def _get_user(user_id):
    if not user_id:
        return None
    from app.models.user import User
    return User.query.get(user_id)

def slack_ready():
    url = (get_setting("slack_webhook_url") or "").strip()
    enabled = get_setting("slack_enabled", "1") != "0"
    return bool(url) and enabled

def bot_ready():
    token = (get_setting("slack_bot_token") or "").strip()
    enabled = get_setting("slack_enabled", "1") != "0"
    return token.startswith("xoxb-") and enabled

def send_slack(text):
    try:
        if not slack_ready():
            return False
        url = get_setting("slack_webhook_url").strip()
        payload = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception as err:
        print("Slack notify error:", err)
        return False

def _slack_api(token, method, payload=None, params=None):
    url = f"https://slack.com/api/{method}"
    if params:
        url += "?" + urlencode(params)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": "Bearer " + token}
    if payload is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def send_dm_to_app_user(user_id, text):
    try:
        if not bot_ready():
            return False
        user = _get_user(user_id)
        if not user or not (user.email or "").strip():
            print("Slack DM skipped: user has no email")
            return False
        token = get_setting("slack_bot_token").strip()
        lookup = _slack_api(token, "users.lookupByEmail", params={"email": user.email.strip()})
        if not lookup.get("ok"):
            print("Slack lookupByEmail failed:", lookup.get("error"), user.email)
            return False
        slack_id = lookup["user"]["id"]
        opened = _slack_api(token, "conversations.open", payload={"users": slack_id})
        if not opened.get("ok"):
            print("Slack conversations.open failed:", opened.get("error"))
            return False
        posted = _slack_api(token, "chat.postMessage", payload={"channel": opened["channel"]["id"], "text": text})
        if not posted.get("ok"):
            print("Slack chat.postMessage failed:", posted.get("error"))
            return False
        return True
    except Exception as err:
        print("Slack DM error:", err)
        return False

def _notify_both(channel_text, assignee_id, dm_text=None):
    send_slack(channel_text)
    if assignee_id:
        send_dm_to_app_user(assignee_id, dm_text or channel_text)

def notify_workorder_created(wo):
    who = _username(wo.assigned_to_id)
    due = wo.expected_completion_date.isoformat() if wo.expected_completion_date else "None"
    pri = wo.priority if wo.priority is not None else "—"
    desc = (wo.description or "").strip().replace("\r\n", "\n")
    if len(desc) > 200:
        desc = desc[:197] + "..."
    extra = f" ({wo.equipment_id})" if wo.equipment_id else ""
    text = (
        f"*New work order* WO-{wo.id}\n"
        f"Equipment: {wo.equipment or '—'}{extra}\n"
        f"Assigned to: {who}\n"
        f"Priority: {pri}  |  Due: {due}\n"
        f"{desc}\n"
        f"<{SITE_URL}/workorder/details/{wo.id}|Open work order>"
    )
    _notify_both(text, wo.assigned_to_id)

def notify_workorder_assigned(wo):
    who = _username(wo.assigned_to_id)
    text = (
        f"*Work order assigned* WO-{wo.id}\n"
        f"Equipment: {wo.equipment or '—'}\n"
        f"Assigned to: {who}\n"
        f"<{SITE_URL}/workorder/details/{wo.id}|Open work order>"
    )
    _notify_both(text, wo.assigned_to_id)

def notify_workorder_completed(wo, by_name=""):
    text = (
        f"*Work order completed* WO-{wo.id}\n"
        f"Equipment: {wo.equipment or '—'}\n"
        f"Completed by: {by_name or _username(wo.completed_by_id)}\n"
        f"<{SITE_URL}/workorder/details/{wo.id}|Open work order>"
    )
    send_slack(text)
    if wo.assigned_to_id:
        send_dm_to_app_user(wo.assigned_to_id, text)

def notify_pm_saved(pm, created=False):
    who = _username(pm.assigned_user_id)
    due = pm.next_due.isoformat() if pm.next_due else "None"
    verb = "New PM" if created else "PM updated"
    sub = f" / {pm.sub_equipment}" if pm.sub_equipment else ""
    text = (
        f"*{verb}* PM-{pm.id}\n"
        f"Equipment: {pm.main_equipment or '—'}{sub}\n"
        f"Frequency: {pm.frequency or '—'}  |  Next due: {due}\n"
        f"Assigned to: {who}\n"
        f"<{SITE_URL}/pm/details/{pm.id}|Open PM>"
    )
    _notify_both(text, pm.assigned_user_id)

def notify_pm_completed(pm, by_name=""):
    due = pm.next_due.isoformat() if pm.next_due else "None"
    text = (
        f"*PM completed* PM-{pm.id}\n"
        f"Equipment: {pm.main_equipment or '—'}\n"
        f"Completed by: {by_name or _username(pm.completed_by_id)}\n"
        f"Next due: {due}\n"
        f"<{SITE_URL}/pm/details/{pm.id}|Open PM>"
    )
    send_slack(text)
    if pm.assigned_user_id:
        send_dm_to_app_user(pm.assigned_user_id, text)

def notify_due_digest():
    from app.models.pm import PM
    from app.models.workorder import WorkOrder
    today = date.today()
    lines = []
    pms = PM.query.filter(PM.next_due.isnot(None), PM.next_due <= today).order_by(PM.next_due).all()
    if pms:
        lines.append("*PMs due or overdue*")
        for pm in pms:
            flag = "OVERDUE" if pm.next_due < today else "DUE TODAY"
            lines.append(f"• PM-{pm.id} {pm.main_equipment or ''} — {flag} ({pm.next_due}) — {_username(pm.assigned_user_id)}")
    wos = WorkOrder.query.filter(
        WorkOrder.expected_completion_date.isnot(None),
        WorkOrder.expected_completion_date < today,
        WorkOrder.status != "Completed",
    ).order_by(WorkOrder.expected_completion_date).all()
    if wos:
        if lines:
            lines.append("")
        lines.append("*Work orders past due*")
        for wo in wos:
            lines.append(f"• WO-{wo.id} {wo.equipment or ''} — due {wo.expected_completion_date} — {_username(wo.assigned_to_id)}")
    if not lines:
        return False
    return send_slack("\n".join(lines))
