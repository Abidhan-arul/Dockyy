from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, current_app, session
from werkzeug.utils import secure_filename
import os
from . import db
from .models import Submission

main = Blueprint('main', __name__)

USERS = {
    'admin123': 'adminpass',
    'user001': 'userpass',
    'user002': 'userpass2'
}

@main.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login_id = request.form.get('login_id')
        password = request.form.get('password')
        role = request.form.get('role')

        if not login_id or not password:
            error = "Login ID and Password are required."
        elif role == "admin" and login_id == "admin123" and USERS[login_id] == password:
            session['username'] = login_id
            session['role'] = 'admin'
            return redirect(url_for('main.admin_dashboard'))
        elif role == "user":
            from .models import User
            user = User.query.filter_by(username=login_id, role='user').first()
            if user and user.password == password:
                session['username'] = login_id
                session['role'] = 'user'
                return redirect(url_for('main.user_dashboard'))
            else:
                error = "Invalid credentials."
        else:
            error = "Unauthorized role for this user."
    return render_template('login.html', error=error)

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/user')
def user_dashboard():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('main.login'))
    from .models import Submission
    submissions = Submission.query.filter_by(name=session['username']).order_by(Submission.timestamp.desc()).all()
    return render_template('user.html', submissions=submissions, username=session['username'])

@main.route('/submit', methods=['POST'])
def submit():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('main.login'))
    name = session['username']
    file = request.files['document']
    if file:
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        path = os.path.join(upload_folder, filename)
        file.save(path)
        submission = Submission(name=name, filename=filename)
        db.session.add(submission)
        db.session.commit()
    return redirect(url_for('main.user_dashboard'))

@main.route('/admin')
def admin_dashboard():
    submissions = Submission.query.order_by(Submission.timestamp.desc()).all()
    return render_template('admin.html', submissions=submissions)

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
    return send_from_directory(upload_folder, filename)

@main.route('/delete/<int:submission_id>', methods=['POST'])
def delete_submission(submission_id):
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('main.login'))
    from .models import Submission
    submission = Submission.query.get_or_404(submission_id)
    if submission.name != session['username']:
        return redirect(url_for('main.user_dashboard'))
    # Delete file from uploads
    upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
    file_path = os.path.join(upload_folder, submission.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(submission)
    db.session.commit()
    return redirect(url_for('main.user_dashboard'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error = 'Username and password are required.'
        else:
            from .models import User
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = 'Username already exists.'
            else:
                user = User(username=username, password=password, role='user')
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('main.login'))
    return render_template('register.html', error=error)

