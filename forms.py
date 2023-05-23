from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField, StringField, TextAreaField,HiddenField,IntegerField,FileField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
<<<<<<< HEAD
from flask_uploads import UploadSet,IMAGES, configure_uploads
from models import User,db
from queries import Queries
from flask import Flask

app = Flask(__name__)
app.config['UPLOADED_PHOTOS_DEST'] = '/static/images'
photos = UploadSet('photos', IMAGES)
configure_uploads(app,photos)

=======
from models import User,db
from queries import Queries
>>>>>>> parent of 29747886 (weird errors fixed)

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
<<<<<<< HEAD
  
  image = FileField('Image',validators =[FileAllowed(photos,'Images only!'),FileRequired('File field should not be empty')])
=======
  image = FileField('Image',validators =[ FileAllowed(['jpg','jpeg','png'],'Images only!')])
>>>>>>> parent of 29747886 (weird errors fixed)
  
class NewRecipeForm(FlaskForm):
  
  name = StringField(validators = [InputRequired()])

  # ingredient = FieldList(FormField(IngredientForm))
  # ingredients = SelectField('Existing Ingredient')

  my_hidden_field = HiddenField("My hidden field")
  
  new_ingredients = StringField("New Ingredient")
  
  instructions = TextAreaField(validators = [InputRequired()])

<<<<<<< HEAD
  time_taken = IntegerField(validators= [InputRequired()])
=======
  time_taken = IntegerField(validators= [InputRequired()])
>>>>>>> parent of 29747886 (weird errors fixed)
