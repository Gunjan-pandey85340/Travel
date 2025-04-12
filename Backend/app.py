from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xyz12345'  # ✅ Secret key
CORS(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["Travel"]
users_collection = db["users"]

# Register routes
from routes.auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix="/user")

if __name__ == "__main__":
    app.run(debug=True)
