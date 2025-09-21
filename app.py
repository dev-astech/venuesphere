# app.py

# Step 1: Import all the tools we need
import os
from flask import Flask, request, jsonify # Flask tools
from flask_bcrypt import Bcrypt # Password hashing tool
from flask_cors import CORS
from models import (
    db, User, UserType, CustomerProfile, ProviderProfile, AdminProfile,
    Venue, VenueCategory, Amenity # <-- Add these
)
from dotenv import load_dotenv # Tool to load our secret .env file
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity

# Step 2: Basic Application Setup
load_dotenv() # Load variables from the .env file

app = Flask(__name__) # Create our Flask application instance
CORS(app)

# Step 3: Configure the application
# We get the secret URLs and keys from the environment file
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# Step 4: Initialize extensions
# Link our extensions to the Flask app instance. Each is done only ONCE.
db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Step 5: Define API Endpoints (Controllers)

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    # --- Input Validation ---
    required_fields = ['email', 'password', 'phone_number', 'user_type']
    if not data or not all(key in data for key in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Add profile-specific validation
    user_type = data.get('user_type').upper()
    if user_type == 'CUSTOMER' and not all(key in data for key in ['first_name', 'last_name']):
        return jsonify({"error": "Customer profile requires first_name and last_name"}), 400
    if user_type == 'PROVIDER' and not 'company_name' in data:
        return jsonify({"error": "Provider profile requires company_name"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email address already registered"}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    new_user = User(
        email=data['email'],
        password_hash=hashed_password,
        phone_number=data['phone_number'],
        user_type=user_type
    )

    # --- Save to Database ---
    try:
        db.session.add(new_user)
        db.session.commit()

        # --- Create Associated Profile ---
        if new_user.user_type == UserType.CUSTOMER:
            profile = CustomerProfile(
                user_id=new_user.id,
                first_name=data['first_name'],
                last_name=data['last_name']
            )
        elif new_user.user_type == UserType.PROVIDER:
            profile = ProviderProfile(
                user_id=new_user.id,
                company_name=data['company_name']
            )
        else:
            db.session.rollback()
            return jsonify({"error": "Invalid user type for profile creation"}), 400

        db.session.add(profile)
        db.session.commit() # Commit the new profile

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500

    return jsonify({
        "message": "User and profile registered successfully!",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "user_type": new_user.user_type.value
        }
    }), 201

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Missing email or password"}), 400

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token)

    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.user_type == UserType.CUSTOMER:
        profile_data = user.customer_profile
        return jsonify({
            "id": user.id,
            "email": user.email,
            "first_name": profile_data.first_name,
            "last_name": profile_data.last_name
        })
    elif user.user_type == UserType.PROVIDER:
        profile_data = user.provider_profile
        return jsonify({
            "id": user.id,
            "email": user.email,
            "company_name": profile_data.company_name,
            "is_verified": profile_data.is_verified
        })

    return jsonify({"error": "Profile not found for user type"}), 404


@app.route('/venues', methods=['POST'])
@jwt_required()
def add_venue():
    # 1. Get the current user's ID from the JWT token
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # 2. Authorization Check: Ensure the user is a PROVIDER
    if not user or user.user_type != UserType.PROVIDER:
        return jsonify({"msg": "Access forbidden: Providers only"}), 403

    # 3. Get data from the request
    data = request.get_json()
    required_fields = ['name', 'category_id', 'address', 'capacity', 'price_per_hour']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # 4. Create a new Venue instance
    new_venue = Venue(
        provider_id=user.id, # Link the venue to the logged-in provider
        name=data['name'],
        category_id=data['category_id'],
        address=data['address'],
        capacity=data['capacity'],
        price_per_hour=data['price_per_hour'],
        description=data.get('description'), # .get() is safer for optional fields
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )

    # 5. Add to database and commit
    try:
        db.session.add(new_venue)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500

    # 6. Return a success response
    return jsonify({
        "message": "Venue created successfully and is under review.",
        "venue_id": new_venue.id
    }), 201


@app.cli.command("seed")
def seed_data():
    """Populates the database with initial essential data."""
    # Check if categories already exist
    if VenueCategory.query.first():
        print("Venue categories already exist. Skipping.")
    else:
        print("Creating venue categories...")
        categories = [
            VenueCategory(name='Wedding Hall', description='Spacious halls suitable for wedding ceremonies and receptions.'),
            VenueCategory(name='Conference Room', description='Professional spaces equipped for meetings and presentations.'),
            VenueCategory(name='Outdoor Space', description='Gardens, terraces, and open areas for various events.')
        ]
        db.session.bulk_save_objects(categories)
        db.session.commit()
        print("Venue categories created.")

    # Check if amenities already exist
    if Amenity.query.first():
        print("Amenities already exist. Skipping.")
    else:
        print("Creating amenities...")
        amenities = [
            Amenity(name='Free Wi-Fi'),
            Amenity(name='Parking Available'),
            Amenity(name='Projector'),
            Amenity(name='Air Conditioning'),
            Amenity(name='Catering Services')
        ]
        db.session.bulk_save_objects(amenities)
        db.session.commit()
        print("Amenities created.")


# This block runs when you execute 'python app.py' directly
if __name__ == '__main__':
    with app.app_context():
        # This creates the database tables from your models
        db.create_all()
    app.run(debug=True)