import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

def create_model():
    np.random.seed(42)
    n_samples = 2000
    
    # 1: Male, 0: Female
    gender = np.random.choice([0, 1], size=n_samples, p=[0.3, 0.7])
    # 1: Married, 0: Single
    married = np.random.choice([0, 1], size=n_samples, p=[0.4, 0.6])
    # Income: 20k to 200k
    income = np.random.randint(20000, 200000, size=n_samples)
    # Loan Amount: 50k to 5M
    loan_amount = np.random.randint(50000, 5000000, size=n_samples)
    # Credit History: 0 to 1
    credit_history = np.random.choice([0, 1], size=n_samples, p=[0.2, 0.8])
    
    # Target Logic
    # Higher chance if: credit_history = 1, income > 50k, loan_amount is reasonable compared to income
    loan_status = []
    for g, m, inc, amt, ch in zip(gender, married, income, loan_amount, credit_history):
        score = 0
        if ch == 1:
            score += 5
        else:
            score -= 5
            
        if inc > 50000:
            score += 2
        if inc > 100000:
            score += 2
            
        if amt / inc < 20: # If asking for less than 20 months of income
            score += 3
        else:
            score -= 2
            
        if score >= 6:
            loan_status.append(1)
        else:
            loan_status.append(0)
            
    df = pd.DataFrame({
        'Gender': gender,
        'Married': married,
        'Income': income,
        'LoanAmount': loan_amount,
        'CreditHistory': credit_history,
        'LoanStatus': loan_status
    })
    
    X = df[['Gender', 'Married', 'Income', 'LoanAmount', 'CreditHistory']]
    y = df['LoanStatus']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    print(f"Model Accuracy on Synthetic Data: {accuracy_score(y_test, preds) * 100:.2f}%")
    
    joblib.dump(model, 'loan_model.pkl')
    print("Model saved to loan_model.pkl")

if __name__ == '__main__':
    create_model()
