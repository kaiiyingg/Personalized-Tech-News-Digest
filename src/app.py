import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify # type: ignore
from src.services.user_service import create_user, find_user_by_username, check_password
from src.services.source_service import get_sources_by_user, create_source, update_source, delete_source, get_source_by_id
from src.services.content_service import get_personalized_digest, mark_content_as_read, toggle_content_liked, update_content_liked
from src.models.user import User
from src.models.source import Source

# ------------------- APP CONFIG -------------------
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# ------------------- AUTH DECORATOR -------------------
def login_required_api(f):
    """
    Decorator to ensure a user is logged in for API endpoints.
    Returns JSON error if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ------------------- ROUTES -------------------

# --- Fast Flashcard View ---
@app.route('/fast', methods=['GET'])
@login_required_api
def fast():
    user_id = session['user_id']
    articles = get_personalized_digest(user_id, limit=1, offset=0, include_read=False)
    article = None
    for a in articles:
        if not a.get('is_read', False) and not a.get('is_liked', False):
            article = a
            break
    return render_template('fast.html', article=article, username=session.get('username'), current_year=datetime.now().year)

@app.route('/skip_article/<int:article_id>', methods=['POST'])
@login_required_api
def skip_article(article_id):
    return redirect(url_for('fast'))

# --- Article Interaction Routes for Dashboard Forms ---
@app.route('/mark_read/<int:article_id>', methods=['POST'])
def mark_read(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    mark_content_as_read(user_id, article_id, is_read=True)
    flash('Marked as read.', 'success')
    return redirect(url_for('index'))

@app.route('/like_article/<int:article_id>', methods=['POST'])
def like_article(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    update_content_liked(user_id, article_id, is_liked=True)
    flash('Article liked & saved.', 'success')
    return redirect(url_for('index'))

@app.route('/unlike_article/<int:article_id>', methods=['POST'])
def unlike_article(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    update_content_liked(user_id, article_id, is_liked=False)
    flash('Article unliked & unsaved.', 'info')
    return redirect(url_for('index'))

# --- Auth & User Management ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = create_user(username, email, password)
        if user:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists. Please try again.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- API Endpoints ---
@app.route('/api/sources', methods=['GET'])
@login_required_api
def get_sources():
    user_id = session['user_id']
    sources = get_sources_by_user(user_id)
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
    return jsonify(sources_data), 200

@app.route('/api/sources', methods=['POST'])
@login_required_api
def add_source():
    user_id = session['user_id']
    data = request.json
    if not data or not all(k in data for k in ('name', 'feed_url', 'type')):
        return jsonify({'error': 'Bad Request', 'message': 'Missing name, feed_url, or type'}), 400
    name = data['name']
    feed_url = data['feed_url']
    source_type = data['type']
    new_source = create_source(user_id, name, feed_url, source_type)
    if new_source:
        return jsonify({'message': 'Source added successfully', 'id': new_source.id}), 201
    else:
        return jsonify({'error': 'Conflict', 'message': 'Source URL might already exist.'}), 409

@app.route('/api/sources/<int:source_id>', methods=['PUT'])
@login_required_api
def update_source_api(source_id):
    user_id = session['user_id']
    data = request.json
    if not data:
        return jsonify({'error': 'Bad Request', 'message': 'No data provided for update'}), 400
    updated = update_source(
        source_id,
        user_id,
        name=data.get('name'),
        feed_url=data.get('feed_url'),
        type=data.get('type')
    )
    if updated:
        return jsonify({'message': 'Source updated successfully'}), 200
    else:
        existing_source = get_source_by_id(source_id, user_id)
        if not existing_source:
            return jsonify({'error': 'Not Found', 'message': 'Source not found or not owned by user.'}), 404
        return jsonify({'error': 'No Change', 'message': 'No valid fields to update or no change detected.'}), 400

@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
@login_required_api
def delete_source_api(source_id):
    user_id = session['user_id']
    deleted = delete_source(source_id, user_id)
    if deleted:
        return jsonify({'message': 'Source deleted successfully'}), 200
    else:
        return jsonify({'error': 'Not Found', 'message': 'Source not found or not owned by user.'}), 404

@app.route('/api/digest', methods=['GET'])
@login_required_api
def get_digest():
    user_id = session['user_id']
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    search_query = request.args.get('q')
    articles = get_personalized_digest(user_id, limit=limit, offset=offset, search_query=search_query)
    return jsonify({'articles': articles}), 200

@app.route('/api/content/<int:content_id>/read', methods=['POST'])
@login_required_api
def mark_content_read_api(content_id):
    user_id = session['user_id']
    data = request.json or {}
    is_read = data.get('is_read', True)
    success = mark_content_as_read(user_id, content_id, is_read=bool(is_read))
    if success:
        return jsonify({'message': 'Content marked as read.'}), 200
    else:
        return jsonify({'error': 'Failed to update read status.'}), 400

@app.route('/api/content/<int:content_id>/like', methods=['POST'])
@login_required_api
def like_content_api(content_id):
    user_id = session['user_id']
    success = update_content_liked(user_id, content_id, is_liked=True)
    if success:
        return jsonify({'message': 'Content liked & saved.'}), 200
    else:
        return jsonify({'error': 'Failed to like content.'}), 400

# ------------------- MAIN -------------------
if __name__ == '__main__':
    app.run(debug=True)