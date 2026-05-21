from app import create_app

app = create_app()

if __name__ == "__main__":
    print("🚀 Starting Maintenance App...")
    print("📍 Local URL: http://127.0.0.1:5000")
    print("🌐 Network URL: http://0.0.0.0:5000")
    print("Press Ctrl + C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)