from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .models import db

def create_app():
    app = Flask(__name__, static_url_path='/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Import models
    from .models import Currency, Bank, Account, Category, Expense, Income, Budget
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Initialize default currency if it doesn't exist
        try:
            usd = Currency.query.filter_by(code='USD').first()
            if not usd:
                usd = Currency(code='USD', name='US Dollar', symbol='$')
                db.session.add(usd)
                db.session.commit()
        except Exception as e:
            print(f"Error initializing default currency: {e}")

    # Register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app