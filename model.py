import sqlite3, random
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Integer, Column, ForeignKey, String
from datetime import datetime
# Initializing an instance of the SQLAlchemy class
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    username = db.Column(db.String(50), unique=True)    
    gender = db.Column(db.String(50))
    privacy_enabled = db.Column(db.Boolean, default=False)
    notification_enabled = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(2505))
    account_type = db.Column(db.String(10))
    accounts = db.relationship('Account', backref='user', lazy=True)
    password = db.Column(db.String(64))
    @db.event.listens_for(db.session, 'before_flush')
    
    def create_account_number(session, flush_context, instances):
        for instance in session.new:
            if isinstance(instance, User):
                instance.account = instance.id + 10000000000
                
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.Integer, unique=True, default=lambda: random.randint(10000000000, 99999999999))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_type = db.Column(db.String(10))
    balance = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(255))
    amount = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)  # Changed this line
    amount = db.Column(db.Float)
    status = db.Column(db.String(20))  # e.g., 'approved', 'pending', 'rejected'

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    amount = db.Column(db.Float)
    description = db.Column(db.String(255))
    destination_country = db.Column(db.String(50))
    currency = db.Column(db.String(10))

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), unique=True)
    cvv = db.Column(db.String(3))
    expiration_date = db.Column(db.String(7))
    cardholder_name = db.Column(db.String(100))
    card_type = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)    
