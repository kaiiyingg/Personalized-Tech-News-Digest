import random
import pyotp 
import os
import sys
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

'''
Do not import the relevant methods only, import the class directly and if want the relevant methods, use class.method()
as if add/remove method from class, need to update import area also which is not maintainable
'''
import src.services.user_service as user_service
import src.services.source_service as source_service
import src.services.content_service as content_service

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

# --- Home/Discover route: latest summaries, daily digest ---
@app.route('/', methods=['GET'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    
    # Get articles grouped by topics
    topics_articles = content_service.get_articles_by_topics(user_id, limit_per_topic=8)

    username = session.get('username')
    current_year = datetime.now().year
    
    return render_template('index.html', 
                         topics_articles=topics_articles, 
                         username=username, 
                         current_year=current_year)

# --- Legacy route for backward compatibility ---
@app.route('/index', methods=['GET'])
def discover():
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = user_service.find_user_by_email(email)
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
        user = user_service.find_user_by_email(email)
        if not user:
            flash('No account found for password reset.', 'danger')
            return render_template('reset_password.html')
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code):
            flash('Invalid code. Please try again.', 'danger')
            return render_template('reset_password.html')
        # Update password
        user_service.update_user_password(user.id, new_password)
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
    content_service.mark_content_as_read(user_id, article_id, is_read=True)
    flash('Article marked as read', 'success')
    return redirect(url_for('index'))

@app.route('/like_article/<int:article_id>', methods=['POST'])
def like_article(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    content_service.update_content_liked(user_id, article_id, is_liked=True)
    flash('Article saved to favorites', 'success')
    return redirect(url_for('index'))

@app.route('/read_article/<int:article_id>')
def read_article(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    # Mark article as read
    content_service.mark_content_as_read(user_id, article_id, is_read=True)

    # Get the article URL to redirect to
    articles = content_service.get_personalized_digest(user_id, limit=1000)  # Get all articles
    article_url = None
    for article in articles:
        if article.get('id') == article_id:
            article_url = article.get('article_url')
            break
    
    if article_url:
        return redirect(article_url)
    else:
        flash('Article not found', 'danger')
        return redirect(url_for('index'))


# --- Auth & User Management ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = user_service.create_user(username, password, email)
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
    user = user_service.find_user_by_email(email)
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
        user = user_service.find_user_by_username(username)
        if user and user_service.check_password(user, password):
            if code:
                totp = pyotp.TOTP(user.totp_secret)
                if not totp.verify(code):
                    flash('Authentication code is invalid', 'danger')
                    return render_template('login.html')
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Welcome back!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Successfully logged out', 'info')
    return redirect(url_for('index'))

@app.route('/api/sources', methods=['GET'])
@login_required_api
def get_sources():
    user_id = session['user_id']
    sources = source_service.get_all_sources()
    sources_data = []
    for s in sources:
        sources_data.append({
            'id': s.id,
            'user_id': s.user_id,
            'name': s.name,
            'feed_url': s.feed_url,
            'last_fetched_at': s.last_fetched_at.isoformat() if s.last_fetched_at else None,
            'created_at': s.created_at.isoformat(),
            'updated_at': s.updated_at.isoformat() if s.updated_at else None
        })
    return jsonify(sources_data), 200


@app.route('/api/digest', methods=['GET'])
@login_required_api
def get_digest():
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    # Fetch general articles for all users (Only fast section shows personalised articles based on user's interested topics.)
    articles = content_service.get_general_digest(limit=limit, offset=offset)
    return jsonify({'articles': articles}), 200

@app.route('/api/content/<int:content_id>/read', methods=['POST'])
@login_required_api
def mark_content_read_api(content_id):
    user_id = session['user_id']
    data = request.json or {}
    is_read = data.get('is_read', True)
    success = content_service.mark_content_as_read(user_id, content_id, is_read=bool(is_read))
    if success:
        return jsonify({'message': 'Content marked as read.'}), 200
    else:
        return jsonify({'error': 'Failed to update read status.'}), 400

@app.route('/api/content/<int:content_id>/like', methods=['POST'])
@login_required_api
def like_content_api(content_id):
    try:
        user_id = session['user_id']
        print(f"Like API called - User ID: {user_id}, Content ID: {content_id}")
        success = content_service.update_content_liked(user_id, content_id, is_liked=True)
        if success:
            print(f"Successfully liked content {content_id} for user {user_id}")
            return jsonify({'message': 'Article saved to favorites'}), 200
        else:
            print(f"Failed to like content {content_id} for user {user_id}")
            return jsonify({'error': 'Failed to like content.'}), 400
    except Exception as e:
        print(f"Error in like_content_api: {e}")
        return jsonify({'error': 'Internal server error.'}), 500

@app.route('/api/content/<int:content_id>/unlike', methods=['POST'])
@login_required_api
def unlike_content_api(content_id):
    try:
        user_id = session['user_id']
        print(f"Unlike API called - User ID: {user_id}, Content ID: {content_id}")
        success = content_service.update_content_liked(user_id, content_id, is_liked=False)
        if success:
            print(f"Successfully unliked content {content_id} for user {user_id}")
            return jsonify({'message': 'Article removed from favorites'}), 200
        else:
            print(f"Failed to unlike content {content_id} for user {user_id}")
            return jsonify({'error': 'Failed to unlike content.'}), 400
    except Exception as e:
        print(f"Error in unlike_content_api: {e}")
        return jsonify({'error': 'Internal server error.'}), 500

# --- Fast Flashcard View ---
@app.route('/fast', methods=['GET'])
@login_required_api
def fast():
    user_id = session['user_id']
    # Get all articles for today (including read)
    all_articles = content_service.get_personalized_digest(user_id, limit=100, offset=0, include_read=True)
    # Filter out instruction items and count
    actual_articles = [a for a in all_articles if a.get('id')]
    total_articles = len(actual_articles)
    articles_read = sum(1 for a in actual_articles if a.get('is_read', False))
    # Get unread articles for flashcard view (automatically prioritized)
    unread_articles = [a for a in actual_articles if not a.get('is_read', False)]
    # Unread articles are automatically shown first
    article = unread_articles[0] if unread_articles else None
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
    # Get articles (including read ones) and filter for liked articles only
    articles = content_service.get_personalized_digest(user_id, limit=100, include_read=True)
    liked_articles = [a for a in articles if a.get('is_liked')]
    username = session.get('username')
    current_year = datetime.now().year
    return render_template('favorites.html', articles=liked_articles, username=username, current_year=current_year)


# --- Unlike Article (Remove from Favorites) ---
# This route allows a user to unlike an article, removing it from their favorites.
# It sets is_liked=False for the user and article in the database.
# After unliking, the article will no longer appear in the favorites page.
@app.route('/unlike_article/<int:article_id>', methods=['POST'])
def unlike_article(article_id):
    if 'user_id' not in session:
        flash('You must be logged in to perform this action', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    content_service.update_content_liked(user_id, article_id, is_liked=False)
    flash('Article removed from favorites', 'info')
    return redirect(url_for('index'))

# ------------------- MAIN -------------------
if __name__ == '__main__':
    app.run(debug=True)