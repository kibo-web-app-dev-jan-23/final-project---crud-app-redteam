from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, Column, ForeignKey,String
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

recipe_ingredient_table = db.Table('recipe_ingredient',
    db.Column('recipe_id', Integer, ForeignKey('recipes.id')),
    db.Column('ingredient_id', Integer, ForeignKey('ingredients.id'))
)

user_recipe_table = db.Table('user_recipe',
    db.Column('user_id', Integer, ForeignKey('users.id')),
    db.Column('recipe_id', Integer, ForeignKey('recipes.id'))
)

class Ingredient(db.Model):
  __tablename__ = 'ingredients'
  
  id = Column(Integer, primary_key=True)
  name = Column(String, nullable= False)

class Recipe(db.Model):
  __tablename__ = 'recipes'
  
  id = Column(Integer, primary_key=True)
  name = Column(String,unique = True , nullable = False)
  time_taken = Column(Integer)
  images = db.relationship('Image', backref='recipe', lazy=True)
  ingredients = relationship("Ingredient", secondary=recipe_ingredient_table, backref="recipes")
  users = relationship("User", secondary=user_recipe_table, backref="recipes")
  user_id = db.Column(Integer, ForeignKey('user.id'))
  uploaded_by = db.relationship('User', foreign_keys=[user_id])
  
class Image(db.Model):
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable = False)
    recipe_id = Column(Integer, ForeignKey('recipe.id'), nullable = False)
    
  
class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    recipes = relationship("Recipe", secondary=user_recipe_table, backref="users")
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
