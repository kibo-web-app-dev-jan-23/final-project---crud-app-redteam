from flask import Flask, render_template, flash, request, abort, g, redirect, url_for, jsonify,send_from_directory
from queries import Queries
from models import db, User, Recipe, Image, Ingredient
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from forms import LoginForm, SignupForm, NewRecipeForm, ImageForm
from flask_uploads import UploadSet,IMAGES, configure_uploads
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
import os
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///recipes.db'
app.config["SECRET_KEY"] = "samuelandmercyproject"
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(os.getcwd(), 'static', 'images')
photos = UploadSet('photos', IMAGES)
configure_uploads(app,photos)

db.init_app(app)
queries = Queries(db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.before_request
def before_request():
    g.user = current_user


def log_report(report):
    with open("report.txt", 'a', encoding='utf-8') as f:
        f.write(f'{report}\n')


@app.get("/")
def index():
    return render_template("index.html")


def create_new_user(name, email, password):
    queries.create_new_user(name, email, password)
    user = User.query.filter_by(email=email).first()
    if user:
        login_user(user)
    else:
        error = "unsuccesful"
    return redirect(url_for('dashboard'))


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    form = SignupForm()
    error = None

    if form.validate_on_submit():
        create_new_user(form.name.data, form.email.data, form.password.data)

    return render_template("signup.html", form=form, error=error)


def validate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if user and queries.validate_password(email, password):
        login_user(user)
        return True
    else:
        return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm()
    if form.validate_on_submit():
        if validate_user(form.email.data, form.password.data):
            return redirect(url_for('dashboard'))
        else:
            error = "invalid password / user"

    return render_template("login.html", form=form, error=error)


@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    if not g.user:
        return redirect(url_for('login'))

    return render_template("dashboard.html")


def get_user_recipes(user_id):
    return db.session.query(Recipe).join(User).filter(User.id == user_id).all()


@app.route("/my_recipes", methods=['POST', 'GET'])
@login_required
def my_recipes():
    recipes = get_user_recipes(g.user.id)
    return render_template("my_recipes.html", recipes=recipes)


def get_recipe(recipe_id):
    return db.session.query(Recipe).filter_by(id=recipe_id).first()


def extract_ingredients(ingredients_str):
    """Takes a string of comma-separated ingredients and returns a list of ingredient names"""
    ingredients_list = ingredients_str.strip().split(",")
    return [item.strip().split(" ")[-1] for item in ingredients_list]


def create_recipe(recipe_name, instructions, time_taken, uploaded_by, ingredients):
    """Creates a new Recipe object and adds it to the database"""
    recipe = Recipe(name=recipe_name,
                    instructions=instructions,
                    time_taken=time_taken,
                    uploaded_by=uploaded_by)
    db.session.add(recipe)
    for ingredient in ingredients:
        ingredient_obj = Ingredient.query.filter_by(name=ingredient).first()
        if not ingredient_obj:
            ingredient_obj = Ingredient(name=ingredient)
        recipe.ingredients.append(ingredient_obj)
    db.session.commit()
    return recipe


def generate_unique_filename(filename):
    """Generates a unique filename by appending a timestamp to the original filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    root, ext = os.path.splitext(filename)
    return f"{root}_{timestamp}{ext}"


def upload_recipe_image(recipe_id, image):
    """Creates a new Image object for the given recipe and adds it to the database"""
    filename = generate_unique_filename(image.filename)
    photos.save(image, name=filename)
    file_url = url_for('get_file', filename=filename)
    image = Image(url=file_url, recipe_id=recipe_id)
    db.session.add(image)
    db.session.commit()


@app.route("/upload_recipes", methods=['GET', 'POST'])
@login_required
def upload_recipes():
    error = None
    form = NewRecipeForm()
    image_form = ImageForm()

    if form.validate_on_submit():
        recipe_name = form.name.data
        instructions = form.instructions.data
        time_taken = form.time_taken.data
        uploaded_by = g.user.id
        ingredients_str = form.ingredients.data
        ingredients = extract_ingredients(ingredients_str)
        recipe = create_recipe(recipe_name, instructions, time_taken, uploaded_by, ingredients)

        if image_form.image.data:
            upload_recipe_image(recipe.id, image_form.image.data)

        flash("Recipe uploaded successfully.")
        return redirect(url_for('my_recipes'))

    return render_template("upload_recipe.html", form=form, image_form=image_form, error=error)



@app.route("/recipe/<int:recipe_id>", methods=['GET'])
def show_recipe(recipe_id):
    recipe = get_recipe(recipe_id)
    if not recipe:
        abort(404)
    return render_template("recipe.html", recipe=recipe)


@app.route("/recipe/<int:recipe_id>/edit", methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
    recipe = get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe.uploaded_by != g.user.id:
        abort(403)

    form = NewRecipeForm(obj=recipe)
    image_form = ImageForm()

    if form.validate_on_submit():
        form.populate_obj(recipe)
        recipe.ingredients = []
        ingredients_str = form.ingredients.data
        ingredients = extract_ingredients(ingredients_str)
        for ingredient in ingredients:
            ingredient_obj = Ingredient.query.filter_by(name=ingredient).first()
            if not ingredient_obj:
                ingredient_obj = Ingredient(name=ingredient)
            recipe.ingredients.append(ingredient_obj)
        db.session.commit()

        if image_form.image.data:
            upload_recipe_image(recipe.id, image_form.image.data)

        flash("Recipe updated successfully!")
        return redirect(url_for('view_recipe', recipe_id=recipe.id))

    return render_template("edit.html", recipe=recipe, form=form, image_form=image_form)


@app.route("/recipe/<int:recipe_id>/delete", methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe.uploaded_by != g.user.id:
        abort(403)

    db.session.delete(recipe)
    db.session.commit()

    flash("Recipe deleted successfully!")
    return redirect(url_for('my_recipes'))

@app.route('/search')
def search():
  search_term = request.args.get('q')
  # recipes = select(Recipe)
  recipes = Recipe.query.join(Recipe.uploaded_by)\
            .filter(or_(Recipe.name.like(f'%{search_term}%'),
                        User.name.like(f'%{search_term}%')))\
            .options(selectinload(Recipe.images)).all()
  for recipe in recipes:
    log_report(recipe.images)
  # recipes = recipes.selectinload
  return render_template('search.html', recipes=recipes)


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
  logout_user()
  g.user = None
  return redirect(url_for('index'))


@app.route("/about", methods=['GET'])
def about():
  return render_template("about.html")