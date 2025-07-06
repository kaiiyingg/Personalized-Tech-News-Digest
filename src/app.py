from flask import Flask, render_template, request, redirect, url_for, session, flash
from src.services.user_service import create_user, find_user_by_username, check_password
from src.models.user import User
import os #Needed to get environment variables 

app = Flask(__name__ )

app.secret_key = os.getenv('FLASK_SECRET_KEY')

@app.route('/')
def index():
    '''
    This route will check if a user is logged in. 
    If so, it displays a welcome message. Otherwise, it redirects to the login page.
    '''
    # 'session' stores data for each user between requests (e.g., login status)
    # 'request' contains data sent by the client (form data, query params, etc.)
    if 'user_id' in session:
        username = session.get('username', 'Guest') # Get username from session
        return render_template('index.html', username=username, logged_in=True)
    else:
        return redirect(url_for('login')) # Redirect to login if not logged in

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    This route handles user registration. 
    GET displays the registration form, and POST processes the registration data.
    '''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Create a new user using the service function
        user = create_user(username, email, password)
        
        if user:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists. Please try again.', 'danger')
    
    # For GET request or failed POST, render the registration form
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    This route handles user login. 
    GET displays the login form, and POST processes the login credentials.
    '''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = find_user_by_username(username)
        
        if user and check_password(user, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    '''
    This route handles user logout by clearing the session.
    '''
    session.pop('user_id', None)  # Remove user_id from session
    session.pop('username', None)  # Remove username from session   
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Ensures Flask app runs in debug mode only when script is executed directly. For production, set debug=False in app.run()
if __name__ == '__main__': app.run(debug=True)