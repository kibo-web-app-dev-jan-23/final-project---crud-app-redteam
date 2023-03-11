from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField, StringField, TextAreaField,HiddenField,IntegerField,FileField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
from models import User,db
from queries import Queries

query = Queries(db)
class LoginForm(FlaskForm):  

  email = EmailField(validators = [InputRequired()])

  password = PasswordField(validators = [InputRequired(),Length(min=4,max=20)])

  submit = SubmitField("Login")

class SignupForm(FlaskForm):  
  name = StringField(validators = [InputRequired()])

  email = EmailField(validators = [InputRequired()])

  password = PasswordField(validators = [InputRequired(),Length(min=4,max=20)])

  submit = SubmitField("Signup")

  def validate_email(self,email):
    existing_email=User.query.filter_by(email=email.data).first()

    if existing_email:
      raise ValidationError("That email already exists. Please use a different one.")

class ImageForm(FlaskForm):
  image = FileField('Image',validators =[ FileAllowed(['jpg','jpeg','png'],'Images only!')])
  
class NewRecipeForm(FlaskForm):
  
  name = StringField(validators = [InputRequired()])

  # ingredient = FieldList(FormField(IngredientForm))
  # ingredients = SelectField('Existing Ingredient')

  my_hidden_field = HiddenField("My hidden field")
  
  new_ingredients = StringField("New Ingredient")
  
  instructions = TextAreaField(validators = [InputRequired()])

  time_taken = IntegerField(validators= [InputRequired()])