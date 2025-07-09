from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify # type: ignore
from src.services.user_service import create_user, find_user_by_username, check_password
from src.services.source_service import get_sources_by_user, create_source, update_source, delete_source, get_source_by_id
from src.models.user import User
from src.models.source import Source
import os #Needed to get environment variables 
from functools import wraps

app = Flask(__name__ )

app.secret_key = os.getenv('FLASK_SECRET_KEY')

def login_required_api(f):
    """
    Decorator to ensure a user is logged in for API endpoints.
    Returns JSON error if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Return a JSON error for API requests, not a redirect
            return jsonify({'error': 'Unauthorized', 'message': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/sources', methods=['GET'])
@login_required_api # Apply the decorator to protect the API endpoint (created above)
def get_sources():
    user_id = session['user_id'] # Get user_id from session, guaranteed by decorator
    sources = get_sources_by_user(user_id) # Call service function

    # Convert list of Source objects to a list of dictionaries for JSON response
    sources_data = []
    for s in sources:
        sources_data.append({
            'id': s.id,
            'user_id': s.user_id,
            'name': s.name,
            'feed_url': s.feed_url,
            'type': s.type,
            'last_fetched_at': s.last_fetched_at.isoformat() if s.last_fetched_at else None,
            'created_at': s.created_at.isoformat(),
            'updated_at': s.updated_at.isoformat() if s.updated_at else None
        })
    return jsonify(sources_data), 200 # Return JSON response with 200 OK status

@app.route('/api/sources', methods=['POST'])
@login_required_api
def add_source():
    user_id = session['user_id']
    data = request.json # Get JSON data from the request body

    # Basic validation: check if required fields are present
    if not data or not all(k in data for k in ('name', 'feed_url', 'type')):
        return jsonify({'error': 'Bad Request', 'message': 'Missing name, feed_url, or type'}), 400

    name = data['name']
    feed_url = data['feed_url']
    source_type = data['type'] # Using 'source_type' to avoid conflict with Python's built-in type() function

    new_source = create_source(user_id, name, feed_url, source_type) # Call service function
    if new_source:
        # Return 201 Created status for successful resource creation
        return jsonify({'message': 'Source added successfully', 'id': new_source.id}), 201
    else:
        # Return 409 Conflict if there's a unique constraint violation (e.g., duplicate URL)
        return jsonify({'error': 'Conflict', 'message': 'Source URL might already exist.'}), 409

@app.route('/api/sources/<int:source_id>', methods=['PUT'])
@login_required_api
def update_source_api(source_id):
    user_id = session['user_id']
    data = request.json
    if not data:
        return jsonify({'error': 'Bad Request', 'message': 'No data provided for update'}), 400

    # Pass only the fields that are present in the request JSON to the service function
    updated = update_source(
        source_id,
        user_id,
        name=data.get('name'),
        feed_url=data.get('feed_url'),
        type=data.get('type')
    ) # Call service function

    if updated:
        return jsonify({'message': 'Source updated successfully'}), 200
    else:
        # Check if source exists but doesn't belong to user, or if no fields were updated
        # A more robust check here would be to first try to get the source by ID
        # to differentiate between a 404 (not found) and 403 (forbidden/not owned)
        existing_source = get_source_by_id(source_id, user_id)
        if not existing_source:
            return jsonify({'error': 'Not Found', 'message': 'Source not found or not owned by user.'}), 404

        # If source exists but no valid fields were provided or no change happened
        return jsonify({'error': 'No Change', 'message': 'No valid fields to update or no change detected.'}), 400


@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
@login_required_api
def delete_source_api(source_id):
    user_id = session['user_id']
    deleted = delete_source(source_id, user_id) # Call service function
    if deleted:
        return jsonify({'message': 'Source deleted successfully'}), 200
    else:
        # Return 404 if the source wasn't found or wasn't owned by the user
        return jsonify({'error': 'Not Found', 'message': 'Source not found or not owned by user.'}), 404

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
if __name__ == '__main__':
    app.run(debug=True)