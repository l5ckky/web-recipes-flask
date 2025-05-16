from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import requests
import json
from bs4 import BeautifulSoup
from time import sleep
import api
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    avatar = db.Column(db.String(120), nullable=True)  # Добавляем поле для хранения пути к аватару

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

available_ingredients = [{'category': 'Овощи',
                         'ingredients': [
                             ('Картофель', 'Картошка'),
                             'Морковь',
                             'Лук',
                             'Помидоры',
                             'Огурцы',
                             'Баклажаны',
                         ]},
                         {'category': 'Мясо и птица',
                          'ingredients': [
                              'Курица',
                              'Говядина',
                              'Свинина',
                              'Баранина',
                          ]},
                         {'category': 'Рыба',
                          'ingredients': [
                              'weg',
                              'Мrjtyrtyорковь',
                              'Лwhtук',
                              'Помиherдоры',
                          ]},
                         {'category': 'Молочные продукты',
                          'ingredients': [
                              'Молоко',
                              'Сыр',
                              'Творог',
                              'Йогурт'
                          ]},
                         {'category': 'Фрукты и ягоды',
                          'ingredients': [
                              'Яблоки',
                              'Бананы',
                              'Мандарины',
                              'Апельсины',
                              'Вишня',
                              'Виноград',
                          ]},
                         {'category': 'ауауц',
                          'ingredients': [
                              ('Картацауццофель', 'Картошка'),
                              'цуп',
                              'Лупкупкук',
                              'Помипккпкдоры',
                              'к',
                              'Бакпкпйлажаны',
                          ]},
                         ]

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', ingredients=available_ingredients)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Проверка загруженного файла
        avatar = None
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{username}_{file.filename}")
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                avatar = filename

        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, email=email, password=hashed_password, avatar=avatar)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Это имя пользователя или email уже заняты', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
# @login_required
def search():
    if request.method == 'POST':
        data = list(filter(lambda x: x[0], request.values.listvalues()))
        if len(data) > 0:
            ingredients = data[0]
        else:
            ingredients = []

        response = api.scrape_recipes(ingredients)
        return render_template('index.html',
                               recipes=response['recipes'],
                               msg=response['msg'],
                               ingredients=available_ingredients)
    elif request.method == 'GET':
        return "error"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=8080, host='127.0.0.1', debug=True)