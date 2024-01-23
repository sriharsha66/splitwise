
from flask import Flask, request, jsonify,current_app
from flask_mysqldb import MySQL
# from collections import defaultdict
# from flask import Flask, request, jsonify
from flask_mail import Mail, Message  # Note the correct import here
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from collections import defaultdict

app = Flask(__name__)
app.config.from_pyfile('config.py')  # Create a separate config file for your app configuration

# Flask-Mail configuration for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'XXXXXXXX@gmail.com'  # Replace with your Gmail email
app.config['MAIL_PASSWORD'] = 'XXXX XXXX XXXX XXXX'  # Replace with your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'XXXXXXXX@gmail.com'  # Replace with your Gmail email

mail = Mail(app)   
# MySQL database setup
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'SXXXXXXXd'
app.config['MYSQL_DB'] = 'expense_app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Helper function to round decimals to two places
def round_decimal(amount):
    return round(amount, 2)

# Create tables if not exist
with app.app_context():
    cur = mysql.connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            name VARCHAR(255),
            email VARCHAR(255),
            mobile_number VARCHAR(255)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            payer_id INT,
            total_amount DECIMAL(12, 2),
            expense_type VARCHAR(255)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            expense_id INT,
            participant_id INT,
            share DECIMAL(12, 2),
            FOREIGN KEY (expense_id) REFERENCES expenses(id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mnames (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255)
        )
    ''')
    mysql.connection.commit()
    cur.close()

def send_weekly_email():
    try:
        with app.app_context():
            cur = mysql.connection.cursor()
            cur.execute('SELECT DISTINCT participant_id, SUM(share) AS total_owe FROM participants GROUP BY participant_id')
            expenses_participant_data = cur.fetchall()
            cur.close()

            for expense_data in expenses_participant_data:
                participant_id = expense_data['participant_id']
                total_owe = round_decimal(float(expense_data['total_owe']))

                if total_owe != 0:
                    email_subject = "Weekly Expense Summary"
                    email_body = f"Hello User {participant_id},\n\n"\
                                 f"Your total amount owed to others: {total_owe}"
                    send_email_async(email_subject, [get_user_email(participant_id)], email_body)

    except Exception as e:
        with app.app_context():
            current_app.logger.error(f"Error sending weekly email: {str(e)}")

def get_user_email(user_id):
    try:
        cur = mysql.connection.cursor()
        query = 'SELECT email FROM users WHERE user_id = %s'
        cur.execute(query, (user_id,))
        result = cur.fetchone()
        cur.close()

        if result:
            return result['email']
        else:
            return None  # User not found

    except Exception as e:
        current_app.logger.error(f"Error getting user email: {str(e)}")
        return None

# Function to get user balance by user_id
def get_user_balance(user_id):
    try:
        cur = mysql.connection.cursor()
        query = 'SELECT balance FROM user_balances WHERE user_id = %s'
        cur.execute(query, (user_id,))
        result = cur.fetchone()
        cur.close()

        if result:
            return result['balance']
        else:
            return 0.0  # Default to 0 balance if user not found

    except Exception as e:
        current_app.logger.error(f"Error getting user balance: {str(e)}")
        return 0.0
    
# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(func=send_weekly_email, trigger="interval", minutes=5)
scheduler.start()

def send_email_async(subject, recipients, body):
    with app.app_context():
        msg = Message(subject, recipients=recipients)
        msg.body = body
        mail.send(msg)

def get_user_email(user_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT email FROM users WHERE user_id = %s', (user_id,))
    email = cur.fetchone()['email']
    cur.close()
    return email

def format_balances(balances):
    return "\n".join([f"User {user_id}: ${balance}" for user_id, balance in balances.items()])

def send_email(subject, recipients, body):
    msg = Message(subject, recipients=recipients)
    msg.body = body
    mail.send(msg)

# API endpoint to add a user
@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        user_data = request.get_json()
        user_id = user_data['user_id']
        name = user_data['name']
        email = user_data['email']
        mobile_number = user_data['mobile_number']

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO users (user_id, name, email, mobile_number) VALUES (%s, %s, %s, %s)',
                    (user_id, name, email, mobile_number))
        mysql.connection.commit()
        cur.close()

        # Send a greeting email to the new user
        greeting_subject = "Welcome to Expense App"
        greeting_body = f"Hello {name},\n\nThank you for joining Expense App!"
        send_email(greeting_subject, [email], greeting_body)

        return jsonify({'message': 'User added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})



# API endpoint to add an expense
@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        expense_data = request.get_json()
        payer_id = expense_data['payer_id']
        total_amount = expense_data['total_amount']
        expense_type = expense_data['expense_type']
        participants = expense_data['participants']

        # Insert into expenses table
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO expenses (payer_id, total_amount, expense_type) VALUES (%s, %s, %s)',
                    (payer_id, total_amount, expense_type))
        mysql.connection.commit()

        # Retrieve the auto-incremented expense_id
        cur.execute('SELECT LAST_INSERT_ID()')
        expense_id = cur.fetchone()['LAST_INSERT_ID()']

        # Calculate share per participant based on expense type
        if expense_type == 'EQUAL':
            share_per_participant = round_decimal(float(total_amount) / len(participants))
        elif expense_type == 'EXACT':
            # Logic to handle EXACT type, ensure total shares match total amount
            pass  # Add your implementation here
        elif expense_type == 'PERCENT':
            # Logic to handle PERCENT type, ensure total percentage shares add up to 100
            pass  # Add your implementation here

        # Insert into participants table
        for participant_id, share in participants.items():
            cur.execute('INSERT INTO participants (expense_id, participant_id, share) VALUES (%s, %s, %s)',
                        (expense_id, participant_id, share))
        mysql.connection.commit()

        cur.close()
         # TODO: Send asynchronous email to participants
        return jsonify({'message': 'Expense added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})


# API endpoint to get balances for a user with history
@app.route('/get_balances/<user_id>', methods=['GET'])
def get_balances(user_id):
    balances = defaultdict(float)
    one_to_one_history = []

    try:
        # Calculate balances for expenses where the user is involved as a payer or participant
        cur = mysql.connection.cursor()

        # Payer balances
        query_payer = '''
            SELECT e.payer_id, e.total_amount
            FROM expenses e
            WHERE e.payer_id = %s
        '''
        cur.execute(query_payer, (user_id,))
        expenses_payer_data = cur.fetchall()

        for expense_data in expenses_payer_data:
            payer_id, amount = expense_data['payer_id'], expense_data['total_amount']
            balances[payer_id] += round_decimal(float(amount))
            one_to_one_history.append({'from': user_id, 'to': payer_id, 'amount': round_decimal(float(amount))})

        # Participant balances
        query_participant = '''
            SELECT p.participant_id, e.payer_id, e.total_amount, p.share
            FROM participants p
            JOIN expenses e ON p.expense_id = e.id
            WHERE p.participant_id = %s
        '''
        cur.execute(query_participant, (user_id,))
        expenses_participant_data = cur.fetchall()

        for expense_data in expenses_participant_data:
            participant_id = expense_data['participant_id']
            payer_id = expense_data['payer_id']
            total_amount = expense_data['total_amount']
            share = expense_data['share']

            # Update balances and history
            balances[payer_id] -= round_decimal(float(share))
            one_to_one_history.append({'from': participant_id, 'to': payer_id, 'amount': round_decimal(float(share))})

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        cur.close()

    # Filter balances to include only non-zero balances
    non_zero_balances = {k: v for k, v in balances.items() if v != 0.0}

    return jsonify({
        'user_id': user_id,
        'balances': non_zero_balances,
        'one_to_one_history': one_to_one_history
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
 