import os
import shutil

# Define old and new names
old_name = 'pm'
new_name = 'preventative_maintenance'

# App root directory
app_root = os.path.dirname(os.path.abspath(__file__))

# Files to update (relative paths from app_root)
files_to_update = [
    'app/__init__.py',
    'app/routes/preventative_maintenance.py',  # After manual rename
    'templates/preventative_maintenance.html',  # After manual rename
    'templates/base.html',
    'templates/dashboard/admin.html',
    'templates/dashboard/technician.html',
    'app/models/preventative_maintenance.py',  # After manual rename
    # Add any other files with 'pm' references, e.g., 'run.py' if applicable
]

# Strings to replace (key: old, value: new)
replacements = {
    "from .routes.pm import bp as pm_bp": f"from .routes.{new_name} import bp as pm_bp",
    "app.register_blueprint(pm_bp, url_prefix='/pm')": f"app.register_blueprint(pm_bp, url_prefix='/{new_name}')",  # Or keep '/pm'
    "from .models.pm import PM": f"from .models.{new_name} import PM",
    "url_for('pm.index')": f"url_for('{new_name}.index')",
    "url_for('pm.manage_users')": f"url_for('{new_name}.manage_users')",
    "render_template('pm.html'": f"render_template('{new_name}.html'",
    # Add more specific strings if needed, e.g., for JS URLs or other links
}

def replace_in_file(file_path):
    # Backup the file
    backup_path = file_path + '.bak'
    shutil.copyfile(file_path, backup_path)
    print(f"Backed up {file_path} to {backup_path}")
    
    # Read and replace (use utf-8 encoding to handle special characters)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {file_path}")

# Run the replacements
for file in files_to_update:
    full_path = os.path.join(app_root, file)
    if os.path.exists(full_path):
        replace_in_file(full_path)
    else:
        print(f"File not found: {full_path} - skip")

print("Renaming complete. Run 'flask db migrate' if model changes, then test your app.")