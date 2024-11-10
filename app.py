from eventwave_app.extensions import app, db
from eventwave_app.routes import main, auth
from flask_migrate import Migrate

app.register_blueprint(main)
app.register_blueprint(auth)

with app.app_context():
    db.create_all()
    migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)

# if __name__ == '__main__':
#     app.run(host='127.0.0.1', port=8080, debug=True)