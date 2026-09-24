import requests
import json

url = "http://127.0.0.1:5000/predict"
payload = {
    "gender": 1,
    "married": 1,
    "income": 500000,
    "loan_amount": 100000,
    "credit_history": 1,
    "loan_type": "Personal",
    "tenure_months": 60,
    "aadhar": "123412341234",
    "pan": "ABCDE1234F",
    "bank_account": "123456789",
    "ifsc": "HDFC0123456",
    "existing_loan": 0,
    "existing_emi": 0
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
