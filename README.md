# Expense Sharing Application

The Expense Sharing Application allows users to manage shared expenses among a group of friends or roommates. Users can add expenses, split them among different people, and keep track of balances.

## Features

1. **User Management**
   - Each user has a unique userId, name, email, and mobile number.

2. **Expense Types**
   - Expenses can be of three types: EQUAL, EXACT, or PERCENT.
   - Users can add any amount, select any type of expense, and split with any available users.

3. **Expense Addition**
   - Users can add an expense, specifying the payer, total amount, type, and participants.
   - Participants can have equal, exact, or percentage shares.

4. **Balance Calculation**
   - The application keeps track of balances between users based on added expenses.

5. **Email Notifications**
   - Participants receive asynchronous email notifications when added to an expense.

6. **Scheduled Email Job**
   - A scheduled job sends a weekly email to users with their total outstanding balances.

## Database Configuration

- The application uses MySQL as the database.
- Database connection details are specified in `db_config` within the code.
- Need to create a DB with specfic name.

## Installation and Setup

1. Install required packages:

   ```bash
   pip install Flask Flask-Mail mysql-connector-python

## MYSQL_Setup

1. Set up MySQL on your machine and create a database with the specified details in "db_config".

# Run the Application

1. python app.py (for Linux perfer to use python3 app.py)

2. Access the application at http://127.0.0.1:5000.

# API Endpoints

Add Expense

Endpoint: /add_expense
Method: POST
Input: JSON payload with payer_id, total_amount, expense_type, and participants.
Get Balances for a User

Endpoint: /get_balances/<user_id>
Method: GET
Optional Query Parameter: simplify (true/false)

# Notes
API responses should take less than 50 milliseconds.
Maximum 1000 participants per expense.
Maximum expense amount: INR 1,00,00,000.

