from database import SessionLocal
from sqlalchemy import text

try:
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    print("✅ DB CONNECTED SUCCESSFULLY")
except Exception as e:
    print("❌ DB CONNECTION FAILED:", e)
finally:
    db.close()