import json
from datetime import datetime
import re

LENDER_KEYWORDS = ['kreditbee', 'mpokket', 'navin', 'simpl', 'zest', 'lazypay', 'loan']
INCOME_KEYWORDS = ['salary', 'payroll', 'credit via neft']
REPAYMENT_KEYWORDS = ['repayment', 'emi', 'auto debit', 'nach', 'loan emi']

def _is_lender(narration: str) -> bool:
    narration_lower = narration.lower()
    return any(keyword in narration_lower for keyword in LENDER_KEYWORDS)

def _is_income(narration: str) -> bool:
    narration_lower = narration.lower()
    return any(keyword in narration_lower for keyword in INCOME_KEYWORDS)

def _is_repayment(narration: str) -> bool:
    narration_lower = narration.lower()
    return any(keyword in narration_lower for keyword in REPAYMENT_KEYWORDS)

def analyze_transactions(transactions: list) -> dict:
    # Handle parsing if transactions is a JSON string
    if isinstance(transactions, str):
        try:
            transactions = json.loads(transactions)
        except:
            transactions = []
            
    # Sort transactions by timestamp ascending
    try:
        transactions = sorted(transactions, key=lambda x: datetime.fromisoformat(x.get('timestamp', '1970-01-01T00:00:00')))
    except:
        pass
        
    total_income = 0.0
    total_repayment = 0.0
    unique_apps = set()
    
    lender_credits = []
    has_circular_debt = 0
    
    balance_trend_delta = 0.0 # simplified metric
    starting_balance = 0.0
    if len(transactions) > 0 and 'balance' in transactions[0]:
        starting_balance = transactions[0]['balance']
        ending_balance = transactions[-1].get('balance', starting_balance)
        balance_trend_delta = (ending_balance - starting_balance) / max(starting_balance, 1)

    nach_bounce = 0

    for idx, t in enumerate(transactions):
        narration = t.get('narration', '').lower()
        amount = float(t.get('amount', 0.0))
        t_type = t.get('type', 'debit').lower()
        timestamp_str = t.get('timestamp')
        
        if not timestamp_str:
            continue
            
        try:
            t_date = datetime.fromisoformat(timestamp_str)
        except:
            continue
            
        # Detect NACH Bounce
        if 'bounce' in narration or 'return' in narration or 'failed' in narration:
            nach_bounce = 1

        # Income Calculation
        if t_type == 'credit' and _is_income(narration):
            total_income += amount
            
        # Repayment
        if t_type == 'debit' and _is_repayment(narration):
            total_repayment += amount

        # Detect apps
        for keyword in LENDER_KEYWORDS:
            if keyword in narration:
                unique_apps.add(keyword)
                
        # Circular Debt detection (lender credit -> lender debit within 48h)
        if t_type == 'credit' and _is_lender(narration):
            lender_credits.append({'date': t_date, 'amount': amount})
            
        if t_type == 'debit' and _is_lender(narration):
            for lc in lender_credits:
                time_diff = (t_date - lc['date']).total_seconds() / 3600 # in hours
                if 0 <= time_diff <= 48:
                    has_circular_debt = 1
                    break

    emi_ratio = 0.0
    if total_income > 0:
        emi_ratio = min(total_repayment / total_income, 1.0)
    elif total_repayment > 0:
        emi_ratio = 1.0
        
    return {
        'circular_debt': has_circular_debt,
        'emi_ratio': emi_ratio,
        'app_count': len(unique_apps),
        'balance_trend': balance_trend_delta,
        'nach_bounce': nach_bounce
    }
