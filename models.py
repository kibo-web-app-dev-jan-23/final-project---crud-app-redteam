from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from flask_login import UserMixin
# from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db = SQLAlchemy(app)

recipe_ingredient_table = db.Table(
  'recipe_ingredient', db.Column('recipe_id', ForeignKey('recipes.id')),
  db.Column('ingredient_id', ForeignKey('ingredients.id')))

user_recipe_table = db.Table('user_recipe',
                             db.Column('user_id', ForeignKey('users.id')),
                             db.Column('recipe_id', ForeignKey('recipes.id')))


class Ingredient(db.Model):
  __tablename__ = 'ingredients'

  id = Column(Integer, primary_key=True)
  name = Column(String, nullable=False)
  recipes = relationship('Recipe',
                         secondary=recipe_ingredient_table,
                         back_populates='ingredients')


class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    time_taken = Column(Integer)
    images = relationship('Image', backref='recipe', lazy=True)
    ingredients = relationship('Ingredient',
                               secondary=recipe_ingredient_table,
                               back_populates='recipes')
    users = relationship('User',
                         secondary=user_recipe_table,
                         back_populates='recipes')
    user_id = Column(Integer, ForeignKey('users.id'))
    uploaded_by = relationship('User', back_populates='uploaded_recipes')
    instructions = Column(Text)

class Image(db.Model):
  __tablename__ = "image"
  id = Column(Integer, primary_key=True)
  url = Column(String(255), nullable=False)
  recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    recipes = relationship('Recipe',
                           secondary=user_recipe_table,
                           back_populates='users')
    password_hash = Column(String(128))
    uploaded_recipes = relationship('Recipe', back_populates='uploaded_by')
  
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



with app.app_context():
  db.metadata.create_all(db.engine)
  db.create_all()
