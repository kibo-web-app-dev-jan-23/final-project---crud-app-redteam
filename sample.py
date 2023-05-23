from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, Column, ForeignKey, String, Table
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'

db = SQLAlchemy(app)

# Define your models here...


recipe_ingredient_table = db.Table('recipe_ingredient',        
    db.Column('recipe_id', ForeignKey('recipes.id')),
    db.Column('ingredient_id', ForeignKey('ingredients.id'))
)

user_recipe_table = db.Table('user_recipe',
    db.Column('user_id', ForeignKey('users.id')),
    db.Column('recipe_id', ForeignKey('recipes.id'))
)

class Ingredient(db.Model):
    __tablename__ = 'ingredients'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    recipes = relationship('Recipe', secondary=recipe_ingredient_table, back_populates='ingredients')


class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    time_taken = Column(Integer)
    images = relationship('Image', backref='recipe', lazy=True)
    ingredients = relationship('Ingredient', secondary=recipe_ingredient_table, back_populates='recipes')
    users = relationship('User', secondary=user_recipe_table, back_populates='recipes')
    user_id = Column(Integer, ForeignKey('users.id'))
    uploaded_by = relationship('User', back_populates='recipes')


class Image(db.Model):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    recipes = relationship('Recipe', secondary=user_recipe_table, back_populates='users')
    password_hash = Column(String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

with app.app_context():
    # Create the database tables
    
    db.metadata.create_all(db.engine)
    db.create_all()

    # Create some example data
    user1 = User(name='john')
    user2 = User(name='jane')

    ingredient1 = Ingredient(name='salt')
    ingredient2 = Ingredient(name='pepper')
    ingredient3 = Ingredient(name='sugar')
    ingredient4 = Ingredient(name='flour')

    recipe1 = Recipe(name='Scrambled eggs', time_taken='10 mins', users=[user1])
    recipe2 = Recipe(name='Chocolate cake', time_taken='1 hour', users=[user2])

    image1 = Image(url='scrambled_eggs.jpg', recipe=recipe1)
    image2 = Image(url='chocolate_cake.jpg', recipe=recipe2)

    # Add the objects to the session
    db.session.add_all([user1, user2, ingredient1, ingredient2, ingredient3, ingredient4, recipe1, recipe2, image1, image2])

    # Commit the session to persist the objects to the database
    db.session.commit()
