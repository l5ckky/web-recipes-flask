from flask import Flask, render_template, request, redirect, url_for, flash
from .forms import RecipeForm, RegistrationForm, LoginForm
from .models import Recipe, db, User  # Импортируем модель User
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user  #Импортируем flask-login

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager() # Инициализация LoginManager
login_manager.init_app(app)
login_manager.login_view = 'login'  # Функция для перенаправления неавторизованных пользователей
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Загружает пользователя по ID для Flask-Login."""
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)  # Логиним пользователя
            next_page = request.args.get('next')
            flash('You have been logged in!', 'success')
            return redirect(next_page or url_for('recipes'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required  # Требует авторизации для доступа
def logout():
    logout_user()  # Разлогиниваем пользователя
    return redirect(url_for('recipes'))


@app.route('/')
@app.route('/recipes')
def recipes():
    recipe_list = Recipe.query.all()
    return render_template('recipes.html', recipes=recipe_list)


@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required #Only logged in user can add recipes
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(title=form.title.data, description=form.description.data, instructions=form.instructions.data)
        db.session.add(recipe)
        db.session.commit()
        return redirect(url_for('recipes'))
    return render_template('new_recipe.html', title='New Recipe', form=form)

if __name__ == '__main__':
    app.run(debug=True)