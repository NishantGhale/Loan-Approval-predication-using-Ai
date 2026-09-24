from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import os
import sqlite3
import re
import traceback
import pandas as pd
import os
try:
    import google.generativeai as genai
except ImportError:
    genai = None

app = Flask(__name__)
app.secret_key = 'super_secret_ai_loan_key' # Required for session management

# Load Model if exists, else it needs to be trained
if os.path.exists('loan_model.pkl'):
    model = joblib.load('loan_model.pkl')
else:
    model = None
    print("Warning: Model not found. Please run model.py first.")

# Configure Gemini AI for Chatbot
# Set your API Key here or in your environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") 

if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    chat_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    chat_model = None
    print("Warning: Gemini API Key not found or google-generativeai not installed. Chatbot will use rule-based fallback.")

# Bank Database with Multiple Options
# Bank Database with Multiple Options (Expanded for 5-7+ recommendations)
banks_data = [
    # Personal Loans
    {"Bank": "SBI", "LoanType": "Personal", "Interest": 11.0, "MaxAmount": 2000000, "Fee": "1.5%", "URL": "https://sbi.co.in/"},
    {"Bank": "HDFC", "LoanType": "Personal", "Interest": 10.5, "MaxAmount": 4000000, "Fee": "1%", "URL": "https://www.hdfcbank.com/"},
    {"Bank": "ICICI", "LoanType": "Personal", "Interest": 10.75, "MaxAmount": 5000000, "Fee": "2%", "URL": "https://www.icicibank.com/"},
    {"Bank": "Axis", "LoanType": "Personal", "Interest": 10.49, "MaxAmount": 4000000, "Fee": "1.5%", "URL": "https://www.axisbank.com/"},
    {"Bank": "Kotak Mahindra", "LoanType": "Personal", "Interest": 10.99, "MaxAmount": 2500000, "Fee": "2%", "URL": "https://www.kotak.com/"},
    {"Bank": "Bank of Baroda", "LoanType": "Personal", "Interest": 11.2, "MaxAmount": 2000000, "Fee": "1%", "URL": "https://www.bankofbaroda.in/"},
    {"Bank": "PNB", "LoanType": "Personal", "Interest": 11.4, "MaxAmount": 1500000, "Fee": "1%", "URL": "https://www.pnbindia.in/"},
    {"Bank": "Canara Bank", "LoanType": "Personal", "Interest": 11.5, "MaxAmount": 1000000, "Fee": "0.5%", "URL": "https://canarabank.com/"},
    {"Bank": "Union Bank", "LoanType": "Personal", "Interest": 11.6, "MaxAmount": 1500000, "Fee": "0.5%", "URL": "https://www.unionbankofindia.co.in/"},
    {"Bank": "IDFC First", "LoanType": "Personal", "Interest": 10.49, "MaxAmount": 10000000, "Fee": "2%", "URL": "https://www.idfcfirstbank.com/"},
    {"Bank": "IndusInd Bank", "LoanType": "Personal", "Interest": 10.25, "MaxAmount": 5000000, "Fee": "1%", "URL": "https://www.indusind.com/"},
    {"Bank": "Federal Bank", "LoanType": "Personal", "Interest": 11.5, "MaxAmount": 2500000, "Fee": "1%", "URL": "https://www.federalbank.co.in/"},
    {"Bank": "Yes Bank", "LoanType": "Personal", "Interest": 10.99, "MaxAmount": 4000000, "Fee": "1.5%", "URL": "https://www.yesbank.in/"},
    {"Bank": "RBL Bank", "LoanType": "Personal", "Interest": 14.0, "MaxAmount": 2000000, "Fee": "2%", "URL": "https://www.rblbank.com/"},
    {"Bank": "Standard Chartered", "LoanType": "Personal", "Interest": 11.5, "MaxAmount": 5000000, "Fee": "1%", "URL": "https://www.sc.com/in/"},

    # Home Loans
    {"Bank": "SBI Home Loans", "LoanType": "Home", "Interest": 8.4, "MaxAmount": 100000000, "Fee": "0%", "URL": "https://sbi.co.in/"},
    {"Bank": "HDFC Home Loans", "LoanType": "Home", "Interest": 8.5, "MaxAmount": 100000000, "Fee": "0.5%", "URL": "https://www.hdfcbank.com/"},
    {"Bank": "ICICI Home Finance", "LoanType": "Home", "Interest": 8.75, "MaxAmount": 50000000, "Fee": "0.5%", "URL": "https://www.icicibank.com/"},
    {"Bank": "LIC Housing Finance", "LoanType": "Home", "Interest": 8.5, "MaxAmount": 150000000, "Fee": "0.25%", "URL": "https://www.lichousing.com/"},
    {"Bank": "Axis Bank", "LoanType": "Home", "Interest": 8.75, "MaxAmount": 50000000, "Fee": "0.5%", "URL": "https://www.axisbank.com/"},
    {"Bank": "Bank of Baroda", "LoanType": "Home", "Interest": 8.4, "MaxAmount": 100000000, "Fee": "0%", "URL": "https://www.bankofbaroda.in/"},
    {"Bank": "Canara Bank", "LoanType": "Home", "Interest": 8.6, "MaxAmount": 75000000, "Fee": "0.25%", "URL": "https://canarabank.com/"},
    {"Bank": "Union Bank", "LoanType": "Home", "Interest": 8.7, "MaxAmount": 50000000, "Fee": "0%", "URL": "https://www.unionbankofindia.co.in/"},
    {"Bank": "PNB Housing", "LoanType": "Home", "Interest": 8.75, "MaxAmount": 30000000, "Fee": "0.5%", "URL": "https://www.pnbhousing.com/"},
    {"Bank": "Tata Capital", "LoanType": "Home", "Interest": 8.95, "MaxAmount": 50000000, "Fee": "0.5%", "URL": "https://www.tatacapital.com/"},
    {"Bank": "L&T Finance", "LoanType": "Home", "Interest": 8.6, "MaxAmount": 50000000, "Fee": "0%", "URL": "https://www.ltfs.com/"},
    {"Bank": "Bajaj Housing Finance", "LoanType": "Home", "Interest": 8.5, "MaxAmount": 50000000, "Fee": "0%", "URL": "https://www.bajajhousingfinance.in/"},

    # Vehicle Loans
    {"Bank": "SBI Car Loan", "LoanType": "Vehicle", "Interest": 8.2, "MaxAmount": 5000000, "Fee": "0%", "URL": "https://sbi.co.in/"},
    {"Bank": "HDFC Vehicle Loan", "LoanType": "Vehicle", "Interest": 8.8, "MaxAmount": 5000000, "Fee": "1%", "URL": "https://www.hdfcbank.com/"},
    {"Bank": "ICICI Bank", "LoanType": "Vehicle", "Interest": 9.0, "MaxAmount": 3000000, "Fee": "1.5%", "URL": "https://www.icicibank.com/"},
    {"Bank": "Axis Bank", "LoanType": "Vehicle", "Interest": 8.7, "MaxAmount": 2500000, "Fee": "1%", "URL": "https://www.axisbank.com/"},
    {"Bank": "Bank of Baroda", "LoanType": "Vehicle", "Interest": 8.5, "MaxAmount": 2000000, "Fee": "0%", "URL": "https://www.bankofbaroda.in/"},
    {"Bank": "Canara Bank", "LoanType": "Vehicle", "Interest": 8.9, "MaxAmount": 1500000, "Fee": "0.5%", "URL": "https://canarabank.com/"},
    {"Bank": "Punjab National Bank", "LoanType": "Vehicle", "Interest": 8.75, "MaxAmount": 2500000, "Fee": "0.5%", "URL": "https://www.pnbindia.in/"},
    
    # Education Loans
    {"Bank": "SBI (Vidya Lakshmi)", "LoanType": "Education", "Interest": 7.5, "MaxAmount": 15000000, "Fee": "0%", "URL": "https://sbi.co.in/"},
    {"Bank": "HDFC Credila", "LoanType": "Education", "Interest": 9.5, "MaxAmount": 10000000, "Fee": "1%", "URL": "https://www.hdfccredila.com/"},
    {"Bank": "ICICI Bank", "LoanType": "Education", "Interest": 9.25, "MaxAmount": 10000000, "Fee": "1%", "URL": "https://www.icicibank.com/"},
    {"Bank": "PNB Education", "LoanType": "Education", "Interest": 8.4, "MaxAmount": 7500000, "Fee": "0%", "URL": "https://www.pnbindia.in/"},
    {"Bank": "Canara Bank", "LoanType": "Education", "Interest": 9.2, "MaxAmount": 4000000, "Fee": "0%", "URL": "https://canarabank.com/"},
    {"Bank": "IDFC First Education", "LoanType": "Education", "Interest": 9.0, "MaxAmount": 5000000, "Fee": "1%", "URL": "https://www.idfcfirstbank.com/"},

    # Crop / Agriculture Loans
    {"Bank": "NABARD", "LoanType": "Crop", "Interest": 4.0, "MaxAmount": 300000, "Fee": "0%", "URL": "https://www.nabard.org/"},
    {"Bank": "SBI Agriculture", "LoanType": "Crop", "Interest": 4.5, "MaxAmount": 1000000, "Fee": "0%", "URL": "https://sbi.co.in/"},
    {"Bank": "Bank of Baroda (Agri)", "LoanType": "Crop", "Interest": 4.25, "MaxAmount": 750000, "Fee": "0%", "URL": "https://www.bankofbaroda.in/"},
    {"Bank": "HDFC Agri", "LoanType": "Crop", "Interest": 5.0, "MaxAmount": 500000, "Fee": "0.5%", "URL": "https://www.hdfcbank.com/"},
    {"Bank": "Union Bank (Agri)", "LoanType": "Crop", "Interest": 4.8, "MaxAmount": 500000, "Fee": "0%", "URL": "https://www.unionbankofindia.co.in/"},
    {"Bank": "IDBI Agri", "LoanType": "Crop", "Interest": 5.5, "MaxAmount": 400000, "Fee": "0%", "URL": "https://www.idbibank.in/"},

    # Business Loans
    {"Bank": "SBI (SME Loan)", "LoanType": "Business", "Interest": 12.5, "MaxAmount": 100000000, "Fee": "1%", "URL": "https://sbi.co.in/"},
    {"Bank": "HDFC Business Loan", "LoanType": "Business", "Interest": 14.0, "MaxAmount": 50000000, "Fee": "1.5%", "URL": "https://www.hdfcbank.com/"},
    {"Bank": "Axis Bank", "LoanType": "Business", "Interest": 14.5, "MaxAmount": 25000000, "Fee": "2%", "URL": "https://www.axisbank.com/"},
    {"Bank": "Bajaj Finserv", "LoanType": "Business", "Interest": 13.5, "MaxAmount": 50000000, "Fee": "2%", "URL": "https://www.bajajfinserv.in/"},
    {"Bank": "SIDBI", "LoanType": "Business", "Interest": 9.5, "MaxAmount": 250000000, "Fee": "0.5%", "URL": "https://www.sidbi.in/"},
    {"Bank": "Fullerton India", "LoanType": "Business", "Interest": 15.0, "MaxAmount": 20000000, "Fee": "2%", "URL": "https://www.fullertonindia.com/"},

    # Gold Loans
    {"Bank": "Muthoot Finance", "LoanType": "Gold", "Interest": 11.9, "MaxAmount": 10000000, "Fee": "0%", "URL": "https://www.muthootfinance.com/"},
    {"Bank": "Manappuram Finance", "LoanType": "Gold", "Interest": 12.5, "MaxAmount": 7500000, "Fee": "0.5%", "URL": "https://www.manappuram.com/"},
    {"Bank": "SBI Gold Loan", "LoanType": "Gold", "Interest": 9.8, "MaxAmount": 5000000, "Fee": "0.5%", "URL": "https://sbi.co.in/"},
    {"Bank": "Federal Bank", "LoanType": "Gold", "Interest": 10.9, "MaxAmount": 3000000, "Fee": "0.25%", "URL": "https://www.federalbank.co.in/"},
    {"Bank": "IIFL Gold Loan", "LoanType": "Gold", "Interest": 11.5, "MaxAmount": 2500000, "Fee": "0%", "URL": "https://www.iifl.com/"},

    # Property Loans
    {"Bank": "Bajaj Finserv", "LoanType": "Property", "Interest": 12.0, "MaxAmount": 50000000, "Fee": "2%", "URL": "https://www.bajajfinserv.in/"},
    {"Bank": "SBI Property Loan", "LoanType": "Property", "Interest": 11.5, "MaxAmount": 20000000, "Fee": "1%", "URL": "https://sbi.co.in/"},
    {"Bank": "HDFC Property Loan", "LoanType": "Property", "Interest": 11.75, "MaxAmount": 30000000, "Fee": "1.5%", "URL": "https://www.hdfcbank.com/"},
    {"Bank": "ICICI Property Loan", "LoanType": "Property", "Interest": 11.9, "MaxAmount": 25000000, "Fee": "1%", "URL": "https://www.icicibank.com/"}
]

# Simple DB for analytics
def init_db():
    conn = sqlite3.connect('analytics.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (id INTEGER PRIMARY KEY, username TEXT, income REAL, loan_amount REAL, approved INTEGER, loan_type TEXT, 
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, fullname TEXT, email TEXT)''')
    
    # Safely try to add columns if they don't exist
    try:
        c.execute("ALTER TABLE requests ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE users ADD COLUMN fullname TEXT")
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

init_db()

def calculate_emi(principal, rate, months):
    if rate == 0:
        return principal / months
    r = rate / (12 * 100) # monthly interest rate
    emi = principal * r * ((1 + r)**months) / (((1 + r)**months) - 1)
    return round(emi, 2)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('analytics.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('analytics.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT * FROM users WHERE username=? OR email=?", (username, email))
        if c.fetchone():
            flash('Username or Email already exists. Please try another.')
            conn.close()
            return redirect(url_for('register'))
            
        # Create new user
        hashed_pw = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, fullname, email) VALUES (?, ?, ?, ?)", 
                  (username, hashed_pw, fullname, email))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "Model is not trained. Please run model.py."}), 500

    data = request.json
    try:
        # Inputs
        gender = int(data.get('gender', 1))
        married = int(data.get('married', 0))
        income = float(data.get('income', 0))
        loan_amount = float(data.get('loan_amount', 0))
        credit_history = int(data.get('credit_history', 1))
        loan_type = data.get('loan_type', 'Personal')
        tenure_months = int(data.get('tenure_months', 60))
        preferred_bank = data.get('preferred_bank', 'Any')

        # Prediction
        cols = ['Gender', 'Married', 'Income', 'LoanAmount', 'CreditHistory']
        features = pd.DataFrame([[gender, married, income, loan_amount, credit_history]], columns=cols)
        prediction = model.predict(features)[0]
        approved = bool(prediction)

        # Document and Bank Details Validation
        aadhar = data.get('aadhar', '')
        pan = data.get('pan', '')
        bank_account = data.get('bank_account', '')
        ifsc = data.get('ifsc', '')

        if not (aadhar and pan and bank_account and ifsc):
            return jsonify({"error": "Valid Aadhar, PAN, and Bank details are required."}), 400

        existing_loan = int(data.get('existing_loan', 0))
        existing_emi = float(data.get('existing_emi', 0))

        # Logic: Max EMI should not exceed 40% of monthly income MINUS existing EMI
        monthly_income = income / 12
        max_emi = (monthly_income * 0.40) - (existing_emi if existing_loan == 1 else 0)

        # 1. Advanced Probability & Risk Calculation
        # Base probability from model and credit history
        prob = 0.5 + (0.4 if credit_history == 1 else -0.3)
        
        # Adjust based on debt-to-income ratio
        dti_ratio = (loan_amount / tenure_months) / monthly_income if monthly_income > 0 else 1
        if dti_ratio < 0.2: prob += 0.1
        elif dti_ratio > 0.5: prob -= 0.2
        
        # Adjust based on age (mocked)
        age = int(data.get('age', 30))
        if 25 <= age <= 50: prob += 0.05
        
        # Clamp probability
        prob = max(0.05, min(0.98, prob))
        
        # Final approval decision (can be overridden by hard rules)
        approved = bool(prob > 0.5 and model.predict(features)[0] == 1)

        # Hard Rejection Rules (Overrides probability)
        if max_emi <= 0 or (loan_amount / tenure_months) > (max_emi * 1.5):
            approved = False
            prob = min(prob, 0.3)

        # 2. Fraud Detection Feature (Dummy logic)
        is_fraudulent = False
        fraud_reason = None
        
        # Check for abnormal income vs loan amount (e.g. 10x annual income)
        if loan_amount > income * 10:
            is_fraudulent = True
            fraud_reason = "Suspicious Loan-to-Income Ratio"
        
        # Check for duplicate/abnormal Aadhar/PAN (dummy check)
        if pan.startswith("000") or aadhar.startswith("000"):
            is_fraudulent = True
            fraud_reason = "Invalid Identification Pattern"

        if is_fraudulent:
            approved = False
            prob = 0.01

        # 3. Risk Level
        risk_level = "Low"
        if prob < 0.4: risk_level = "High"
        elif prob < 0.7: risk_level = "Medium"

        # Filter banks by loan type
        available_banks = [b for b in banks_data if b['LoanType'].lower() == loan_type.lower()]
        
        # If no exact match, fallback to all banks
        if not available_banks:
            available_banks = banks_data

        # Sort by interest rate (lowest first)
        available_banks.sort(key=lambda x: x['Interest'])
        
        # If preferred bank is chosen, move it to top
        if preferred_bank != 'Any':
            pref_match = next((b for b in available_banks if b['Bank'] == preferred_bank), None)
            if pref_match:
                available_banks.remove(pref_match)
                available_banks.insert(0, pref_match)

        # Calculate EMI and Max Loan for each bank
        bank_options = []
        for b in available_banks:
            emi = calculate_emi(loan_amount, b['Interest'], tenure_months)
            
            r = b['Interest'] / (12 * 100)
            if r > 0:
                max_loan = max_emi / (r * ((1 + r)**tenure_months) / (((1 + r)**tenure_months) - 1))
            else:
                max_loan = max_emi * tenure_months
                
            max_loan = min(max_loan, b['MaxAmount']) # Cap at bank's max
            
            bank_options.append({
                "Bank": b['Bank'],
                "Interest": b['Interest'],
                "EMI": emi,
                "MaxEligible": round(max_loan, 2),
                "Fee": b['Fee'],
                "URL": b['URL']
            })

        # Log analytics
        conn = sqlite3.connect('analytics.db')
        c = conn.cursor()
        username = session.get('username', 'guest')
        c.execute("INSERT INTO requests (username, income, loan_amount, approved, loan_type) VALUES (?, ?, ?, ?, ?)",
                  (username, income, loan_amount, 1 if approved else 0, loan_type))
        conn.commit()
        conn.close()

        rejection_reason = None
        if not approved:
            if is_fraudulent:
                rejection_reason = f"Security Flag: {fraud_reason}. Please verify your details."
            elif credit_history == 0:
                rejection_reason = "Low Credit Score: Your credit history does not meet our minimum safety standards."
            elif max_emi <= 0:
                rejection_reason = "High Existing Debt: Your current EMI obligations exceed your repayment capacity."
            elif (loan_amount / tenure_months) > max_emi:
                rejection_reason = "Insufficient Income: Your monthly income is too low for the requested loan amount."
            else:
                rejection_reason = "Internal Risk Assessment: Your application does not meet our algorithmic safety criteria."

        response = {
            "approved": approved,
            "probability": round(prob * 100, 1),
            "risk_level": risk_level,
            "bank_options": bank_options if approved else [],
            "rejection_reason": rejection_reason,
            "is_fraudulent": is_fraudulent
        }
        
        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/credit_score', methods=['POST'])
def get_credit_score():
    data = request.json
    pan = data.get('pan', '').upper()
    
    if not re.match(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", pan):
        return jsonify({"error": "Invalid PAN format"}), 400
    
    # Sophisticated mock logic based on PAN components
    # 4th character: Holder type (P=Personal, C=Company, etc.)
    holder_type = pan[3] 
    # Sum of digits in PAN
    digits = re.findall(r'\d', pan)
    digit_sum = sum(int(d) for d in digits)
    
    # Base score influenced by holder type and digit patterns
    base = 600
    if holder_type == 'P': base += 50 # Personal accounts often have more history in our mock
    base += (digit_sum * 3) # Add variability
    
    # Add factors from income/existing loans (simulated)
    income_hint = int(digits[0]) * 100000 # Just a silly mock hint
    base += (income_hint / 100000) * 5
    
    # Cap between 300 and 900
    score = max(300, min(900, base))
    
    # Categories and realistic factors
    if score >= 800:
        category = "Excellent"
        color = "#10b981" # Green
        factors = ["No delayed payments in 36 months", "Credit utilization below 10%", "High credit mix"]
    elif score >= 700:
        category = "Good"
        color = "#3b82f6" # Blue
        factors = ["Consistent payment history", "Moderate credit age", "low inquiry rate"]
    elif score >= 600:
        category = "Average"
        color = "#f59e0b" # Orange
        factors = ["1-2 delayed payments", "High utilization (60%)", "New credit history"]
    else:
        category = "Poor"
        color = "#ef4444" # Red
        factors = ["Recent defaults detected", "Multiple hard inquiries", "Very high utilization"]
    
    return jsonify({
        "score": score,
        "category": category,
        "color": color,
        "factors": factors,
        "bureau": "CIBIL / Experian (Simulated)",
        "last_updated": "Just now"
    })

@app.route('/analytics', methods=['GET'])
def analytics():
    conn = sqlite3.connect('analytics.db')
    c = conn.cursor()
    
    # 1. Basic Stats
    c.execute("SELECT COUNT(*) FROM requests")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM requests WHERE approved = 1")
    approved = c.fetchone()[0]
    rejected = total - approved
    
    c.execute("SELECT loan_type, COUNT(*) as cnt FROM requests GROUP BY loan_type ORDER BY cnt DESC LIMIT 1")
    pop_loan = c.fetchone()
    
    # 2. Data for Charts
    c.execute("SELECT loan_type, COUNT(*) FROM requests GROUP BY loan_type")
    loan_types_data = dict(c.fetchall())
    
    conn.close()
    
    # Calculate Risk Distribution (Mocked for analytics)
    risk_distribution = {
        "Low Risk": round(total * 0.45) if total > 0 else 0,
        "Medium Risk": round(total * 0.35) if total > 0 else 0,
        "High Risk": round(total * 0.20) if total > 0 else 0
    }
    
    return jsonify({
        "total_requests": total,
        "approval_rate": round(approved/total * 100, 2) if total > 0 else 0,
        "popular_loan": pop_loan[0] if pop_loan else "N/A",
        "approval_distribution": [approved, rejected],
        "loan_types_labels": list(loan_types_data.keys()),
        "loan_types_values": list(loan_types_data.values()),
        "risk_distribution": risk_distribution
    })


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    user_message_lower = user_message.lower()
    
    if not user_message:
        return jsonify({"response": "Please ask a question."})

    # 1. Attempt to use Gemini AI for a smart, conversational response
    if chat_model:
        try:
            prompt = f"""
            You are 'Finly', a world-class Financial AI Specialist. 
            You provide expert advice on loans, EMI structures, credit score optimization, and banking protocols.
            Your tone is professional, analytical, yet encouraging.
            - Use <b>bold</b> for key terms and <br> for spacing.
            - If asked about loan eligibility, mention factors like Income, DTI ratio, and Credit History.
            - Avoid general knowledge; keep it focused on finance.
            
            Current User Query: {user_message}
            """
            response = chat_model.generate_content(prompt)
            # Clean up the response for HTML display
            resp_text = response.text.replace('\n', '<br>').replace('**', '<b>').replace('**', '</b>')
            return jsonify({"response": resp_text})
        except Exception as e:
            print(f"Gemini API Error: {e}")
            print(f"Gemini API Error: {e}")
            # Fall back to rule-based logic below if API fails
    
    # 2. Rule-based Fallback (If no Gemini key or API fails)
    response = "I'm still learning! You can ask me to <b>calculate EMI</b>, show you <b>loan plans</b>, compare <b>bank interest rates</b>, or tell you about required <b>documents</b>.<br><br><small>(Tip: Add a GEMINI_API_KEY in the code to make me super smart!)</small>"
    
    if "emi" in user_message_lower:
        numbers = re.findall(r"[\d\.]+", user_message_lower)
        nums = [float(n) for n in numbers if n.count('.') <= 1 and float(n) > 0]
        
        if len(nums) >= 3:
            principal = nums[0]
            rate = nums[1]
            months = nums[2]
            
            if rate > months and months < 30:
                rate, months = months, rate
                
            months = int(months)
            emi = calculate_emi(principal, rate, months)
            response = f"For a loan amount of ₹{principal:,.2f} at {rate}% interest for {months} months, your estimated EMI is <b>₹{emi:,.2f}</b>."
        else:
            response = "I can calculate your EMI! Please provide the loan amount, interest rate, and tenure in months. Example: <i>'calculate EMI for 1000000 at 10.5% for 60 months'</i>."
            
    elif any(word in user_message_lower for word in ["plan", "types", "options", "bank", "which loan"]):
        loan_types = {}
        for b in banks_data:
            ltype = b['LoanType']
            if ltype not in loan_types or b['Interest'] < loan_types[ltype]:
                loan_types[ltype] = b['Interest']
        
        plans_str = "<br>• " + "<br>• ".join([f"<b>{k} Loan</b> (Starting at {v}%)" for k, v in loan_types.items()])
        response = f"We have several loan plans available! Here are the best starting interest rates from our partner banks: {plans_str}<br><br>Which one are you interested in?"
        
    elif any(word in user_message_lower for word in ["document", "kyc", "aadhar", "pan", "paperwork"]):
        response = "For loan approval, we require:<br>• A valid 12-digit <b>Aadhar number</b><br>• A valid <b>PAN card</b><br>• <b>Bank Account details</b> with IFSC code<br><br>Uploading clear copies in the KYC section speeds up processing."
        
    elif any(word in user_message_lower for word in ["cibil", "credit", "score"]):
        response = "A good credit history (usually a <b>CIBIL score above 700</b>) significantly increases your chances of loan approval and can help you secure lower interest rates from top banks."
        
    elif any(word in user_message_lower for word in ["interest", "rate", "percentage"]):
        response = "Interest rates vary by loan type and bank. Home loans typically have the lowest rates (around 8.5%), while personal loans are higher (10-12%). Our system recommends the lowest rate for you automatically when you check eligibility."
        
    elif any(word in user_message_lower for word in ["eligibility", "approve", "reject", "qualify", "can i get"]):
        response = "Approval depends on factors like your <b>income</b>, <b>loan amount</b>, <b>credit history</b>, and <b>existing EMIs</b>. You can fill out the eligibility form on the dashboard to get an instant AI prediction!"
        
    elif any(word in user_message_lower for word in ["hello", "hi", "hey", "greetings"]):
        response = "Hello there! 👋 I am your Financial AI Assistant. I can help you find the best loan plans, calculate your EMI, and check your eligibility. What do you need help with?"
        
    elif any(word in user_message_lower for word in ["who are you", "what are you"]):
        response = "I am the AI Assistant for this Loan Prediction platform. I am here to help you navigate loan options, calculate costs, and answer any financial questions you might have!"
        
    elif any(word in user_message_lower for word in ["thank", "thanks"]):
        response = "You're very welcome! If you have any more questions about loans or finance, just ask."
        
    elif any(word in user_message_lower for word in ["how are you"]):
        response = "I'm just a computer program, but I'm doing great! Ready to help you with your financial questions. How can I assist you today?"
        
    elif "income" in user_message_lower or "salary" in user_message_lower:
        response = "Your annual income is a key factor in determining how much loan you can afford. Typically, banks prefer that your total EMIs do not exceed 40-50% of your monthly income."

    elif "age" in user_message_lower:
        response = "Age is a factor in loan approvals. Typically, you must be between 18 and 60 years old (or retirement age) to qualify for most loans. A longer remaining working life allows for a longer loan tenure."
        
    return jsonify({"response": response})

@app.route('/profile_data')
def profile_data():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = sqlite3.connect('analytics.db')
    c = conn.cursor()
    c.execute("SELECT fullname, email, username FROM users WHERE username=?", (session['username'],))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            "fullname": user[0],
            "email": user[1],
            "username": user[2]
        })
    return jsonify({"error": "User not found"}), 404


@app.route('/all_banks')
def all_banks():
    # Return all banks sorted by interest
    sorted_banks = sorted(banks_data, key=lambda x: x['Interest'])
    return jsonify(sorted_banks)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    new_fullname = data.get('fullname')
    new_email = data.get('email')
    new_password = data.get('password')
    
    conn = sqlite3.connect('analytics.db')
    c = conn.cursor()
    
    try:
        if new_password:
            hashed_pw = generate_password_hash(new_password)
            c.execute("UPDATE users SET fullname=?, email=?, password=? WHERE username=?", 
                      (new_fullname, new_email, hashed_pw, session['username']))
        else:
            c.execute("UPDATE users SET fullname=?, email=? WHERE username=?", 
                      (new_fullname, new_email, session['username']))
        
        conn.commit()
        return jsonify({"success": True, "message": "Settings updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
