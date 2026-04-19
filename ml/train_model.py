import pandas as pd
import numpy as np
import pickle
from xgboost import XGBClassifier
from faker import Faker
import os

fake = Faker()

def generate_synthetic_data(num_samples=2000):
    np.random.seed(42)
    Faker.seed(42)
    
    data = []
    for _ in range(num_samples):
        circular_debt = np.random.choice([0, 1], p=[0.8, 0.2])
        emi_ratio = np.clip(np.random.normal(0.4, 0.2), 0.0, 1.0)
        app_count = int(np.clip(np.random.normal(3, 2), 0, 15))
        balance_trend = np.clip(np.random.normal(0, 1), -5.0, 5.0)
        nach_bounce = np.random.choice([0, 1], p=[0.85, 0.15])
        
        # Rule-based calculation for probability of debt spiral
        risk_score = (circular_debt * 3) + (emi_ratio * 4) + (app_count * 0.5) - balance_trend + (nach_bounce * 2)
        
        # Convert to 1/0 based on a threshold
        is_spiral = 1 if risk_score > 5.5 else 0
        
        # Add some noise to make the model learn rather than memorize a fixed rule
        if np.random.rand() < 0.1:
            is_spiral = 1 - is_spiral
            
        data.append({
            'user_id': fake.uuid4(),
            'circular_debt': circular_debt,
            'emi_ratio': emi_ratio,
            'app_count': app_count,
            'balance_trend': balance_trend,
            'nach_bounce': nach_bounce,
            'is_spiral': is_spiral
        })
        
    return pd.DataFrame(data)

if __name__ == "__main__":
    print("Generating synthetic data...")
    df = generate_synthetic_data()
    print(f"Generated {len(df)} samples.")
    print(f"Spiral cases: {df['is_spiral'].sum()}")
    
    X = df[['circular_debt', 'emi_ratio', 'app_count', 'balance_trend', 'nach_bounce']]
    y = df['is_spiral']
    
    # Train the XGBoost model
    print("Training XGBoost model...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X, y)
    
    # Ensure ml directory exists (it should, based on setup)
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"Model saved successfully to {model_path}.")
