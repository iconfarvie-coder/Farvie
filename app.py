from flask import Flask, render_template, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

# --- AUTHENTICATION API ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400
        
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Registration successful!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "User already exists"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['email'] = user['email']
        return jsonify({
            "message": "Login successful",
            "balance": user['crypto_balance'],
            "wallet": user['web3_wallet'] or "No wallet connected"
        }), 200
    
    return jsonify({"error": "Invalid email or password"}), 401

# --- USER PROFILE & DATA API ---
@app.route('/api/user/data', methods=['GET'])
def get_user_data():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    user = conn.execute('SELECT crypto_balance, web3_wallet FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return jsonify({
        "balance": user['crypto_balance'],
        "wallet": user['web3_wallet'] or "No wallet connected"
    })

# --- SECURE WITHDRAWAL ENGINE ---
@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json()
    wallet_address = data.get('wallet')
    amount = float(data.get('amount', 0))
    
    if not wallet_address or amount <= 0:
        return jsonify({"error": "Invalid request arguments"}), 400
        
    conn = get_db_connection()
    user = conn.execute('SELECT crypto_balance FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['crypto_balance'] < amount:
        conn.close()
        return jsonify({"error": "Insufficient mining balance"}), 400
        
    new_balance = user['crypto_balance'] - amount
    conn.execute('UPDATE users SET crypto_balance = ? WHERE id = ?', (new_balance, session['user_id']))
    conn.execute('INSERT INTO withdrawals (user_id, wallet_address, amount) VALUES (?, ?, ?)', 
                 (session['user_id'], wallet_address, amount))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Withdrawal request submitted successfully", "new_balance": new_balance}), 200

# --- SIMULATED MINING SYNC ENGINE ---
@app.route('/api/miner/sync', methods=['POST'])
def sync_mining_rewards():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json()
    mined_amount = float(data.get('mined', 0))
    
    conn = get_db_connection()
    user = conn.execute('SELECT crypto_balance FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    updated_balance = user['crypto_balance'] + mined_amount
    
    conn.execute('UPDATE users SET crypto_balance = ? WHERE id = ?', (updated_balance, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "Synced", "balance": updated_balance}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8765, debug=True)
