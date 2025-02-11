from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .models import db, Bank, Account, Currency, Expense, Category, Budget, Income
from datetime import datetime, timedelta
from sqlalchemy import func, case
import calendar

app = Flask(__name__)
main = Blueprint('main', __name__)

def calculate_account_balances(accounts):
    for account in accounts:
        # Get total expenses
        total_expenses = db.session.query(func.sum(Expense.amount)).filter(Expense.account_id == account.id).scalar() or 0
        # Get total incomes
        total_incomes = db.session.query(func.sum(Income.amount)).filter(Income.account_id == account.id).scalar() or 0
        # Calculate net balance (incomes - expenses)
        account.balance = total_incomes - total_expenses

@main.route('/')
def index():
    # Get accounts with related data
    accounts = Account.query.join(Bank).join(Currency).all()
    
    # Get expenses by category (considering expense type)
    category_expenses = db.session.query(
        Category.name,
        func.sum(case(
            (Expense.type == 'expense', Expense.amount),
            else_=0
        ))
    ).join(Expense).group_by(Category.name).all()
    
    category_labels = []
    category_amounts = []
    if category_expenses:
        category_labels = [item[0] for item in category_expenses]
        category_amounts = [float(item[1] or 0) for item in category_expenses]
    
    # Get monthly expenses for the last 6 months (considering expense type)
    today = datetime.utcnow()
    six_months_ago = today - timedelta(days=180)
    
    monthly_expenses = db.session.query(
        func.strftime('%Y-%m', Expense.date).label('month'),
        func.sum(case(
            (Expense.type == 'expense', Expense.amount),
            else_=0
        )).label('total')
    ).filter(
        Expense.date >= six_months_ago,
        Expense.type == 'expense'  # Only include actual expenses
    ).group_by('month').order_by('month').all()
    
    monthly_labels = []
    monthly_amounts = []
    
    if monthly_expenses:
        for expense in monthly_expenses:
            year, month = map(int, expense[0].split('-'))
            month_name = calendar.month_abbr[month]
            monthly_labels.append(f"{month_name} {year}")
            monthly_amounts.append(float(expense[1] or 0))
    
    # Get default currency (USD)
    default_currency = Currency.query.filter_by(code='USD').first()
    
    # Calculate account balances (considering both expenses and revenues)
    for account in accounts:
        expenses_total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.account_id == account.id,
            Expense.type == 'expense'
        ).scalar() or 0
        
        revenues_total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.account_id == account.id,
            Expense.type == 'revenue'
        ).scalar() or 0
        
        account.balance = revenues_total - expenses_total
    
    return render_template('index.html',
                         accounts=accounts,
                         category_labels=category_labels,
                         category_amounts=category_amounts,
                         monthly_labels=monthly_labels,
                         monthly_amounts=monthly_amounts,
                         default_currency=default_currency)

@main.route('/banks', methods=['GET', 'POST'])
def banks():
    if request.method == 'POST':
        name = request.form.get('name')
        bank = Bank(name=name)
        db.session.add(bank)
        db.session.commit()
        return redirect(url_for('main.banks'))
    
    banks = Bank.query.all()
    return render_template('banks.html', banks=banks)

@main.route('/accounts', methods=['GET', 'POST'])
def accounts():
    if request.method == 'POST':
        name = request.form.get('name')
        bank_id = request.form.get('bank_id')
        currency_id = request.form.get('currency_id')
        account = Account(name=name, bank_id=bank_id, currency_id=currency_id)
        db.session.add(account)
        db.session.commit()
        return redirect(url_for('main.accounts'))
    
    accounts = Account.query.join(Bank).join(Currency).all()
    calculate_account_balances(accounts)
    banks = Bank.query.all()
    currencies = Currency.query.all()
    return render_template('accounts.html', accounts=accounts, banks=banks, currencies=currencies)

@main.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        account_id = request.form.get('account_id')
        transaction_type = request.form.get('type', 'expense')
        
        expense = Expense(
            amount=amount,
            description=description,
            category_id=category_id,
            account_id=account_id,
            type=transaction_type,
            date=datetime.utcnow()
        )
        
        account = Account.query.get(account_id)
        if account:
            if transaction_type == 'expense':
                account.balance -= amount
            else:
                account.balance += amount
        
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('main.expenses'))
    
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    categories = Category.query.all()
    accounts = Account.query.all()
    return render_template('expenses.html', expenses=expenses, categories=categories, accounts=accounts)

@main.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        try:
            # Clean and parse amount value
            raw_amount = request.form.get('amount', '0')
            amount = float(raw_amount.replace(
                request.form.get('currency_symbol', '').strip(), ''
            ).replace(',', '.').strip())
            
            description = request.form.get('description')
            category_id = request.form.get('category_id')
            account_id = request.form.get('account_id')
            transaction_type = request.form.get('type', 'expense')
            
            # Create and save the expense
            expense = Expense(
                amount=abs(amount),
                description=description,
                category_id=category_id,
                account_id=account_id,
                type=transaction_type,
                date=datetime.utcnow()
            )
            
            db.session.add(expense)
            expense.update_account_balance()
            db.session.commit()
            
            return redirect(url_for('main.expenses'))
            
        except Exception as e:
            print(f"Error adding expense: {str(e)}")
            db.session.rollback()
            flash('Error adding expense: ' + str(e), 'error')
            return redirect(url_for('main.add_expense'))
    
    categories = Category.query.all()
    accounts = [
        {
            'id': a.id,
            'name': a.name,
            'currency_id': a.currency_id
        } for a in Account.query.all()
    ]
    banks = Bank.query.all()
    currencies = [
        {
            'id': c.id,
            'code': c.code,
            'name': c.name,
            'symbol': c.symbol
        } for c in Currency.query.all()
    ]
    
    return render_template('add_expense.html', 
                         categories=categories,
                         accounts=accounts,
                         banks=banks,
                         currencies=currencies)

@main.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        name = request.form.get('name')
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('main.categories'))
    
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@main.route('/currencies', methods=['GET', 'POST'])
def currencies():
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        symbol = request.form.get('symbol')
        currency = Currency(code=code, name=name, symbol=symbol)
        db.session.add(currency)
        db.session.commit()
        return redirect(url_for('main.currencies'))
    
    currencies = Currency.query.all()
    return render_template('currencies.html', currencies=currencies)

@main.route('/add_category_ajax', methods=['POST'])
def add_category_ajax():
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'category': {
            'id': category.id,
            'name': category.name
        }
    })

@main.route('/add_account_ajax', methods=['POST'])
def add_account_ajax():
    name = request.form.get('name')
    bank_id = request.form.get('bank_id')
    currency_id = request.form.get('currency_id')
    
    account = Account(name=name, bank_id=bank_id, currency_id=currency_id)
    db.session.add(account)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'account': {
            'id': account.id,
            'name': account.name
        }
    })

@main.route('/add_bank_ajax', methods=['POST'])
def add_bank_ajax():
    name = request.form.get('name')
    
    bank = Bank(name=name)
    db.session.add(bank)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'bank': {
            'id': bank.id,
            'name': bank.name
        }
    })

@main.route('/add_currency_ajax', methods=['POST'])
def add_currency_ajax():
    code = request.form.get('code')
    name = request.form.get('name')
    symbol = request.form.get('symbol')
    
    currency = Currency(code=code, name=name, symbol=symbol)
    db.session.add(currency)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'currency': {
            'id': currency.id,
            'code': currency.code,
            'name': currency.name,
            'symbol': currency.symbol
        }
    })

app.register_blueprint(main)