from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import pickle
import pandas as pd
import os
import json
from datetime import datetime, timedelta

from database import SessionLocal, UserScore
from services.parser import analyze_transactions
from services.alerts import send_finguard_alert

app = FastAPI(title="FinGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load model
model_path = os.path.join("ml", "model.pkl")
with open(model_path, 'rb') as f:
    xgb_model = pickle.load(f)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock transaction generator
def get_mock_transactions(user_id: str):
    now = datetime.utcnow()
    # Simple mock: if user_id == 'mahesh_critical', or 'jay', or '1', give high risk markers
    if 'mahesh' in user_id.lower() or 'jay' in user_id.lower() or user_id == '1':
        return [
            {"type": "credit", "amount": 50000, "narration": "salary transfer", "timestamp": (now - timedelta(days=10)).isoformat()},
            {"type": "debit", "amount": 15000, "narration": "kreditbee emi", "timestamp": (now - timedelta(days=9)).isoformat()},
            {"type": "debit", "amount": 25000, "narration": "mpokket loan emi", "timestamp": (now - timedelta(days=8)).isoformat()},
            {"type": "credit", "amount": 5000, "narration": "lazypay loan credited", "timestamp": (now - timedelta(days=2)).isoformat()},
            {"type": "debit", "amount": 5000, "narration": "simpl repayment", "timestamp": (now - timedelta(days=2, hours=12)).isoformat()},
            {"type": "debit", "amount": 10000, "narration": "nach return fee due to bounce", "timestamp": (now - timedelta(days=1)).isoformat()}
        ]
    # Default safe user
    return [
        {"type": "credit", "amount": 80000, "narration": "salary transfer", "timestamp": (now - timedelta(days=5)).isoformat()},
        {"type": "debit", "amount": 4000, "narration": "zest emi", "timestamp": (now - timedelta(days=2)).isoformat()}
    ]

@app.post("/score/{user_id}")
async def score_user(user_id: str, db: Session = Depends(get_db)):
    # 1. Fetch mock transactions
    transactions = get_mock_transactions(user_id)
    
    # 2. Extract Signals
    signals = analyze_transactions(transactions)
    
    # 3. XGBoost Prediction
    # Create DataFrame matching training columns: 'circular_debt', 'emi_ratio', 'app_count', 'balance_trend', 'nach_bounce'
    df_features = pd.DataFrame([{
        'circular_debt': signals['circular_debt'],
        'emi_ratio': signals['emi_ratio'],
        'app_count': signals['app_count'],
        'balance_trend': signals['balance_trend'],
        'nach_bounce': signals['nach_bounce']
    }])
    
    # predict_proba returns array of [prob_safe, prob_spiral]
    prob_spiral = xgb_model.predict_proba(df_features)[0][1]
    
    # Convert to 0-100 risk score
    risk_score = int(prob_spiral * 100)
    
    # List of triggered human-readable signals
    triggered_signals = []
    if signals['circular_debt']: triggered_signals.append("Circular Debt Detected")
    if signals['emi_ratio'] > 0.5: triggered_signals.append(f"High EMI Ratio ({signals['emi_ratio']*100:.0f}%)")
    if signals['app_count'] > 2: triggered_signals.append(f"Multiple Loan Apps ({signals['app_count']})")
    if signals['nach_bounce']: triggered_signals.append("NACH Bounce Detected")
    
    # 4. Trigger Alert if > 66
    if risk_score > 66:
        user_name = "Mahesh" if "mahesh" in user_id.lower() else user_id
        send_finguard_alert(user_name, risk_score, triggered_signals[:3])
        print(f"Telegram Alert triggered for score: {risk_score}")
        
    # 5. Save to database
    db_score = UserScore(
        user_id=user_id,
        score=risk_score,
        signals_triggered=json.dumps(triggered_signals)
    )
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    
    return {
        "user_id": user_id,
        "risk_score": risk_score,
        "is_critical": risk_score > 66,
        "signals": signals,
        "triggered_alerts": triggered_signals
    }
