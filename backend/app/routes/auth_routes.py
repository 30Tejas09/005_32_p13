from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.db_session import get_session
from app.models.schema import User

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'reporter').strip().lower()
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()

    if not username or not password or not full_name:
        return jsonify({"error": "Username, password, and full name are required."}), 400

    if role not in ['admin', 'handler', 'reporter']:
        return jsonify({"error": "Role must be one of: admin, handler, reporter"}), 400

    db = get_session()
    try:
        existing = db.query(User).filter_by(username=username).first()
        if existing:
            return jsonify({"error": f"Username '{username}' is already taken."}), 409

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            full_name=full_name,
            email=email,
            phone=phone
        )
        db.add(new_user)
        db.commit()
        return jsonify({
            "message": "User registered successfully.",
            "user": new_user.to_dict()
        }), 201
    finally:
        db.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    db = get_session()
    try:
        user = db.query(User).filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid username or password."}), 401

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        return jsonify({
            "message": "Login successful.",
            "user": user.to_dict()
        }), 200
    finally:
        db.close()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        # Check header if passed
        user_header = request.headers.get('X-User-Id')
        if user_header:
            user_id = user_header

    if not user_id:
        return jsonify({"user": None}), 200

    db = get_session()
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"user": None}), 200
        return jsonify({"user": user.to_dict()}), 200
    finally:
        db.close()
