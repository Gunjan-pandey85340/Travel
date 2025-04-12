from flask import Blueprint, request, jsonify, current_app
from bson.objectid import ObjectId
from utils.password_utils import hash_password, check_password
from utils.jwt_util import token_required
from pymongo import MongoClient
import jwt
import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["Travel"]
users = db["users"]

auth_bp = Blueprint("auth_bp", __name__)

# 🔐 Protected Route (Test JWT)
@auth_bp.route("/protected", methods=["GET"])
@token_required
def protected():
    return jsonify({"status": 200, "msg": "Access granted!", "user_id": request.user_id})

# 📝 Registration Route
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    existing_user = users.find_one({"email": data["email"]})
    
    if existing_user:
        return jsonify({"status": 400, "msg": "Email already registered"}), 400

    hashed_pw = hash_password(data["password"])

    user = {
        "fullName": data["fullName"],
        "email": data["email"],
        "phonenumber": data["phonenumber"],
        "password": hashed_pw,
    }
    users.insert_one(user)
    return jsonify({"status": 200, "msg": "User registered successfully"})

# 🔐 Login Route with JWT
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = users.find_one({"email": data["email"]})

    if not user or not check_password(data["password"], user["password"]):
        return jsonify({"status": 401, "msg": "Invalid email or password"}), 401

    token = jwt.encode({
        "user_id": str(user["_id"]),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, current_app.config["SECRET_KEY"], algorithm="HS256")

    # Make sure the token is a string
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    return jsonify({
        "status": 200,
        "msg": "Login successful",
        "token": token,
        "user": {
            "_id": str(user["_id"]),
            "email": user["email"],
            "fullName": user["fullName"]
        }
    })

# 📧 Email Verification for Password Reset
@auth_bp.route("/verify_email", methods=["POST"])
def verify_email():
    data = request.get_json()
    user = users.find_one({"email": data["email"]})
    if user:
        return jsonify({"status": 200, "msg": "Email verified", "id": str(user["_id"])})
    return jsonify({"status": 404, "msg": "Email not found"}), 404

# 🔁 Update Password (Can also protect with @token_required)
@auth_bp.route("/update_password", methods=["POST"])
def update_password():
    data = request.get_json()
    user = users.find_one({"_id": ObjectId(data["_id"])})

    if not user or not check_password(data["old_password"], user["password"]):
        return jsonify({"status": 401, "msg": "Old password incorrect"}), 401

    new_hashed = hash_password(data["new_password"])
    users.update_one({"_id": ObjectId(data["_id"])}, {"$set": {"password": new_hashed}})
    return jsonify({"status": 200, "msg": "Password updated successfully"})
