"""
TechPulse - Personalized Tech News Digest Application

A Flask web application that provides personalized technology news aggregation:
- User authentication with TOTP (Two-Factor Authentication)
- RSS feed ingestion from multiple tech news sources
- AI-powered content classification and filtering
- Personalized content recommendations based on user interests
- Fast-view mode for quick article consumption
- User preference management and content interaction tracking

Memory-optimized for 512MB hosting environments with efficient content processing.
"""

import random
import pyotp 
import os
import sys
import threading
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

# Import service modules directly for better maintainability
import src.services.user_service as user_service
import src.services.source_service as source_service
import src.services.content_service as content_service

# ===== APPLICATION CONSTANTS =====

LOGIN_TEMPLATE = 'login.html'
CHANGE_EMAIL_TEMPLATE = 'change_email.html'
RESET_PASSWORD_TEMPLATE = 'reset_password.html'
RESET_USERNAME_TEMPLATE = 'reset_username.html'
USER_NOT_FOUND_MSG = 'User not found.'
LOGIN_REQUIRED_MSG = 'You must be logged in to perform this action.'
DANGER_CATEGORY = 'danger'

# ===== FLASK APPLICATION SETUP =====

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Global refresh operation management
refresh_lock = threading.Lock()
refresh_in_progress = False

# Environment-based configuration
if os.getenv('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
else:
    app.config['DEBUG'] = True

# Redis configuration for caching
if not os.getenv('REDIS_URL'):
    os.environ['REDIS_URL'] = 'redis://redis:6379/0'

# ===== AUTHENTICATION DECORATORS =====

def login_required_api(f):
    """
    Decorator for API endpoints requiring authentication.
    Returns JSON error response if user not logged in.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with authentication check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ------------------- ROUTES -------------------

# --- Home route: latest summaries, daily digest ---
@app.route('/', methods=['GET'])
def index():
    print("[index] Called. session:", dict(session))
    if 'user_id' not in session:
        return redirect(url_for('register'))
    user_id = session['user_id']
    
    # Check if this is a fresh login (auto-refresh trigger)
    auto_refresh = session.pop('trigger_auto_refresh', False)
    
    # Get articles grouped by topics
    topics_articles = content_service.get_articles_by_topics(user_id, limit_per_topic=8)

    username = session.get('username')
    current_year = datetime.now().year
    
    return render_template('index.html', 
                         topics_articles=topics_articles, 
                         username=username, 
                         current_year=current_year,
                         auto_refresh=auto_refresh)

# --- Legacy route for backward compatibility ---
@app.route('/index', methods=['GET'])
def discover():
    print("[discover] Called.")
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    print("[forgot_password] Called. session:", dict(session))
    if request.method == 'POST':
        email = request.form['email']
        user = user_service.find_user_by_email(email)
        if not user:
            flash('No account found with that email.', 'danger')
            return render_template('reset_password.html')
        session['reset_email'] = email
        flash('Enter the 6-digit code from your authenticator app and your new password.', 'info')
        return redirect(url_for('reset_password'))
    return render_template('reset_password.html')

# --- Profile Page ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    print("[profile] Called. session:", dict(session))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    username = session.get('username') or ''
    user = user_service.find_user_by_username(username)
    if not user:
        flash(USER_NOT_FOUND_MSG, DANGER_CATEGORY)
        return redirect(url_for('index'))
    if request.method == 'POST':
        new_username = request.form.get('username') or ''
        if new_username and new_username != user.username:
            if user_service.update_user_username(user_id, new_username):
                session['username'] = new_username
                flash('Username updated successfully.', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Failed to update username. Try a different one.', 'danger')
    return render_template('profile.html', current_user=user, username=session.get('username'), current_year=datetime.now().year)

# --- Change Email ---
@app.route('/change_email', methods=['GET', 'POST'])
def change_email():
    print("[change_email] Called. session:", dict(session))
    if 'user_id' not in session:
        print("[change_email] No user_id in session. Redirecting to login.")
        return redirect(url_for('login'))
    user_id = session['user_id']
    user = user_service.find_user_by_id(user_id)
    print(f"[change_email] user_id: {user_id}, user: {user}")
    if not user:
        print("[change_email] User not found. Redirecting to login.")
        flash(USER_NOT_FOUND_MSG, DANGER_CATEGORY)
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_email = request.form.get('new_email', '').strip()
        print(f"[change_email] POST new_email: {new_email}")
        if not new_email:
            print("[change_email] No new_email provided.")
            flash('Please enter a new email.', 'danger')
            return render_template(CHANGE_EMAIL_TEMPLATE)
        if new_email == user.email:
            print("[change_email] New email is same as current email.")
            flash('New email is the same as current email.', 'danger')
            return render_template(CHANGE_EMAIL_TEMPLATE)
        updated = user_service.update_user_email(user_id, new_email)
        print(f"[change_email] update_user_email result: {updated}")
        if updated:
            session['setup_email'] = new_email
            print("[change_email] Email updated. Redirecting to setup_totp.")
            flash('Email updated. Please set up TOTP for your new email.', 'success')
            return redirect(url_for('setup_totp'))
        else:
            print("[change_email] Failed to update email.")
            flash('Failed to update email. Try a different one.', 'danger')
    return render_template(CHANGE_EMAIL_TEMPLATE)

# --- Reset Password API ---
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    print("[reset_password] Called. session:", dict(session))
    if 'verified_email' not in session:
        print("[reset_password] No verified email in session. Redirecting to verify code.")
        flash('Please verify your code first.', 'danger')
        return redirect(url_for('verify_code'))
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        print(f"[reset_password] POST new_password: {'*' * len(new_password)}, confirm_password: {'*' * len(confirm_password)}")
        if not new_password or not confirm_password:
            print("[reset_password] Missing fields.")
            flash('All fields are required.', 'danger')
            return render_template(RESET_PASSWORD_TEMPLATE)
        if new_password != confirm_password:
            print("[reset_password] Passwords do not match.")
            flash('Passwords do not match.', 'danger')
            return render_template(RESET_PASSWORD_TEMPLATE)
        email = session.pop('verified_email', None)
        user = user_service.find_user_by_email(email)
        print(f"[reset_password] user: {user}")
        if not user:
            print("[reset_password] No user found for email.")
            flash('No account found for password reset.', 'danger')
            return render_template(RESET_PASSWORD_TEMPLATE)
        user_service.update_user_password(user.id, new_password)
        print("[reset_password] Password updated. Redirecting to login.")
        flash('Password reset successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template(RESET_PASSWORD_TEMPLATE)

# --- Verify Code Page ---
@app.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    print("[verify_code] Called. session:", dict(session))
    if request.method == 'POST':
        code = request.form.get('auth_code', '').strip()
        print(f"[verify_code] POST code: {code}")
        if not code:
            print("[verify_code] Missing fields.")
            flash('Code is required.', 'danger')
            return render_template('verify_code.html')

        # Fetch user from session or context
        user_id = session.get('user_id')
        if not user_id:
            print("[verify_code] No user in session.")
            flash('Session expired. Please try again.', 'danger')
            return redirect(url_for('login'))

        user = user_service.find_user_by_id(user_id)
        if not user:
            print("[verify_code] No user found for ID.")
            flash('No account found for verification.', 'danger')
            return render_template('verify_code.html')

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code):
            print("[verify_code] Invalid TOTP code.")
            flash('Invalid code. Please try again.', 'danger')
            return render_template('verify_code.html')

        session['verified_email'] = user.email
        print("[verify_code] Code verified. Redirecting to reset password.")
        return redirect(url_for('reset_password'))
    return render_template('verify_code.html')

# --- Reset Username Page ---
@app.route('/reset_username', methods=['GET', 'POST'])
def reset_username():
    print("[reset_username] Called. session:", dict(session))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        new_username = request.form.get('new_username', '').strip()
        password = request.form.get('password', '').strip()

        print(f"[reset_username] POST email: {email}, new_username: {new_username}, password: {'*' * len(password)}")

        if not email or not new_username or not password:
            print("[reset_username] Missing fields.")
            flash('All fields are required.', 'danger')
            return render_template(RESET_USERNAME_TEMPLATE)

        user = user_service.find_user_by_email(email)
        if not user:
            print("[reset_username] No user found for email.")
            flash('No account found with that email.', 'danger')
            return render_template(RESET_USERNAME_TEMPLATE)

        if not user_service.check_password(user, password):
            print("[reset_username] Incorrect password.")
            flash('Incorrect password.', 'danger')
            return render_template(RESET_USERNAME_TEMPLATE)

        if user_service.find_user_by_username(new_username):
            print("[reset_username] Username already taken.")
            flash('Username already taken. Please try a different one.', 'danger')
            return render_template(RESET_USERNAME_TEMPLATE)

        updated = user_service.update_user_username(user.id, new_username)
        print(f"[reset_username] update_user_username result: {updated}")
        if updated:
            print("[reset_username] Username updated successfully.")
            flash('Username updated successfully.', 'success')
            return redirect(url_for('login'))
        else:
            print("[reset_username] Failed to update username.")
            flash('Failed to update username. Please try again.', 'danger')

    return render_template(RESET_USERNAME_TEMPLATE)

# --- Article Interaction Routes for Dashboard Forms ---
@app.route('/mark_read/<int:article_id>', methods=['POST'])
def mark_read(article_id):
    print("[mark_read] Called. session: {} article_id: {}".format(dict(session), article_id))
    if 'user_id' not in session:
        flash(LOGIN_REQUIRED_MSG, DANGER_CATEGORY)
        return redirect(url_for('login'))
    user_id = session['user_id']
    content_service.mark_content_as_read(user_id, article_id, is_read=True)
    flash('Article marked as read', 'success')
    return redirect(url_for('index'))

@app.route('/like_article/<int:article_id>', methods=['POST'])
def like_article(article_id):
    print("[like_article] Called. session: {} article_id: {}".format(dict(session), article_id))
    if 'user_id' not in session:
        flash(LOGIN_REQUIRED_MSG, DANGER_CATEGORY)
        return redirect(url_for('login'))
    user_id = session['user_id']
    content_service.update_content_liked(user_id, article_id, is_liked=True)
    flash('Article saved to favorites', 'success')
    return redirect(url_for('index'))

@app.route('/read_article/<int:article_id>')
def read_article(article_id):
    print("[read_article] Called. session: {} article_id: {}".format(dict(session), article_id))
    if 'user_id' not in session:
        flash(LOGIN_REQUIRED_MSG, DANGER_CATEGORY)
        return redirect(url_for('login'))

    user_id = session['user_id']
    # Mark article as read
    content_service.mark_content_as_read(user_id, article_id, is_read=True)

    # Use robust lookup: fetch article directly by ID
    article = content_service.get_article_by_id(article_id)
    if article and article.get('article_url'):
        return redirect(article['article_url'])
    else:
        flash('Article not found', 'danger')
        return redirect(url_for('index'))


# --- Auth & User Management ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    print("[register] Called. session:", dict(session))
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
    print("[setup_totp] Called. session:", dict(session))
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
    print("[login] Called. session:", dict(session))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        code = request.form.get('code')
        user = user_service.find_user_by_username(username)
        if not user:
            flash('Username not found.', 'danger')
            return render_template(LOGIN_TEMPLATE)
        if not user_service.check_password(user, password):
            flash('Incorrect password.', 'danger')
            return render_template(LOGIN_TEMPLATE)
        if code:
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(code):
                flash('Authentication code is invalid', 'danger')
                return render_template(LOGIN_TEMPLATE)
        session['user_id'] = user.id
        session['username'] = user.username
                # --- Auto-ingestion logic ---
        from src.services import content_service
        import datetime
        last_ingest = content_service.get_last_ingestion_time()
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Ensure last_ingest is timezone-aware if it exists
        if last_ingest is not None and last_ingest.tzinfo is None:
            last_ingest = last_ingest.replace(tzinfo=datetime.timezone.utc)
        
        trigger_refresh = True
        if last_ingest and (now - last_ingest).total_seconds() < 2 * 3600:
            trigger_refresh = False
            
        session['trigger_auto_refresh'] = trigger_refresh
        flash('Welcome back!', 'success')
        return redirect(url_for('index'))
    return render_template(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    print("[logout] Called. session:", dict(session))
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Successfully logged out', 'info')
    return redirect(url_for('index'))

@app.route('/api/sources', methods=['GET'])
@login_required_api
def get_sources():
    print("[get_sources] Called. session:", dict(session))
    sources = source_service.get_all_sources()
    sources_data = []
    for s in sources:
        sources_data.append({
            'id': s.id,
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
    print("[get_digest] Called. session:", dict(session))
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    # Fetch general articles for all users (Only fast section shows personalised articles based on user's interested topics.)
    articles = content_service.get_general_digest(limit=limit, offset=offset)
    return jsonify({'articles': articles}), 200

@app.route('/api/content/<int:content_id>/read', methods=['POST'])
@login_required_api
def mark_content_read_api(content_id):
    print("[mark_content_read_api] Called. session: {} content_id: {}".format(dict(session), content_id))
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
    print("[like_content_api] Called. session: {} content_id: {}".format(dict(session), content_id))
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
    print("[unlike_content_api] Called. session: {} content_id: {}".format(dict(session), content_id))
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
    print("[fast] Called. session:", dict(session))
    # Fast View now uses dynamic loading via JavaScript
    # Start with 0 values, will be updated by frontend as articles are loaded and read
    return render_template(
        'fast.html',
        article=None,
        username=session.get('username'),
        current_year=datetime.now().year,
        articles_read=0,
        total_articles=0
    )
# --- Fast View API for batching where articles are loaded in batches of 10 ---
@app.route('/api/fast_articles', methods=['GET'])
def api_fast_articles():
    print("[api_fast_articles] Called. session:", dict(session))
    if 'user_id' not in session:
        print("[api_fast_articles] No user_id in session - unauthorized")
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    print(f"[api_fast_articles] Processing for user_id: {user_id}")
    
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        print(f"[api_fast_articles] Request params: offset={offset}, limit={limit}, refresh={refresh}")
        
        # Get user's selected topics
        user_topics = user_service.get_user_topics(user_id)
        print(f"[api_fast_articles] User topics: {user_topics}")
        
        # Get articles based on user topics or fallback to general
        if user_topics:
            # Get articles from user topics
            all_articles = content_service.get_articles_by_user_topics_extended(user_id, user_topics, limit=10000, offset=0)
        else:
            # User has no topics selected, get general articles
            all_articles = content_service.get_personalized_digest(user_id, limit=10000, offset=0, include_read=False)
            all_articles = [a for a in all_articles if isinstance(a, dict) and a.get('id')]
        
        # Filter to only unread articles
        all_unread_articles = [a for a in all_articles if not a.get('is_read', False)]
        total_unread = len(all_unread_articles)
        
        # Get the batch for current request
        start_idx = offset
        end_idx = offset + limit
        batch_articles = all_unread_articles[start_idx:end_idx]
        
        # Filter to unread articles only for Fast View (redundant check but for safety)
        unread_articles = [a for a in batch_articles if not a.get('is_read', False)]
        
        # Shuffle articles on first load (offset=0) or when refresh is requested
        if offset == 0 or refresh:
            random.shuffle(unread_articles)
            print("[api_fast_articles] Shuffled articles for fresh experience")
        
        print(f"[api_fast_articles] Found {len(batch_articles)} batch articles, {len(unread_articles)} unread in batch")
        print(f"[api_fast_articles] Total unread articles available: {total_unread}")
        print(f"[api_fast_articles] Returning {len(unread_articles)} articles")
        
        return jsonify({
            'articles': unread_articles,
            'total_unread': total_unread,
            'batch_size': len(unread_articles),
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"[api_fast_articles] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/manage_interests', methods=['GET', 'POST'])
def manage_interests():
    print("[manage_interests] Called. session:", dict(session))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    # List of all available topics (from content_service)
    all_topics = content_service.TOPIC_LABELS
    if request.method == 'POST':
        selected_topics = request.form.getlist('topics')
        # Update user_topics in DB
        user_service.set_user_topics(user_id, selected_topics)
        flash('Your interests have been updated.', 'success')
        return redirect(url_for('manage_interests'))
    # Get user's current topics
    user_topics = user_service.get_user_topics(user_id)
    return render_template('manage_interests.html', all_topics=all_topics, user_topics=user_topics, username=session.get('username'), current_year=datetime.now().year)

# --- Favorites (Liked Content) ---
@app.route('/favorites', methods=['GET'])
def favorites():
    print("[favorites] Called. session:", dict(session))
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
    print("[unlike_article] Called. session: {} article_id: {}".format(dict(session), article_id))
    if 'user_id' not in session:
        flash('You must be logged in to perform this action', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    content_service.update_content_liked(user_id, article_id, is_liked=False)
    flash('Article removed from favorites', 'info')
    return redirect(url_for('index'))

# ------------------- JOB ENDPOINTS FOR RENDER FREE TIER -------------------
@app.route('/api/jobs/ingest', methods=['POST'])
def trigger_ingest_job():
    """
    Trigger article ingestion job via HTTP endpoint.
    This works better than background scheduling on Render free tier.
    Includes concurrency protection to prevent multiple simultaneous refreshes.
    """
    global refresh_in_progress
    
    # Check if refresh is already in progress
    if refresh_in_progress:
        return jsonify({
            'success': False,
            'error': 'Refresh already in progress. Please wait for it to complete.',
            'timestamp': datetime.now().isoformat()
        }), 429  # Too Many Requests
    
    # Try to acquire lock with timeout
    if not refresh_lock.acquire(blocking=False):
        return jsonify({
            'success': False,
            'error': 'Another refresh operation is currently running. Please try again in a moment.',
            'timestamp': datetime.now().isoformat()
        }), 429
    
    try:
        refresh_in_progress = True
        # Import and run the ingestion job directly
        from src.jobs.web_jobs import run_ingest_articles
        result = run_ingest_articles()
        
        if result.get('success'):
            # Update last ingestion time on successful ingestion
            content_service.update_last_ingestion_time()
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
    finally:
        refresh_in_progress = False
        refresh_lock.release()

@app.route('/api/jobs/cleanup', methods=['POST'])
def trigger_cleanup_job():
    """
    Trigger cleanup job via HTTP endpoint.
    This works better than background scheduling on Render free tier.
    """
    try:
        from src.jobs.web_jobs import run_cleanup
        result = run_cleanup()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/jobs/status', methods=['GET'])
def job_status():
    """
    Get information about when jobs were last run and current refresh status.
    Useful for monitoring on free tier.
    """
    global refresh_in_progress
    
    try:
        # Get some basic stats about content freshness
        stats = content_service.get_content_stats()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'refresh_in_progress': refresh_in_progress,
            'message': 'Refresh is currently running' if refresh_in_progress else 'Job status retrieved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'refresh_in_progress': refresh_in_progress,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/favorites', methods=['GET'])
@login_required_api
def get_favorites_api():
    """API endpoint to get user's favorite articles"""
    print("[get_favorites_api] Called. session:", dict(session))
    try:
        user_id = session['user_id']
        articles = content_service.get_personalized_digest(user_id, limit=100, include_read=True)
        liked_articles = [a for a in articles if a.get('is_liked')]
        return jsonify(liked_articles), 200
    except Exception as e:
        print(f"Error in get_favorites_api: {e}")
        return jsonify({'error': 'Failed to get favorites'}), 500

# ------------------- HEALTH CHECK -------------------
@app.route('/health')
@app.route('/healthz')
def health_check():
    """Simple health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'TechPulse'
    }), 200

# ------------------- MAIN -------------------
if __name__ == '__main__':
    app.run(debug=True)