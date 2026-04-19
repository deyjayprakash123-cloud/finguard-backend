from database import SessionLocal, UserScore
import json
import datetime

def preload_users():
    db = SessionLocal()
    
    # 1. User 1: Ramesh (Low risk)
    # Stable balance, 1 loan
    ramesh = UserScore(
        user_id="ramesh_stable_123",
        score=25,
        signals_triggered=json.dumps([]),
        timestamp=datetime.datetime.utcnow()
    )
    
    # 2. User 2: Mahesh (High risk)
    # 5 loans, 70% EMI ratio, circular debt
    mahesh = UserScore(
        user_id="mahesh_critical_123",
        score=98,
        signals_triggered=json.dumps([
            "Circular Debt Detected",
            "High EMI Ratio (70%)",
            "Multiple Loan Apps (5)",
            "NACH Bounce Detected"
        ]),
        timestamp=datetime.datetime.utcnow()
    )
    
    # 3. User 3: Suresh (Medium risk)
    # 2 loans, 40% EMI ratio
    suresh = UserScore(
        user_id="suresh_moderate_123",
        score=55,
        signals_triggered=json.dumps([
            "High EMI Ratio (40%)",
            "Multiple Loan Apps (2)"
        ]),
        timestamp=datetime.datetime.utcnow()
    )

    db.add(ramesh)
    db.add(mahesh)
    db.add(suresh)
    db.commit()
    print("Pre-loaded 3 demo users successfully into SQLite!")

if __name__ == "__main__":
    preload_users()
