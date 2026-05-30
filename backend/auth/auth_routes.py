from flask import Blueprint, request, jsonify
from .auth_utils import register_user, login_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json

    if register_user(data["username"], data["password"]):
        return jsonify({"message": "Signup successful"})
    
    return jsonify({"error": "User already exists"}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    if login_user(data["username"], data["password"]):
        return jsonify({"message": "Login successful"})
    
    return jsonify({"error": "Invalid credentials"}), 401