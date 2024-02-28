from sqlalchemy_utils import URLType
from eventwave_app.extensions import db
from eventwave_app.utils import FormEnum
from flask_login import UserMixin


class Comment(db.Model):
    """Comment model."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment = db.Column(db.Text, nullable=False)
    event_id = db.Column(
        db.Integer, db.ForeignKey('event.id'), nullable=False)
    event = db.relationship('Event', back_populates='comments')
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User')
    def __repr__(self):
        return f'<Comment: {self.comment}>'
    
class Event(db.Model):
    """Event model."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seatgeek_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    date_time = db.Column(db.String(200), nullable=False)
    performer = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(260), nullable=True)
    comments = db.relationship('Comment', back_populates='event')
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User')
    def __repr__(self):
        return f'<Event: {self.title}>'
    
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))
    email = db.Column(db.String(80))
    events = db.relationship('Event', backref='creator', lazy=True)
    def __repr__(self):
        return f'<User: {self.username}>'