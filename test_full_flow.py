from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, UserScore
import json

client = TestClient(app)

def test_mahesh_critical_flow():
    print("Testing 'Mahesh (Critical)' User Flow...")
    
    # 1. Trigger the scoring endpoint
    response = client.post("/score/mahesh_critical_123")
    assert response.status_code == 200
    
    data = response.json()
    print(f"\n[API Response]")
    print(json.dumps(data, indent=2))
    
    # 2. Assertions based on mocked data in main.py
    assert data["is_critical"] is True, "Mahesh should be flagged as critical."
    assert data["risk_score"] > 66, "Mahesh's risk score should be > 66."
    print("[OK] Scoring pipeline successfully predicted High Risk.")
    
    # 3. Check SQLite Persistence
    db = SessionLocal()
    saved_record = db.query(UserScore).filter(UserScore.user_id == "mahesh_critical_123").order_by(UserScore.id.desc()).first()
    db.close()
    
    assert saved_record is not None, "Record was not saved to SQLite."
    assert saved_record.score == data["risk_score"], "Saved score doesn't match API score."
    print("[OK] Results successfully persisted to SQLite.")
    
    print("\n[OK] Full Flow Test Passed!")

def test_safe_user_flow():
    print("\nTesting 'Safe' User Flow...")
    response = client.post("/score/safe_user_999")
    assert response.status_code == 200
    data = response.json()
    assert data["is_critical"] is False, "Safe user should not be critical."
    print(f"Safe User Score: {data['risk_score']}/100")
    print("[OK] Scoring pipeline correctly identified safe user.")
    print("[OK] Safe Flow Test Passed!")

if __name__ == "__main__":
    test_mahesh_critical_flow()
    test_safe_user_flow()
