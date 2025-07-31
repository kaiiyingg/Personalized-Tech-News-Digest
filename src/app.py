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
    print("[index] Called. session:", dict(session))
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
            return render_template('forgot_password.html')
        session['reset_email'] = email
        flash('Enter the 6-digit code from your authenticator app and your new password.', 'info')
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html')

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
        flash('User not found.', 'danger')
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
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_email = request.form.get('new_email', '').strip()
        print(f"[change_email] POST new_email: {new_email}")
        if not new_email:
            print("[change_email] No new_email provided.")
            flash('Please enter a new email.', 'danger')
            return render_template('change_email.html')
        if new_email == user.email:
            print("[change_email] New email is same as current email.")
            flash('New email is the same as current email.', 'danger')
            return render_template('change_email.html')
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
    return render_template('change_email.html')

# --- Reset Password API ---
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    print("[reset_password] Called. session:", dict(session))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password', '').strip()
        print(f"[reset_password] POST email: {email}, code: {code}, new_password: {'*' * len(new_password)}")
        if not email or not code or not new_password:
            print("[reset_password] Missing fields.")
            flash('All fields are required.', 'danger')
            return render_template('reset_password.html')
        user = user_service.find_user_by_email(email)
        print(f"[reset_password] user: {user}")
        if not user:
            print("[reset_password] No user found for email.")
            flash('No account found for password reset.', 'danger')
            return render_template('reset_password.html')
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code):
            print("[reset_password] Invalid TOTP code.")
            flash('Invalid code. Please try again.', 'danger')
            return render_template('reset_password.html')
        user_service.update_user_password(user.id, new_password)
        print("[reset_password] Password updated. Redirecting to login.")
        flash('Password reset successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

# --- Reset Username Page ---
@app.route('/reset_username', methods=['GET', 'POST'])
def reset_username():
    print("[reset_username] Called. session:", dict(session))
    if 'user_id' not in session:
        print("[reset_username] No user_id in session. Redirecting to login.")
        flash('You must be logged in to change your username.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    user = user_service.find_user_by_id(user_id)
    print(f"[reset_username] user_id: {user_id}, user: {user}")
    if not user:
        print("[reset_username] User not found. Redirecting to login.")
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_username = request.form.get('new_username', '').strip()
        password = request.form.get('password', '').strip()
        print(f"[reset_username] POST new_username: {new_username}, password: {'*' * len(password)}")
        if not user_service.check_password(user, password):
            print("[reset_username] Incorrect password.")
            flash('Incorrect password.', 'danger')
            return render_template('reset_username.html')
        if not new_username or new_username == user.username:
            print("[reset_username] Invalid or same username.")
            flash('Please enter a new username.', 'danger')
            return render_template('reset_username.html')
        if user_service.find_user_by_username(new_username):
            print("[reset_username] Username already taken.")
            flash('Username already taken.', 'danger')
            return render_template('reset_username.html')
        updated = user_service.update_user_username(user_id, new_username)
        print(f"[reset_username] update_user_username result: {updated}")
        if updated:
            session['username'] = new_username
            print("[reset_username] Username updated. Redirecting to profile.")
            flash('Username updated successfully.', 'success')
            return redirect(url_for('profile'))
        else:
            print("[reset_username] Failed to update username.")
            flash('Failed to update username. Try again.', 'danger')
            return render_template('reset_username.html')
    return render_template('reset_username.html')

# --- Article Interaction Routes for Dashboard Forms ---
@app.route('/mark_read/<int:article_id>', methods=['POST'])
def mark_read(article_id):
    print(f"[mark_read] Called. session: {{}} article_id: {{}}".format(dict(session), article_id))
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    content_service.mark_content_as_read(user_id, article_id, is_read=True)
    flash('Article marked as read', 'success')
    return redirect(url_for('index'))

@app.route('/like_article/<int:article_id>', methods=['POST'])
def like_article(article_id):
    print(f"[like_article] Called. session: {{}} article_id: {{}}".format(dict(session), article_id))
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
        return redirect(url_for('login'))
    user_id = session['user_id']
    content_service.update_content_liked(user_id, article_id, is_liked=True)
    flash('Article saved to favorites', 'success')
    return redirect(url_for('index'))

@app.route('/read_article/<int:article_id>')
def read_article(article_id):
    print(f"[read_article] Called. session: {{}} article_id: {{}}".format(dict(session), article_id))
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'danger')
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
            return render_template('login.html')
        if not user_service.check_password(user, password):
            flash('Incorrect password.', 'danger')
            return render_template('login.html')
        if code:
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(code):
                flash('Authentication code is invalid', 'danger')
                return render_template('login.html')
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Welcome back!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')

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
    user_id = session['user_id']
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
    print(f"[mark_content_read_api] Called. session: {{}} content_id: {{}}".format(dict(session), content_id))
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
    print(f"[like_content_api] Called. session: {{}} content_id: {{}}".format(dict(session), content_id))
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
    print(f"[unlike_content_api] Called. session: {{}} content_id: {{}}".format(dict(session), content_id))
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
    user_id = session['user_id']
    # Get user's selected topics
    user_topics = user_service.get_user_topics(user_id)
    # Get articles matching user's topics
    articles = content_service.get_articles_by_user_topics(user_id, user_topics, limit=100)
    total_articles = len(articles)
    articles_read = sum(1 for a in articles if a.get('is_read', False))
    unread_articles = [a for a in articles if not a.get('is_read', False)]
    article = unread_articles[0] if unread_articles else None
    return render_template(
        'fast.html',
        article=article,
        username=session.get('username'),
        current_year=datetime.now().year,
        articles_read=articles_read,
        total_articles=total_articles
    )
# --- Fast View API for batching where articles are loaded in batches of 10 ---
@app.route('/api/fast_articles', methods=['GET'])
def api_fast_articles():
    print("[api_fast_articles] Called. session:", dict(session))
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    user_topics = user_service.get_user_topics(user_id)
    # If ?all=1, fetch all relevant articles (no batching)
    if request.args.get('all') == '1':
        articles = content_service.get_articles_by_user_topics(user_id, user_topics, limit=1000, offset=0)  # large limit
        # Shuffle articles to mix topics
        random.shuffle(articles)
        return jsonify({'articles': articles}), 200
    else:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        articles = content_service.get_articles_by_user_topics(user_id, user_topics, limit=limit, offset=offset)
        return jsonify({'articles': articles}), 200

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
    print(f"[unlike_article] Called. session: {{}} article_id: {{}}".format(dict(session), article_id))
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