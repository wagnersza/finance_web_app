from app import create_app
from app.models import db, Currency

def init_currencies():
    # Create default currencies
    currencies = [
        {
            'code': 'USD',
            'name': 'Dólar Americano',
            'symbol': '$'
        },
        {
            'code': 'EUR',
            'name': 'Euro',
            'symbol': '€'
        },
        {
            'code': 'BRL',
            'name': 'Real Brasileiro',
            'symbol': 'R$'
        }
    ]
    
    # Add currencies if they don't exist
    for currency_data in currencies:
        if not Currency.query.filter_by(code=currency_data['code']).first():
            currency = Currency(**currency_data)
            db.session.add(currency)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        init_currencies()