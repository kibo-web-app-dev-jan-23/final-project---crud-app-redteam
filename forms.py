from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField, StringField, TextAreaField,HiddenField,IntegerField,FileField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_wtf.file import FileAllowed, FileRequired
from flask_uploads import UploadSet,IMAGES, configure_uploads
from models import User,db
from queries import Queries
from flask import Flask

app = Flask(__name__)
app.config['UPLOADED_PHOTOS_DEST'] = '/static/images'
photos = UploadSet('photos', IMAGES)
configure_uploads(app,photos)


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
  
  image = FileField('Image',validators =[FileAllowed(photos,'Images only!'),FileRequired('File field should not be empty')])
  
  
class NewRecipeForm(FlaskForm):
  
  name = StringField(validators = [InputRequired()])

  my_hidden_field = HiddenField("My hidden field")
  
  ingredients = TextAreaField(validators = [InputRequired()])
  
  instructions = TextAreaField(validators = [InputRequired()])

  time_taken = IntegerField(validators= [InputRequired()])
