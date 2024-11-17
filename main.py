from app import app
import os

if __name__ == "__main__":
    # Create database tables
    with app.app_context():
        from database import db
        db.create_all()
    
    # Run app on port 5000 consistently
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
