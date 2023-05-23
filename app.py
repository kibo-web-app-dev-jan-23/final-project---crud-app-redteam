from flask import Flask, render_template, flash, request, abort, g, redirect, url_for, jsonify,send_from_directory
from queries import Queries
from models import db, User, Recipe, Image,Ingredient
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

# path = os.getcwd()
# app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///recipes.db'
# app.config["SECRET_KEY"] = "samuelandmercyproject"
# app.config['UPLOADED_PHOTOS_DEST'] = f'{path}/static/images'
# photos = UploadSet('photos', IMAGES)
# configure_uploads(app,photos)

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
  # f= open("report.txt",'a',encoding = 'utf-8')
  # f.write(f'{report}\n')
  # f.close
  with open("report.txt", 'a', encoding='utf-8') as f:
        f.write(f'{report}\n')

@app.get("/")
def index():
  return render_template("index.html")


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
  form = SignupForm()
  error = None

  if form.validate_on_submit():
    queries.create_new_user(form.name.data, form.email.data,
                            form.password.data)
    user = User.query.filter_by(email=form.email.data).first()
    if user:
      login_user(user)
    else:
      error = "unsuccesful"
    return redirect(url_for('dashboard'))
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

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#   error = None
#   form = LoginForm()
#   if form.validate_on_submit():
#     user = User.query.filter_by(email=form.email.data).first()
#     if user:
#       if queries.validate_password(form.email.data, form.password.data):
#         login_user(user)
#         return redirect(url_for('dashboard'))
#       else:
#         error = "invalid password / user"
#     else:
#       error = "invalid password / user"
#   return render_template("login.html", form=form, error=error)


@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
  if not g.user:
    return redirect(url_for('login'))
  last_12_entries = Recipe.query.order_by(Recipe.id.desc()).limit(12).all()
  log_report(last_12_entries)
  return render_template("dashboard.html",recipes = last_12_entries)


@app.route("/my_recipes", methods=['POST', 'GET'])
@login_required
def my_recipes():
  recipes = db.session.query(Recipe).join(User).filter(
    User.id == g.user.id).all()
  return render_template("my_recipes.html", recipes=recipes)


@app.route("/recipe/<recipe_id>", methods=['POST', 'GET'])
@login_required
def show_recipe(recipe_id):
  recipe_id = int(recipe_id)
  recipe = db.session.query(Recipe).filter_by(id=recipe_id).first()
  recipe_list = recipe.instructions.split(".")
  if not recipe:
    abort(404, "No product with that id")
  return render_template("recipe.html", recipe=recipe, recipe_list=recipe_list)

@app.route('/uploads/<filename>')
def get_file(filename):
  return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'],filename)


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
        uploaded_by = g.user
        ingredients_list = extract_ingredients(form.ingredients.data)
        try:
            recipe = create_recipe(recipe_name, instructions, time_taken, uploaded_by, ingredients_list)
        except IntegrityError:
            db.session.rollback()
            error = "Recipe name must be unique. Please choose a different name."
            return render_template('upload_new_recipes.html', form=form, image_form=image_form, error=error)

        if image_form.validate_on_submit():
            upload_recipe_image(recipe.id, image_form.image.data)
            flash('Your recipe has been uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            report = "Validation failed"
            log_report(report)

    return render_template('upload_new_recipes.html', form=form, image_form=image_form, error=error)



@app.route('/image/<recipe_id>')
def get_image(recipe_id):
  image = db.session.query(Image).filter(recipe_id== recipe_id).first()
  return image


def edit_recipe(recipe, form):
    recipe.name = form.name.data
    recipe.instructions = form.instructions.data
    recipe.time_taken = form.time_taken.data
    recipe.ingredients = extract_ingredients(form.ingredients.data)

    db.session.add(recipe)
    db.session.commit()

def update_recipe_and_ingredients(recipe, ingredients):
    """
    Updates a recipe and its associated ingredients.
    """
    # update the recipe
    db.session.add(recipe)

    # remove existing ingredients
    recipe.ingredients.clear()

    # add the new ingredients
    for ingredient_name in ingredients:
        ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
        if not ingredient:
            ingredient = Ingredient(name=ingredient_name)
        recipe.ingredients.append(ingredient)

    db.session.commit()


def get_recipe(recipe_id):
    return db.session.query(Recipe).filter_by(id=recipe_id).first()

@app.route('/recipe/edit/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):

  recipe = get_recipe(recipe_id)
  if not recipe:
      abort(404)
  # if recipe.uploaded_by != current_user:
  #     abort(403)

  form = NewRecipeForm(obj=recipe)
  image_form = ImageForm()
  # recipe = Recipe.query.get_or_404(recipe_id)
  # form = NewRecipeForm(request.form, obj=recipe)
  # image = Image.query.filter_by(recipe_id=recipe.id).first()
  # image_form = ImageForm(request.form, obj=image)

  if request.method == 'POST' and form.validate():
    form.populate_obj(recipe)  # update the recipe object with the form data

    # extract ingredients from form data
    ingredients = extract_ingredients(form.ingredients.data)

    # update the recipe and ingredients
    try:
      update_recipe_and_ingredients(recipe, ingredients)
      flash('Your recipe has been updated successfully!', 'success')
    except IntegrityError:
      db.session.rollback()
      error = "Recipe name must be unique. Please choose a different name."
      return render_template('edit.html',form=form,image_form=image_form,recipe=recipe,is_update=True,error=error)

    # handle image upload
    if image_form.validate_on_submit() and image_form.image.data:
      upload_recipe_image(image_form, recipe)

    # redirect to the updated recipe
    return redirect(url_for('show_recipe', recipe_id=recipe.id))

  return render_template('edit.html',form=form,image_form=image_form,recipe=recipe,is_update=True)

# @app.route('/recipe/edit/<int:recipe_id>', methods=['GET', 'POST'])
# @login_required
# def update_recipe(recipe_id):
#   recipe = Recipe.query.get_or_404(recipe_id)
#   form = NewRecipeForm(request.form, obj=recipe)
#   image = Image.query.filter_by(recipe_id=recipe.id).first()
#   image_form = ImageForm(request.form,obj=image)

#   # fetch the existing image object associated with the recipe
#   # image = Image.query.filter_by(recipe_id=recipe.id).first()

#   if request.method == 'POST' and form.validate():
#     form.populate_obj(recipe)  # update the recipe object with the form data

#     # handle image upload
#     if image_form.validate_on_submit() and image_form.image.data:
#       # create FileStorage object from uploaded file
#       filestorage = FileStorage(stream=image_form.image.data.stream,
#                                 filename=image_form.image.data.filename)

#       # save image to disk
#       filename = secure_filename(filestorage.filename)
#       filestorage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

#       if image:
#         # if an image object already exists, update the url property
#         image.url = filename
#       else:
#         # if an image object does not exist, create a new object
#         image = Image(url=filename, recipe_id=recipe.id)
#         db.session.add(image)

#       flash('Image uploaded successfully.', 'success')

#     else:
#       flash('No image selected.', 'danger')

#     try:
#       db.session.commit()  # commit changes to the database
#       flash('Your recipe has been updated successfully!', 'success')
#       return redirect(url_for('show_recipe', recipe_id=recipe.id))
#     except IntegrityError:
#       db.session.rollback()
#       error = "'Recipe name must be unique. Please choose a different name.error'"
#       return render_template('edit.html',
#                          form=form,
#                          image_form=image_form,
#                          recipe=recipe,
#                          is_update=True,error = error)

#     # return redirect(url_for('my_recipes'))
#   return render_template('edit.html',
#                          form=form,
#                          image_form=image_form,
#                          recipe=recipe,
#                          is_update=True)


@app.route('/recipe/delete/<int:recipe_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def delete_recipe(recipe_id):
  recipe = get_recipe(recipe_id)
  if not recipe:
      abort(404)
  if recipe.uploaded_by != current_user:
      abort(403)
  image = Image.query.filter_by(recipe_id=recipe.id).first()
  if request.method == 'POST':
    db.session.delete(recipe)  # delete the recipe object
    if image:
      db.session.delete(image)  # delete the associated image object
    db.session.commit()  # commit changes to the database
    flash('Your recipe has been deleted successfully!', 'success')

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
