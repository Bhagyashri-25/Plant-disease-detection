import os
from flask import Flask, redirect, render_template, request, flash, session
from PIL import Image
import torchvision.transforms.functional as TF
import CNN
import numpy as np
import torch
import pandas as pd
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

# Load disease and supplement information
disease_info = pd.read_csv('disease_info.csv', encoding='cp1252')
supplement_info = pd.read_csv('supplement_info.csv', encoding='cp1252')

# Load the model
model = CNN.CNN(39)
model.load_state_dict(torch.load("plant_disease_model_1_latest.pt"))
model.eval()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Change this to a strong secret key

# MongoDB setup
client = MongoClient("mongodb+srv://<your-username>:<your-password>@cluster0.mongodb.net/<your-database>?retryWrites=true&w=majority")  # Replace with your MongoDB URI
client = MongoClient(MONGO_URI)
db = client["your_database_name"]

# Prediction function
def prediction(image_path):
    image = Image.open(image_path)
    image = image.resize((224, 224))
    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1, 3, 224, 224))
    output = model(input_data)
    output = output.detach().numpy()
    index = np.argmax(output)
    return index

# Routes
@app.route('/')
def home_page():
    return render_template('dashboard.html')

@app.route('/home')
def dashboard_page():
    return render_template('home.html')

@app.route('/contact')
def contact():
    return render_template('contact-us.html')

@app.route('/index')
def ai_engine_page():
    return render_template('index.html')

@app.route('/mobile-device')
def mobile_device_detected_page():
    return render_template('mobile-device.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        image = request.files['image']
        filename = image.filename
        file_path = os.path.join('static/uploads', filename)
        image.save(file_path)
        print(file_path)
        pred = prediction(file_path)
        title = disease_info['disease_name'][pred]
        description = disease_info['description'][pred]
        prevent = disease_info['Possible Steps'][pred]
        image_url = disease_info['image_url'][pred]
        supplement_name = supplement_info['supplement name'][pred]
        supplement_image_url = supplement_info['supplement image'][pred]
        supplement_buy_link = supplement_info['buy link'][pred]
        return render_template('submit.html', title=title, desc=description, prevent=prevent,
                               image_url=image_url, pred=pred, sname=supplement_name,
                               simage=supplement_image_url, buy_link=supplement_buy_link)

@app.route('/market', methods=['GET', 'POST'])
def market():
    return render_template('market.html', supplement_image=list(supplement_info['supplement image']),
                           supplement_name=list(supplement_info['supplement name']),
                           disease=list(disease_info['disease_name']),
                           buy=list(supplement_info['buy link']))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            flash('Email already registered!', 'danger')
            return redirect('/register')
        
        # Hash the password and insert into the database
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        users_collection.insert_one({'name': name, 'email': email, 'password': hashed_password})
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Find the user in the database
        user = users_collection.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['user'] = user['name']  # Store user name in session
            flash('Login successful!', 'success')
            return redirect('/home')  # Redirect to /home after successful login
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from session
    flash('You have been logged out.', 'success')  # Flash message to indicate logout
    return redirect('/')  # Redirect to the home page

if __name__ == '__main__':
    app.run(debug=True)
