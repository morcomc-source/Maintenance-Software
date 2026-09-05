from flask import Flask, flash, redirect, url_for, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from flask_migrate import Migrate
db = SQLAlchemy() # Global db
login_manager = LoginManager() # Global login manager
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
  
    # Init extensions after app/config
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
  
    # Init Migrate inside create_app (after db/app ready)
    migrate = Migrate(app, db)
  
    # User loader (nested for late import)
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return User.query.get(int(user_id))
  
    # Unauthorized handler (after init)
    @login_manager.unauthorized_handler
    def unauthorized():
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
  
    # Import models (late, inside create_app to avoid circulars)
    from .models.user import User
    from .models.pm import PM
    from .models.part import Part
    from .models.part_transaction import PartTransaction
    from .models.equipment import Equipment
    from .models.settings import PartLocation, PartSublocation, AppSetting
  
# Register blueprints
    from .routes.pm import bp as pm_bp
    from .routes.parts import bp as parts_bp
    from .routes.auth import bp as auth_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.workorder import bp as workorder_bp
    from .routes.equipment import bp as equipment_bp
    from .routes.settings import bp as settings_bp
    from .routes.permits import bp as permits_bp

    app.register_blueprint(pm_bp, url_prefix='/pm')
    app.register_blueprint(parts_bp, url_prefix='/parts')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(workorder_bp, url_prefix='/workorder')
    app.register_blueprint(equipment_bp, url_prefix='/equipment')
    app.register_blueprint(settings_bp)
    app.register_blueprint(permits_bp)

    @app.route('/serviceworker.js')
    def service_worker():
        response = make_response(send_from_directory(app.static_folder, 'serviceworker.js'))
        response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        response.headers['Service-Worker-Allowed'] = '/'
        response.headers['Cache-Control'] = 'no-cache'
        return response
    
    
    # Local time display (Central)
    @app.template_filter("localtime")
    def localtime_filter(value, fmt="%Y-%m-%d %I:%M %p"):
        if value is None:
            return "—"
        try:
            from zoneinfo import ZoneInfo
            from datetime import timezone
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            local = value.astimezone(ZoneInfo("America/Chicago"))
            return local.strftime(fmt)
        except Exception:
            return value.strftime(fmt) if hasattr(value, "strftime") else str(value)

    return app