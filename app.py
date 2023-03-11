from flask import Flask, render_template, request, abort,g, redirect,url_for
from queries import Queries
from models import db, User
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///product.db'
app.config["SECRET_KEY"] = "samuelandmercyproject"
db.init_app(app)
queries = Queries(db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))
  
@app.before_request
def before_request():
  g.user = current_user


def validate_email(self,email):
  existing_email= User.query.filter_by(email = email.data).first()
  
  if existing_email:
    raise ValidationError("That email already exists. please choose a different one.")

class LoginForm(FlaskForm):  

  email = EmailField(validators = [InputRequired()])

  password = PasswordField(validators = [InputRequired(),Length(min=4,max=20)])

  submit = SubmitField("Login")

@app.get("/")
def index():
  params = {
        "query": request.values.get("query"),
        "time_taken": request.values.getlist("time_taken"),
        "ingredient": request.values.getlist("ingredient")
    }
  products = queries.search_recipes(params)
  return render_template("index.html", products=products, params=params)
  
@app.get("/sign_up")  
def sign_up():
  return render_template("signup.html")


@app.post("/form")
def handle_submit():
  # Get the form data
  name = request.form["name"]
  email = request.form["email"]
  password = request.form["password"]
  re_password = request.form["re_password"]
  try:
    validate_email(email)
  except ValidationError :
    error = "That email already exists. please choose a different one."
    return render_template('signup.html',error = error)
  # Validate the form data
  errors = {}
  if password != re_password:
      errors["password"] = "Passwords did not match"
  
  if errors:
      # Return the form with errors
      return render_template("signup.html", errors=errors)

  # Insert the data into the database
  if queries.create_new_user(name,email,password):
    user_email = User.query.filter_by(email=email).first()
    login_user(user_email)
  

  # Redirect the user to a confirmation page
  return redirect("/dashboard")

@app.route('/login',methods=['GET','POST'])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data).first()
    if user:
      if queries.validate_password(form.email.data,form.password.data):
        login_user(user)
        return redirect(url_for(dashboard))
  if request.method =='POST':
    if current_user.is_authenticated:
      return redirect(url_for('dashboard'))
    
    # email = request.form['email']
    # password = request.form['password']
    # user_email = User.query.filter_by(email=email).first()
    # if user_email: 
    #   if queries.validate_password(email,password):
    #     login_user(user_email)
    #     return redirect(url_for('dashboard'))
    # error = "Incorrect User email or password"
    # return render_template('login.html',error = error)
  return render_template("login.html", form = form)

@app.get("/recipe/<recipe_id>")
@login_required
def show_product(recipe_id):
    product = queries.select_product_with_details(recipe_id)
    if not product:
        abort(404, "No product with that id")
    return render_template("recipe.html", product=product)

@app.route("/dashboard", methods = ['GET','POST'])
@login_required
def dashboard():
  if not g.user:
    return redirect(url_for('login'))
  
  return render_template("profile.html")
  

@app.route("/logout", methods = ['GET','POST'])
@login_required
def logout():
  logout_user()
  return redirect(url_for('login'))

app.run(host='0.0.0.0', port=81)

