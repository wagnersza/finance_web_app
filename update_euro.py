from app import create_app
from app.models import db, Currency

def update_euro_symbol():
    app = create_app()
    with app.app_context():
        euro = Currency.query.filter_by(code='EUR').first()
        if euro:
            euro.symbol = '€'  # Using the proper Euro symbol
            db.session.commit()
            print("Updated EUR symbol successfully")
        else:
            print("EUR currency not found")

if __name__ == '__main__':
    update_euro_symbol()