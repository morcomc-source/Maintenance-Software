import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.notify import notify_due_digest, slack_ready
app = create_app()
with app.app_context():
    if not slack_ready():
        print("Slack not configured or disabled.")
        sys.exit(0)
    ok = notify_due_digest()
    print("Due digest sent." if ok else "Nothing due, or send failed.")
