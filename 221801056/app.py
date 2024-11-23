from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the pre-trained collaborative filtering model
model_path = r'C:\Users\USER\Downloads\Job\Job\collaborative_filtering_model_sklearn.pkl'
model = joblib.load(model_path)

job_list = {
    101: "Software Engineer",
    102: "Data Scientist",
    103: "Product Manager",
    104: "Marketing Specialist",
    105: "UX Designer"
}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose another one.")
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!")
            return redirect(url_for('home'))
        else:
            flash("Login failed. Please check your username and password.")
    return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        degree = request.form['degree']
        skills = request.form['skills']

        user_id = session['user_id']
        recommendations = []

        # Simulate user-item interaction vector
        # Assuming user-item interaction matrix is of size (num_users, num_jobs)
        # Here we simulate a sparse interaction by initializing a vector of zeros and adding some values.

        user_features = np.zeros(84090)  # Assuming 84090 is the number of features or jobs in your matrix
        user_features[user_id] = 1  # This is just a placeholder, replace it with actual data

        # Use the model's 'transform' or 'components_' to get the user's latent features
        try:
            user_latent = model.transform(user_features.reshape(1, -1))  # Reshape to match expected input shape
        except AttributeError:
            flash("Model doesn't support 'transform' method, or it's not compatible.")
            return redirect(url_for('home'))

        # For each job, calculate the recommendation score based on the latent factors
        for job_id, job_title in job_list.items():
            # Simulate job latent features
            try:
                job_latent = model.components_[:, job_id - 101]  # Access job latent features
                prediction = np.dot(user_latent, job_latent)  # Compute recommendation score using dot product
                recommendations.append((job_title, prediction))
            except IndexError:
                flash(f"Error while processing job {job_id}.")
                continue

        # Sort and select top 3 recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        top_recommendations = recommendations[:3]

        return render_template('recommendation.html', recommendations=top_recommendations, degree=degree, skills=skills)
    
    return render_template('home.html')

@app.route('/recommendation')
def recommendation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('recommendation.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Logged out successfully!")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
