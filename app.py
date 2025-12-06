from flask import Flask
from flask_cors import CORS
from db import mongo, MONGO_URI_STRING
from client_routes import client_bp
from scheduler_routes import scheduler_bp

app = Flask(__name__)
app.config["MONGO_URI"] = MONGO_URI_STRING
CORS(app, origins="*")
mongo.init_app(app)

app.register_blueprint(client_bp)
app.register_blueprint(scheduler_bp)


if __name__ == '__main__':
    app.run(debug=True)
