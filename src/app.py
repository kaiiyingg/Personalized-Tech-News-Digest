import random
import pyotp 
import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from src.services.user_service import create_user, check_password, find_user_by_email, update_user_password
from src.services.source_service import get_sources_by_user
from src.services.content_service import get_personalized_digest, mark_content_as_read, update_content_liked
from src.services.content_service import get_articles_by_topics

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

# --- Home route: redirect to login page ---
@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('login'))

@app.route('/index', methods=['GET'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    
    # Get articles grouped by topics
    topics_articles = get_articles_by_topics(user_id, limit_per_topic=8)
    
    username = session.get('username')
    current_year = datetime.now().year
    
    return render_template('index.html', 
                         topics_articles=topics_articles, 
                         username=username, 
                         current_year=current_year)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = find_user_by_email(email)
        if not user:
            flash('No account found with that email.', 'danger')
            return render_template('forgot_password.html')
        session['reset_email'] = email
        flash('Enter the 6-digit code from your authenticator app and your new password.', 'info')
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html')

# --- Reset Password Page ---
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']
        new_password = request.form['new_password']
        user = find_user_by_email(email)
        if not user:
            flash('No account found for password reset.', 'danger')
            return render_template('reset_password.html')
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code):
            flash('Invalid code. Please try again.', 'danger')
            return render_template('reset_password.html')
        # Update password
        update_user_password(user.id, new_password)
        flash('Password reset successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')
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


# --- Auth & User Management ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = create_user(username, password, email)
        if user:
            flash('Registration successful! Please set up your authenticator app.', 'success')
            # Show QR code for TOTP setup
            session['setup_email'] = email
            return redirect(url_for('setup_totp'))
        else:
            flash('Username or email already exists. Please try again.', 'danger')
            return render_template('register.html')
    return render_template('register.html')
# --- TOTP Setup Page ---
@app.route('/setup_totp', methods=['GET'])
def setup_totp():
    email = session.get('setup_email')
    if not email:
        flash('No email found for TOTP setup.', 'danger')
        return redirect(url_for('register'))
    user = find_user_by_email(email)
    if not user:
        flash('No account found for TOTP setup.', 'danger')
        return redirect(url_for('register') )
    totp = pyotp.TOTP(user.totp_secret)
    provisioning_uri = totp.provisioning_uri(name=email, issuer_name="TechPulse")
    return render_template('setup_totp.html', provisioning_uri=provisioning_uri)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        code = request.form.get('code')
        from src.services.user_service import find_user_by_username
        user = find_user_by_username(username)
        if user and check_password(user, password):
            if code:
                totp = pyotp.TOTP(user.totp_secret)
                if not totp.verify(code):
                    flash('Invalid authenticator code.', 'danger')
                    return render_template('login.html')
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

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

# --- Fast Flashcard View ---
@app.route('/fast', methods=['GET'])
@login_required_api
def fast():
    user_id = session['user_id']
    skipped = session.get('skipped_articles', set())
    # Get all articles for today (including read)
    all_articles = get_personalized_digest(user_id, limit=100, offset=0, include_read=True)
    # Filter out instruction items and count
    actual_articles = [a for a in all_articles if a.get('id')]
    total_articles = len(actual_articles)
    articles_read = sum(1 for a in actual_articles if a.get('is_read', False))
    # Get unread articles for flashcard view (already filtered for articles with ID)
    unread_articles = [a for a in actual_articles if not a.get('is_read', False)]
    # Prioritize skipped articles at the top - using safer get() method
    skipped_articles = [a for a in unread_articles if a.get('id') in skipped]
    unskipped_articles = [a for a in unread_articles if a.get('id') not in skipped]
    ordered_articles = skipped_articles + unskipped_articles
    article = ordered_articles[0] if ordered_articles else None
    return render_template(
        'fast.html',
        article=article,
        username=session.get('username'),
        current_year=datetime.now().year,
        articles_read=articles_read,
        total_articles=total_articles
    )


# --- Favorites (Liked Content) ---
@app.route('/favorites', methods=['GET'])
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    # Get only liked articles
    articles = get_personalized_digest(user_id, limit=100)
    liked_articles = [a for a in articles if a.get('is_liked')]
    username = session.get('username')
    current_year = datetime.now().year
    return render_template('favorites.html', articles=liked_articles, username=username, current_year=current_year)


# --- Skip Article (Flashcard View) ---
# This route allows a user to skip an article in the fast (flashcard) view.
# Skipped articles are tracked in the session for the current day and prioritized at the top of the flashcard list.
# Skipping does NOT mark the article as read while unskipped articles will be marked as read.
@app.route('/skip_article/<int:article_id>', methods=['POST'])
def skip_article(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    # Track skip in session for the day (not persisted in DB)
    skipped = session.get('skipped_articles', set())
    skipped.add(article_id)
    session['skipped_articles'] = skipped
    flash('Article skipped.', 'info')
    return redirect(url_for('fast'))

# --- Unlike Article (Remove from Favorites) ---
# This route allows a user to unlike an article, removing it from their favorites.
# It sets is_liked=False for the user and article in the database.
# After unliking, the article will no longer appear in the favorites page.
@app.route('/unlike_article/<int:article_id>', methods=['POST'])
def unlike_article(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    update_content_liked(user_id, article_id, is_liked=False)
    flash('Article unliked & removed from favorites.', 'info')
    return redirect(url_for('index'))

# ------------------- MAIN -------------------
if __name__ == '__main__':
    app.run(debug=True)