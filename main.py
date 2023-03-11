from flask import Flask, render_template, flash, request, abort, g, redirect, url_for, jsonify
from queries import Queries
from models import db, User, Recipe, Image
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from forms import LoginForm, SignupForm, NewRecipeForm, ImageForm
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
import os
from sqlalchemy import or_

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///recipes.db'
app.config["SECRET_KEY"] = "samuelandmercyproject"
app.config['UPLOAD_FOLDER'] = 'static/images'

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


@app.get("/")
def index():
  params = {
    "query": request.values.get("query"),
    "time_taken": request.values.getlist("time_taken"),
    "ingredient": request.values.getlist("ingredient")
  }
  products = queries.search_recipes(params)
  return render_template("index.html", products=products, params=params)


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


@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data).first()
    if user:
      if queries.validate_password(form.email.data, form.password.data):
        login_user(user)
        return redirect(url_for('dashboard'))
      else:
        error = "invalid password / user"
    else:
      error = "invalid password / user"

  

  return render_template("login.html", form=form, error=error)


@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
  if not g.user:
    return redirect(url_for('login'))

  return render_template("dashboard.html")


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

    # create new recipe
    recipe = Recipe(name=recipe_name,
                    instructions=instructions,  
                    time_taken=time_taken,
                    uploaded_by=g.user)
    db.session.add(recipe)
    try:
        db.session.commit()  # commit changes to the database
        flash('Your recipe has been updated successfully!', 'success')
        return redirect(url_for('show_recipe', recipe_id=recipe.id))
    except IntegrityError:
        db.session.rollback()
        error ="Recipe name must be unique. Please choose a different name.','error'"
        

    # handle image upload
    if image_form.validate_on_submit() and image_form.image.data:
      # create FileStorage object from uploaded file
      filestorage = FileStorage(stream=image_form.image.data.stream,
                                filename=image_form.image.data.filename)

      # save image to disk
      filename = secure_filename(filestorage.filename)
      filestorage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

      # create new image object and associate with recipe
      image = Image(url=filename, recipe_id=recipe.id)
      db.session.add(image)  
      db.session.commit()  # commit changes to the database
        
    else:
      return jsonify(image_form.errors)
      flash('No image selected.', 'danger')

    flash('Your recipe has been uploaded successfully!', 'success')
    return redirect(url_for('dashboard'))

  return render_template('upload_new_recipes.html',
                         form=form,
                         image_form=image_form,error=error)


@app.route('/recipe/edit/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
  print(request.method)
  recipe = Recipe.query.get_or_404(recipe_id)
  form = NewRecipeForm(request.form, obj=recipe)
  image_form = ImageForm()

  # fetch the existing image object associated with the recipe
  image = Image.query.filter_by(recipe_id=recipe.id).first()

  if request.method == 'POST' and form.validate():
    form.populate_obj(recipe)  # update the recipe object with the form data

    # handle image upload
    if image_form.validate_on_submit() and image_form.image.data:
      # create FileStorage object from uploaded file
      filestorage = FileStorage(stream=image_form.image.data.stream,
                                filename=image_form.image.data.filename)

      # save image to disk
      filename = secure_filename(filestorage.filename)
      filestorage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

      if image:
        # if an image object already exists, update the url property
        image.url = filename
      else:
        # if an image object does not exist, create a new object
        image = Image(url=filename, recipe_id=recipe.id)
        db.session.add(image)

      flash('Image uploaded successfully.', 'success')

    else:
      flash('No image selected.', 'danger')

    try:
      db.session.commit()  # commit changes to the database
      flash('Your recipe has been updated successfully!', 'success')
      return redirect(url_for('show_recipe', recipe_id=recipe.id))
    except IntegrityError:
      db.session.rollback()
      error = "'Recipe name must be unique. Please choose a different name.error'"
      return render_template('edit.html',
                         form=form,
                         image_form=image_form,
                         recipe=recipe,
                         is_update=True,error = error)

    return redirect(url_for('my_recipes'))
  return render_template('edit.html',
                         form=form,
                         image_form=image_form,
                         recipe=recipe,
                         is_update=True)


@app.route('/recipe/delete/<int:recipe_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def delete_recipe(recipe_id):
  recipe = Recipe.query.get_or_404(recipe_id)
  # fetch the existing image object associated with the recipe
  image = Image.query.filter_by(recipe_id=recipe.id).first()
  if request.method == 'POST':
    db.session.delete(recipe)  # delete the recipe object
    if image:
      db.session.delete(image)  # delete the associated image object
    db.session.commit()  # commit changes to the database
    flash('Your recipe has been deleted successfully!', 'success')

  return redirect(url_for('dashboard'))


@app.route('/search')
def search():
  search_term = request.args.get('q')
  recipes = Recipe.query.filter(
    or_(Recipe.name.like(f'%{search_term}%'),
        Recipe.user_id.like(f'%{search_term}%'))).all()
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


app.run(host='0.0.0.0', port=81)
