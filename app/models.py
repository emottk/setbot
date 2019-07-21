from datetime import datetime
from app import db

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	slack_username = db.Column(db.String(64), index=True, unique=True)
	slack_userid = db.Column(db.Integer, index=True, unique=True)
	set_scores = db.relationship('Score', backref='user', lazy='dynamic')

	def __repr__(self):
		return '<User {}>'.format(self.slack_username)
	

class Score(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	orig_input = db.Column(db.String(64))
	value = db.Column(db.Time, index=True)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Score {}>'.format(self.value)
