# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

# --- User & Profile Models ---

class UserType(enum.Enum):
    CUSTOMER = 'CUSTOMER'
    PROVIDER = 'PROVIDER'
    ADMIN = 'ADMIN'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False, default=UserType.CUSTOMER)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

class CustomerProfile(db.Model):
    __tablename__ = 'customer_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    profile_picture_url = db.Column(db.String(255), nullable=True)
    user = db.relationship('User', backref=db.backref('customer_profile', uselist=False))

class ProviderProfile(db.Model):
    __tablename__ = 'provider_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    business_registration_number = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(100), nullable=True)
    business_address = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref=db.backref('provider_profile', uselist=False))

class AdminProfile(db.Model):
    __tablename__ = 'admin_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    permission_level = db.Column(db.String(50), default='SUPPORT_STAFF')
    user = db.relationship('User', backref=db.backref('admin_profile', uselist=False))


# --- Venue & Listing Models ---

class VenueCategory(db.Model):
    __tablename__ = 'venue_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Amenity(db.Model):
    __tablename__ = 'amenities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon_url = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon_url': self.icon_url
        }

venue_amenities = db.Table('venue_amenities',
    db.Column('venue_id', db.Integer, db.ForeignKey('venues.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenities.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'venues'
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
    provider = db.relationship('ProviderProfile', backref=db.backref('venues', lazy=True))
    category = db.relationship('VenueCategory', backref=db.backref('venues', lazy=True))
    amenities = db.relationship('Amenity', secondary=venue_amenities, lazy='subquery',
        backref=db.backref('venues', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'capacity': self.capacity,
            'price_per_hour': str(self.price_per_hour), # Convert Decimal to string for JSON
            'status': self.status,
            'category': self.category.to_dict() if self.category else None,
            'amenities': [amenity.to_dict() for amenity in self.amenities]
        }

class VenueImage(db.Model):
    __tablename__ = 'venue_images'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    venue = db.relationship('Venue', backref=db.backref('images', lazy=True, cascade="all, delete-orphan"))