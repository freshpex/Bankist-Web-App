from flask import Flask, render_template, request, g, session, url_for, redirect, flash, send_from_directory, abort
import sqlite3, hashlib, os, requests
from werkzeug.utils import secure_filename
from model import db, User, Transaction, Receipt, Loan, Account, Card
from flask_migrate import Migrate
from config import INTERNATIONAL_FEE
import stripe, os
from faker import Faker
import random
from datetime import datetime

fake = Faker()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
DATABASE_FILE = 'instance/database.db'
stripe_keys = {
    'secret_key': os.environ['STRIPE_SECRET_KEY'],
    'publishable_key': os.environ['STRIPE_PUBLISHABLE_KEY'],
}
stripe.api_key = stripe_keys['secret_key']

migrate = Migrate(app, db)
db.init_app(app)

# Function handling the hash password
def hash_password(password):
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000)
    return salt + password_hash

# Function handling the password checker for correctness and tallying
def check_password(password, password_hash):
    salt = password_hash[:16]
    stored_password_hash = password_hash[16:]
    new_password_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000)
    return new_password_hash == stored_password_hash


def get_user(user_id):
    query = "SELECT id, email, firstname, lastname, username, gender, password, notification_enabled, privacy_enabled, profile_image, account_type FROM user WHERE id = ?"
    args = (user_id,)
    row = db_query(query, args)

    if not row:
        return None

    return {
        'id': row[0][0], 'email': row[0][1], 'firstname': row[0][2], 'lastname': row[0][3], 'username': row[0][4], 'gender': row[0][5], 'password': row[0][10], 'notification_enabled': bool(row[0][7]), 'privacy_enabled': bool(row[0][6]), 'account_type': row[0][9]
    }


@app.before_request
def load_user():
    user_id = session.get('user_id')
    if user_id is not None:
        g.user = get_user(user_id)
    else:
        g.user = None

# Get a useable connection to the database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
        db.row_factory = sqlite3.Row
    return db

# Close the database connection when the app shuts down
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# return the results from a database query
def db_query(query, args=None):
    cur = get_db().execute(query, args or ())
    rv = cur.fetchall()
    cur.close()
    return rv

# execute a database query
def db_execute(query, args=()):
    conn = get_db()
    conn.execute(query, args)
    conn.commit()
    return True

def check_user_exists(email, username):
    # Check if user with the given email or username exists
    query = "SELECT id FROM user WHERE email = ? OR username = ?"
    args = (email, username)
    user = db_query(query, args)

    return bool(user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        username = secure_filename(request.form['username'])
        password = request.form['password']
        firstname = request.form['fname']
        lastname = request.form['lname']
        password = request.form['password']
        session['username'] = username

        # Check if user already exists
        if check_user_exists(email, username):
            error_message = 'User with the same email or username already exists.'
            return render_template('signup.html', error=error_message)

        # Hash password
        password_hash = hash_password(password)

        # Insert user into the database
        query = "INSERT INTO user (email, username, password, firstname, lastname) VALUES (?, ?, ?)"
        args = (email, username, password_hash, firstname, lastname)

        db_execute(query, args)

        # Redirect to sign-in page
        return redirect(url_for('login'))

    # Render sign-up page
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Check if user exists in database
        query = "SELECT id, password FROM user WHERE username = ?"
        args = (username,)
        row = db_query(query, args)

        if not row:  # Check if row is empty
            # User not found
            error = 'Invalid email or password'
            return render_template('login.html', error=error)

        # Check password
        password_hash = row[0][1]
        if check_password(password, password_hash):
            # Password is correct, store user ID in session
            # Access the first row's first element
            session['user_id'] = row[0][0]
            return redirect('/dashboard')
        else:
            # Password is incorrect
            error = 'Invalid email or password'
            return render_template('login.html', error=error)

    # Render sign-in page
    return render_template('login.html')


@app.route('/signout')
def signout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

   
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if g.user is None:
        return redirect(url_for('login'))
    # Fetch the current user's accounts
    user_accounts = Account.query.filter_by(user_id=g.user['id']).all()
    
    user_cards = Card.query.filter_by(user_id=g.user['id']).all()
    
    for loan_id in user_accounts:
        account_id = loan_id.id
    
    loan_history = Loan.query.filter_by(account_id=account_id).all()
    
    # Fetch the current user's Transactions
    user_transactions = Transaction.query.filter_by(user_id=g.user['id']).all()

    # Calculate the sum of deposits and withdrawals
    deposits = sum(transaction.amount for transaction in user_transactions if transaction.amount > 0)
    withdrawals = sum(transaction.amount for transaction in user_transactions if transaction.amount < 0)

    return render_template('dashboard.html', user_accounts=user_accounts, deposits=deposits, withdrawals=withdrawals, user_cards=user_cards, loan_history=loan_history)


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if g.user is None:
        return redirect(url_for('login'))
    
    name = request.form['name']
    feedback = request.form['feedback']
    
    # Fetch the current user's accounts
    user_accounts = Account.query.filter_by(user_id=g.user['id']).all()
    return render_template('dashboard.html', user_accounts=user_accounts)

@app.route('/message', methods=['POST'])
def message():    
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']
    return f"Your message has been sent. Thank you!:{name, email, subject, message}"
    

@app.route('/products')
def products():
    if g.user is None:
        return redirect(url_for('login'))
    return render_template('products.html')

@app.route('/createaccount', methods=['GET', 'POST'])
def createaccount():
    if g.user is None:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        gender = request.form['gender']
        username = request.form['username']
        account_type = request.form['account_type']

        # Fetch the current user instance
        current_user = User.query.get(g.user['id'])

        # Update the user details
        current_user.username = username
        current_user.firstname = fname
        current_user.lastname = lname
        current_user.gender = gender
        current_user.account_type = account_type

        new_account = Account(user_id=g.user['id'], account_type=account_type)
        db.session.add(new_account)

        # Commit the changes to the database
        db.session.commit()

        # Redirect to account page
        return redirect(url_for('accounts'))

    # Render the createaccount page
    return render_template('createaccount.html')



@app.route('/accounts')
def accounts():
    if g.user is None:
        return redirect(url_for('login'))
    
    # Fetch the current user's accounts
    user_accounts = Account.query.filter_by(user_id=g.user['id']).all()
    return render_template('accounts.html', user_accounts=user_accounts)  # Pass user_accounts to the template

@app.template_filter('group_digits')
def group_digits(s):
    # Format the string s by grouping digits in fours
    grouped_digits = [s[i:i + 4] for i in range(0, len(s), 4)]
    return ' '.join(grouped_digits)

@app.route('/cardpayment')
def cardpayment():
    if g.user is None:
        return redirect(url_for('login'))
    user_cards = Card.query.filter_by(user_id=g.user['id']).all()
    return render_template('cardpayment.html', user_cards=user_cards)

def generate_card_number(card_type):
    card_prefixes = {
        'visa': ['4'],
        'master': ['5'],
        'amex': ['34', '37'],
        'discover': ['6011'],
    }

    if card_type not in card_prefixes:
        raise ValueError("Invalid card type")

    prefix = random.choice(card_prefixes[card_type])
    card_number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(14)])  # 15 digits (excluding check digit)

    check_digit = str((10 - sum(int(digit) for digit in card_number) % 10) % 10)
    card_number += check_digit

    return card_number

def generate_cvv():
    return str(random.randint(100, 999))

def generate_expiration_date():
    current_year = datetime.now().year
    expiration_year = current_year + random.randint(1, 5)  # Card valid for 1 to 5 years
    expiration_month = random.randint(1, 12)
    
    expiration_date = f"{expiration_month:02d}/{expiration_year}"

    return expiration_date

@app.route('/generate-card', methods=['POST'])
def generate_card():
    if g.user is None:
        return redirect(url_for('login'))
    card_type = request.form.get('card')
    card_number = generate_card_number(card_type)
    cvv = generate_cvv()
    expiration_date = generate_expiration_date()
    cardholder_name = request.form.get('name')
    # Assuming g.user is the currently logged-in user
    user_id=g.user['id']

    # Create a new Card instance and associate it with the current user
    card = Card(card_number=card_number, cvv=cvv, expiration_date=expiration_date, cardholder_name=cardholder_name, card_type=card_type, user_id=user_id)
    
    # Add the new card to the database
    db.session.add(card)
    db.session.commit()

    return render_template('generated_card.html', card_number=card_number, cvv=cvv, expiration_date=expiration_date, cardholder_name=cardholder_name, card_type=card_type, group_digits=group_digits)

@app.route('/feedbacks')
def feedbacks():
    if g.user is None:
        return redirect(url_for('login'))
    return render_template('feedbacks.html')

@app.route('/transaction')
def transaction():
    if g.user is None:
        return redirect(url_for('login'))
    user_accounts = User.query.filter_by(id=g.user['id']).all()
    return render_template('transaction.html', user_accounts=user_accounts)

@app.route('/history')
def history():
    if g.user is None:
        return redirect(url_for('login'))

    user_transactions = Transaction.query.filter_by(user_id=g.user['id']).all()
    return render_template('history.html', user_transactions=user_transactions)

@app.route('/view_receipt/<int:transaction_id>')
def view_receipt(transaction_id):
    if g.user is None:
        return redirect(url_for('login'))

    transaction = Transaction.query.get(transaction_id)
    return render_template('view_receipt.html', transaction=transaction)

# Route for processing transactions
@app.route('/process_transaction_logic', methods=['POST'])
def process_transaction_logic(account_id, amount, description, transaction_type, destination_country=None, currency=None):
    account = Account.query.get(account_id)
    international_fee = INTERNATIONAL_FEE

    if not account:
        return render_template('error.html', error_message='Invalid source account.')

    if account.balance < amount:
        return render_template('error.html', error_message='Insufficient funds.')
    
    if transaction_type == 'international':
        amount = amount + international_fee
        
    account.balance -= amount

    new_transaction = Transaction(
        description=description,
        amount=-amount,
        user_id=account.user_id
    )

    db.session.add(new_transaction)
    db.session.commit()

    international_fee = INTERNATIONAL_FEE

    account.balance -= international_fee if transaction_type == 'international' else 0
    new_receipt = Receipt(
        transaction_id=new_transaction.id,
        amount=amount,
        description=description,
        destination_country=destination_country,
        currency=currency
    )

    db.session.add(new_receipt)
    db.session.commit()
    return render_template('confirmation.html', confirmation_message=f"Transaction successfully processed. Receipt ID: {new_receipt.id}")


# Route for processing transactions
@app.route('/process_transaction', methods=['POST'])
def process_transaction():
    if g.user is None:
        return redirect(url_for('login'))

    transaction_type = request.form.get('transaction_type')
    account_id = request.form.get('source_account')
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    destination_country = request.form.get('destination_country')
    currency = request.form.get('currency')
    acc_number = request.form.get('acc_number')
    acc_name = request.form.get('acc_name')

    if transaction_type == 'international':
        destination_country = request.form.get('destination_country')
        currency = request.form.get('currency')
        international_fee = INTERNATIONAL_FEE        
        amount -= international_fee
        
    user_accounts = Account.query.filter_by(user_id=g.user['id']).all() 

    if len(user_accounts) > 1:
        return render_template('process_transaction.html', user_accounts=user_accounts, amount=amount, description=description, transaction_type=transaction_type, source_account=account_id, destination_country=destination_country, currency=currency) 
    return process_transaction_logic(account_id, amount, description, transaction_type, destination_country, currency)

# Route for processing transactions
@app.route('/process_double_transaction', methods=['POST'])
def process_double_transaction():
    if g.user is None:
        return redirect(url_for('login'))

    transaction_type = request.form.get('transaction_type')
    account_id = request.form.get('source_account')
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    destination_country = request.form.get('destination_country')
    currency = request.form.get('currency')
    acc_number = request.form.get('acc_number')
    acc_name = request.form.get('acc_name')
    return process_transaction_logic(account_id, amount, description, transaction_type, destination_country, currency)


@app.route('/loan_history/<int:account_id>')
def loan_history(account_id):
    if g.user is None:
        return redirect(url_for('login'))

    loan_history = Loan.query.filter_by(account_id=account_id).all()
    return render_template('loan_history.html', account_id=account_id, loan_history=loan_history)

@app.route('/request_loan', methods=['GET', 'POST'])
def request_loan():
    if g.user is None:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        amount = float(request.form.get('amount'))

        # Create a new loan request
        new_loan = Loan(account_id=account_id, amount=amount, status='pending')

        # Add the loan request to the database
        db.session.add(new_loan)
        db.session.commit()

        # Redirect to loan history page
        return redirect(url_for('loan_history', account_id=account_id))

        for loan in loan_history:
            loan_request_successful = loan.status

        if loan_request_successful == 'pending':
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='Loan request failed.')

    return render_template('request_loan.html')  # Replace with the actual template name

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if g.user is None:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        amount = float(request.form['amount'])
        account_id = int(request.form['account_id'])
        print(account_id)

        # Fetch the user's account
        account = Account.query.filter_by(id=account_id).first()

        if not account:
            return render_template('error.html', error_message='Invalid account.')

        # Ensure that account.balance is initialized to 0.0 if it's None
        if account.balance is None:
            account.balance = 0.0

        # Perform the deposit
        account.balance += amount

        # Create a new transaction record
        new_transaction = Transaction(
            description='Deposit',
            amount=amount,
            user_id=g.user['id']
        )

        db.session.add(new_transaction)
        db.session.commit()
        
        # Create a Stripe Session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',  # Change to your desired currency
                    'unit_amount': int(amount * 100),  # Amount in cents
                    'product_data': {
                        'name': 'Deposit',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('deposit_success', _external=True),
            cancel_url=url_for('deposit_cancel', _external=True),
        )

        return redirect(session.url)
    return render_template('deposit.html')

@app.route('/deposit/success')
def deposit_success():
    return render_template('confirmation.html', confirmation_message='Deposit successful!')

@app.route('/deposit/cancel')
def deposit_cancel():
    return render_template('error.html', error_message='Deposit canceled.')

@app.errorhandler(400)
def handle_bad_request(e):
    return 'Bad Request: {0}'.format(e.description), 400

if __name__ == '__main__':
    app.run()
