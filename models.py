# models.py

# We are importing the necessary tools from our installed packages.
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

# This creates a database object that will link SQLAlchemy to our Flask app.
db = SQLAlchemy()

# As per your document, user_type is an ENUM. This creates a special class for it.
class UserType(enum.Enum):
    CUSTOMER = 'CUSTOMER'
    PROVIDER = 'PROVIDER'
    ADMIN = 'ADMIN'

# This class defines the 'users' table in our database. It's a blueprint.
# It inherits from db.Model, which gives it all the database capabilities.
class User(db.Model):
    # This line explicitly names the table in the database 'users'.
    __tablename__ = 'users'
    
    # Below, we define each column of the table as specified in your document.
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False, default=UserType.CUSTOMER)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

# --- Profile Models ---

class CustomerProfile(db.Model):
    __tablename__ = 'customer_profiles'
    # This is a one-to-one relationship. The user_id is both the Primary Key
    # for this table and a Foreign Key pointing to the users table.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Profile-specific fields from the document
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    profile_picture_url = db.Column(db.String(255), nullable=True)

    # This creates a back-reference, allowing you to access the User object
    # from a CustomerProfile object, e.g., my_customer_profile.user
    user = db.relationship('User', backref=db.backref('customer_profile', uselist=False))

class ProviderProfile(db.Model):
    __tablename__ = 'provider_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Profile-specific fields from the document
    company_name = db.Column(db.String(100), nullable=False)
    business_registration_number = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(100), nullable=True)
    business_address = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('provider_profile', uselist=False))

class AdminProfile(db.Model):
    __tablename__ = 'admin_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Profile-specific fields from the document
    full_name = db.Column(db.String(100), nullable=False)
    permission_level = db.Column(db.String(50), default='SUPPORT_STAFF')

    user = db.relationship('User', backref=db.backref('admin_profile', uselist=False))


class VenueCategory(db.Model):
    __tablename__ = 'venue_categories'
    # [cite_start]Attributes from the document [cite: 83-86]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

class Amenity(db.Model):
    __tablename__ = 'amenities'
    # [cite_start]Attributes from the document [cite: 71-74]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon_url = db.Column(db.String(255), nullable=True)

# This is the "Junction Table" for the many-to-many relationship
# [cite_start]between Venues and Amenities [cite: 75]
venue_amenities = db.Table('venue_amenities',
    db.Column('venue_id', db.Integer, db.ForeignKey('venues.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenities.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'venues'
    # [cite_start]Attributes from the document [cite: 51-61]
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider_profiles.user_id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('venue_categories.id'), nullable=False)
    
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    capacity = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='UNDER_REVIEW', nullable=False)
    
    # Relationships
    provider = db.relationship('ProviderProfile', backref=db.backref('venues', lazy=True))
    category = db.relationship('VenueCategory', backref=db.backref('venues', lazy=True))
    
    # Many-to-many relationship with Amenity
    amenities = db.relationship('Amenity', secondary=venue_amenities, lazy='subquery',
        backref=db.backref('venues', lazy=True))

class VenueImage(db.Model):
    __tablename__ = 'venue_images'
    # [cite_start]Attributes from the document [cite: 63-68]
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    
    venue = db.relationship('Venue', backref=db.backref('images', lazy=True, cascade="all, delete-orphan"))
