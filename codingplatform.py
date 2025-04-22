from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import uuid
import random
import subprocess
import tempfile
import os

app = Flask(_name_)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    skill_level = db.Column(db.String(20))

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20))
    input_format = db.Column(db.String(100))
    output_format = db.Column(db.String(100))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'))
    code = db.Column(db.Text)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)

# Challenge Generator (simple mock)
challenges = [
    {"description": "Write a function that returns the factorial of a number.", "difficulty": "easy", "input_format": "int", "output_format": "int"},
    {"description": "Write a function to check if a string is a palindrome.", "difficulty": "medium", "input_format": "string", "output_format": "bool"},
    {"description": "Given a list of integers, return the maximum product of any two numbers.", "difficulty": "hard", "input_format": "List[int]", "output_format": "int"}
]

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user = User(username=data['username'], skill_level=data.get('skill_level', 'easy'))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered", "user_id": user.id})

@app.route('/generate-challenge', methods=['POST'])
def generate_challenge():
    skill = request.json.get('skill_level', 'easy')
    filtered = [c for c in challenges if c['difficulty'] == skill]
    selected = random.choice(filtered)
    challenge = Challenge(**selected)
    db.session.add(challenge)
    db.session.commit()
    return jsonify({"id": challenge.id, **selected})

@app.route('/submit-code', methods=['POST'])
def submit_code():
    data = request.json
    code = data['code']
    challenge_id = data['challenge_id']
    user_id = data['user_id']

    # Simple validation & execution (mock)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(code.encode())
            tmp.flush()
            result = subprocess.run(['python', tmp.name], capture_output=True, text=True, timeout=5)
            feedback = result.stdout + result.stderr
            score = 100 if result.returncode == 0 else 50
    except Exception as e:
        feedback = str(e)
        score = 0
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    submission = Submission(user_id=user_id, challenge_id=challenge_id, code=code, score=score, feedback=feedback)
    db.session.add(submission)
    db.session.commit()
    return jsonify({"score": score, "feedback": feedback})

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    results = db.session.query(User.username, db.func.sum(Submission.score).label('total_score'))\
        .join(Submission, User.id == Submission.user_id)\
        .group_by(User.username)\
        .order_by(db.desc('total_score')).limit(10).all()
    return jsonify([{"username": r[0], "score": r[1]} for r in results])

if _name_ == '_main_':
    db.create_all()
    app.run(debug=True)
