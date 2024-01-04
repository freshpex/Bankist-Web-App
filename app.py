from flask import Flask, render_template, request, g, session, url_for, redirect, flash, send_from_directory, abort, jsonify
from werkzeug.utils import secure_filename
from model import db, User, Transaction, Receipt, Loan, Account, Card
from flask_migrate import Migrate
from config import INTERNATIONAL_FEE
import stripe
import os
from faker import Faker
import random
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
stripe_keys = {
    'secret_key': os.environ['STRIPE_SECRET_KEY'],
    'publishable_key': os.environ['STRIPE_PUBLISHABLE_KEY'],
}
stripe.api_key = stripe_keys['secret_key']

fake = Faker()

migrate = Migrate(app, db)
db.init_app(app)

def hash_password(password):
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000)
    return salt + password_hash

def check_password(password, password_hash):
    salt = password_hash[:16]
    stored_password_hash = password_hash[16:]
    new_password_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000)
    return new_password_hash == stored_password_hash


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return None
    return {
        'id': user.id, 'email': user.email, 'firstname': user.firstname, 'lastname': user.lastname, 'username': user.username, 'gender': user.gender, 'password': user.password, 'notification_enabled': user.notification_enabled, 'privacy_enabled': user.privacy_enabled, 'account_type': user.account_type
    }


@app.before_request
def load_user():
    user_id = session.get('user_id')
    if user_id is not None:
        g.user = get_user(user_id)
    else:
        g.user = None

def check_user_exists(email, username):
    # Use the query object to check if user with the given email or username exists
    user = User.query.filter((User.email == email) | (User.username == username)).first()
    return bool(user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = secure_filename(request.form['username'])
        password = request.form['password']
        firstname = request.form['fname']
        lastname = request.form['lname']
        session['username'] = username

        if check_user_exists(email, username):
            error_message = 'User with the same email or username already exists.'
            return jsonify(success=False, error=error_message)
        
        password_hash = hash_password(password)
        user = User(email=email, username=username, password=password_hash, firstname=firstname, lastname=lastname)
        db.session.add(user)
        db.session.commit()
        
        return jsonify(success=True)
    return jsonify(success=False)

@app.route ('/login', methods= [ 'GET', 'POST'])
def login_post ():
    if  request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user:
            error = 'Invalid email or password'
            return jsonify(success=False, error=error)
        password_hash = user.password
        if check_password(password, password_hash):
            session['user_id'] = user.id
            return redirect('/dashboard')
        else:
            error = 'Invalid email or password'
            return jsonify(success=False, error=error)
    return redirect(url_for('index'))    

@app.route('/signout')
def signout():
    session.clear()
    session.pop('user_id', None)
    return redirect(url_for('index'))
   
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    print("Debug - g.user:", g.user)
    if g.user is None:
        print("Debug - Redirecting to index")
        return redirect(url_for('index'))
    print("Debug - Rendering dashboard.html")
    
    # Fetch the current user's accounts
    user_accounts = Account.query.filter_by(user_id=g.user['id']).all()
    
    user_cards = Card.query.filter_by(user_id=g.user['id']).all()
    
    if user_accounts:
        for loan_id in user_accounts:
            account_id = loan_id.id
        loan_history = Loan.query.filter_by(account_id=account_id).all()
    else:
        loan_history = []

    user_transactions = Transaction.query.filter_by(user_id=g.user['id']).all()

    deposits = sum(transaction.amount for transaction in user_transactions if transaction.amount > 0)
    withdrawals = sum(transaction.amount for transaction in user_transactions if transaction.amount < 0)
    
    current_user = User.query.get(g.user['id'])
    
    profile_image_url = url_for('static', filename=current_user.profile_image_path)
    
    print(profile_image_url)

    return render_template('dashboard.html', user_accounts=user_accounts, deposits=deposits, withdrawals=withdrawals, user_cards=user_cards, loan_history=loan_history, user_transactions=user_transactions, profile_image_url=profile_image_url)


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if g.user is None:
        return redirect(url_for('index'))
    
    name = request.form['name']
    feedback = request.form['feedback']
    
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
        return redirect(url_for('login_post'))
    return render_template('products.html')

@app.route('/createaccount', methods=['GET', 'POST'])
def createaccount():
    if g.user is None:
        return redirect(url_for('login_post'))
    
    if request.method == 'POST':
        print(request.files)
        fname = request.form['fname']
        lname = request.form['lname']
        gender = request.form['gender']
        picture = request.files.get('pic')
        id_front = request.files.get('front')
        id_back = request.files.get('back')
        account_type = request.form['account_type']
        
        passcode = request.form['passcode']
        pin = request.form.get('pin')
        
        if passcode != "CODED":
            return render_template('error.html', error="incorrect Passcode, Submit a complaint to an Admin")

         # Save the file to the images folder
        folder_name = 'static'
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        filename = secure_filename(picture.filename)
        picture.save(os.path.join(folder_name, filename))

        current_user = User.query.get(g.user['id'])
        current_user.firstname = fname
        current_user.lastname = lname
        current_user.gender = gender
        current_user.account_type = account_type
        current_user.pin = pin
        current_user.profile_image_path = filename

        new_account = Account(user_id=g.user['id'], account_type=account_type)
        db.session.add(new_account)
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('createaccount.html')

@app.route('/accounts')
def accounts():
    if g.user is None:
        return redirect(url_for('login_post'))
    
    user_accounts = Account.query.filter_by(user_id=g.user['id']).all()
    return render_template('accounts.html', user_accounts=user_accounts)

@app.template_filter('group_digits')
def group_digits(s):
    grouped_digits = [s[i:i + 4] for i in range(0, len(s), 4)]
    return ' '.join(grouped_digits)

@app.route('/cardpayment')
def cardpayment():
    if g.user is None:
        return redirect(url_for('login_post'))
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
    expiration_year = current_year + random.randint(1, 5)
    expiration_month = random.randint(1, 12)
    
    expiration_date = f"{expiration_month:02d}/{expiration_year}"

    return expiration_date

@app.route('/generate-card', methods=['POST'])
def generate_card():
    if g.user is None:
        return redirect(url_for('login_post'))
    card_type = request.form.get('card')
    card_number = generate_card_number(card_type)
    cvv = generate_cvv()
    expiration_date = generate_expiration_date()
    cardholder_name = request.form.get('name')
    user_id=g.user['id']

    card = Card(card_number=card_number, cvv=cvv, expiration_date=expiration_date, cardholder_name=cardholder_name, card_type=card_type, user_id=user_id)
    
    db.session.add(card)
    db.session.commit()

    return render_template('generated_card.html', card_number=card_number, cvv=cvv, expiration_date=expiration_date, cardholder_name=cardholder_name, card_type=card_type, group_digits=group_digits)

@app.route('/feedbacks')
def feedbacks():
    if g.user is None:
        return redirect(url_for('index'))
    return render_template('feedbacks.html')

@app.route('/view_receipt/<int:transaction_id>')
def view_receipt(transaction_id):
    if g.user is None:
        return redirect(url_for('login_post'))

    transaction = Transaction.query.get(transaction_id)
    return render_template('view_receipt.html', transaction=transaction)

def process_transaction_logic(account_id, amount, description, transaction_type, acc_number, destination_country=None, currency=None):
    account = Account.query.get(account_id)
    international_fee = INTERNATIONAL_FEE

    if not account:
        return jsonify(success=False, error='Insufficient funds')

    if account.balance < amount:
        return jsonify(success=False, error='Insufficient funds')

    account.balance -= amount

    international_fee = INTERNATIONAL_FEE

    account.balance -= international_fee if transaction_type == 'international' else 0

    destination_account_number = acc_number
    destination_account = Account.query.filter_by(account_number=destination_account_number).first()

    if destination_account:
        destination_account.balance += amount
        db.session.commit()

    new_transaction = Transaction(
        description=description,
        amount=-amount,
        user_id=account.user_id,
        timestamp=datetime.utcnow(),
        account_number=acc_number
    )

    db.session.add(new_transaction)
    db.session.commit()

    new_receipt = Receipt(
        transaction_id=new_transaction.id,
        amount=amount,
        description=description,
        destination_country=destination_country,
        currency=currency
    )

    db.session.add(new_receipt)
    db.session.commit()

    return {'success': True, 'confirmation_message': f"Transaction successfully processed. Receipt ID: {new_receipt.id}"}
 
# Route for processing transactions
@app.route('/process_transaction', methods=['POST'])
def process_transaction():
    if g.user is None:
        return jsonify(success=False, error='User not logged in.')

    transaction_type = request.form.get('transaction_type')
    account_id = request.form.get('source_account')
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    destination_country = request.form.get('destination_country')
    currency = request.form.get('currency')
    acc_number = request.form.get('acc_number')
    acc_name = request.form.get('acc_name')
    pin = int(request.form.get('pin'))
    
    current_user = User.query.get(g.user['id'])
    
    if pin != current_user.pin:
        return jsonify(success=False, error='Incorrect Pin')

    result = process_transaction_logic(account_id, amount, description, transaction_type, acc_number, destination_country, currency)

    if hasattr(result, 'json'):
        result = result.json        
        
    if result:
        if 'error' in result:
            return jsonify(success=False, error=result['error'])
        else:
            return jsonify(success=True, message=result['confirmation_message'])
        
@app.route('/loan_history/<int:account_id>')
def loan_history(account_id):
    if g.user is None:
        return redirect(url_for('login'))

    loan_history = Loan.query.filter_by(account_id=account_id).all()
    return render_template('loan_history.html', account_id=account_id, loan_history=loan_history)

@app.route('/request_loan', methods=['GET', 'POST'])
def request_loan():
    if g.user is None:
        return redirect(url_for('login_post'))

    if request.method == 'POST':
        account_id = request.form.get('account_id')
        amount = request.form.get('amount')
        pin = int(request.form.get('pin'))
    
        current_user = User.query.get(g.user['id'])
        
        if pin != current_user.pin:
            return jsonify(success=False, error='Incorrect Pin')

        new_loan = Loan(account_id=account_id, amount=amount, status='pending')

        db.session.add(new_loan)
        db.session.commit()

        loan_history = Loan.query.filter_by(account_id=account_id).all()

        for loan in loan_history:
            loan_request_successful = loan.status

        if loan_request_successful == 'pending':
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='Loan request failed.')

    return render_template('request_loan.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if g.user is None:
        return redirect(url_for('login_post'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        account_id = int(request.form['account_id'])

        account = Account.query.filter_by(id=account_id).first()

        if not account:
            return render_template('error.html', error_message='Invalid account.')

        if account.balance is None:
            account.balance = 0.0

        account.balance += amount

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
                    'currency': 'usd',
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

        session['account_id'] = account_id
        session['amount'] = amount

        return redirect(session.url)

    return render_template('deposit.html')

@app.route('/deposit/success', methods=['GET'])
def deposit_success():
    account_id = session.get('account_id')
    amount = session.get('amount')

    account = Account.query.filter_by(id=account_id).first()

    if not account:
        return render_template('error.html', error_message='Invalid account.')

    if account.balance is None:
        account.balance = 0.0

    account.balance += amount

    new_transaction = Transaction(
        description='Deposit',
        amount=amount,
        user_id=g.user['id']
    )

    db.session.add(new_transaction)
    db.session.commit()

    return render_template('deposit_success.html')


@app.route('/deposit/cancel')
def deposit_cancel():
    return render_template('error.html', error_message='Deposit canceled.')

@app.route('/bank_statement', methods=['GET', 'POST'])
def bank_statement():
    if g.user is None:
        return redirect(url_for('login_post'))

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

        user_transactions = Transaction.query.filter_by(user_id=g.user['id']).filter(
            Transaction.timestamp >= start_datetime, Transaction.timestamp <= end_datetime).all()

        return render_template('bank_statement.html', user_transactions=user_transactions)

    return render_template('bank_statement_filter.html')

@app.errorhandler(400)
def handle_bad_request(e):
    return 'Bad Request: {0}'.format(e.description), 400

if __name__ == '__main__':
    app.run()
