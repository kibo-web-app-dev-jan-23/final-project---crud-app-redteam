from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Recipe, Ingredient, User
from werkzeug.security import generate_password_hash

class Queries:
  PER_PAGE = 10

  def __init__(self, db):
    self.db = db

  def create_new_user(self,new_user_name,email,password):
    
    password_hash = generate_password_hash(password)
    self.db.session.add(User(name = new_user_name,email =email,password_hash = password_hash))
    self.db.session.commit()
    
    
  def validate_password(self,email,password):
    
    user_password = self.db.session.query(User).filter(User.email == email).first()
    if user_password.check_password(password):
      return True
    else:
      return False


    
  def select_product_with_details(self, id):
    query = (select(Recipe).filter(Recipe.id == id).options(
      selectinload(Recipe.ingredients)).options(
        selectinload(Recipe.uploaded_by)).options(selectinload(
          Recipe.users)).options(selectinload(Recipe.images)))

    return self.db.session.scalars(query).first()
  
  def search_recipes(self, params):
    query = select(Recipe)

    if params["query"]:
      query = query.filter(Recipe.name.like(f"%{params['query']}%"))

    if params["ingredient"]:
      query = query.join(Recipe.ingredients)
      for category in params["ingredient"]:
        # filter where category param is LIKE the category name
        query = query.filter(Ingredient.name.like(f"%{category}%"))

    if params["time_taken"]:
      query = query.filter(Recipe.timetaken < params["max_time_taken"])

    query = query.options(selectinload(Recipe.ingredients)).options(
      selectinload(Recipe.uploaded_by)).options(selectinload(Recipe.images))

    return self.db.paginate(query, per_page=Queries.PER_PAGE)

  # def get_ingredients(self):
  #   ingredients = Ingredient.self.query.all()
  #   ingredients_choices = [(i.name,i.name.caputalize()) for i in ingredients]
  #   return ingredients_choices