from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)  # e.g., USD, EUR, GBP
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(5), nullable=False)

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    accounts = db.relationship('Account', backref='bank', lazy=True)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    currency = db.relationship('Currency')
    expenses = db.relationship('Expense', backref='account', lazy=True)
    incomes = db.relationship('Income', backref='account', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    expenses = db.relationship('Expense', backref='category', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False, default='expense')  # 'expense' or 'revenue'

    @property
    def is_expense(self):
        return self.type == 'expense'

    @property
    def display_amount(self):
        return -self.amount if self.is_expense else self.amount

    def update_account_balance(self):
        if self.account:
            if self.is_expense:
                self.account.balance -= self.amount
            else:
                self.account.balance += self.amount
            db.session.add(self.account)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    category = db.relationship('Category')
    currency = db.relationship('Currency')

class Report:
    def __init__(self, expenses):
        self.expenses = expenses

    def total_expenses(self):
        return sum(expense.amount for expense in self.expenses)

    def expenses_by_category(self):
        category_totals = {}
        for expense in self.expenses:
            if expense.category in category_totals:
                category_totals[expense.category] += expense.amount
            else:
                category_totals[expense.category] = expense.amount
        return category_totals