from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Recipe, Ingredient, User

class Queries:
  PER_PAGE = 10
  def __init__(self,db):
    self.db = db
    
  def select_product_with_details(self, id):
        query = (
            select(Recipe)
            .filter(Recipe.id == id)
            .options(selectinload(Recipe.ingredients))
            .options(selectinload(Recipe.uploaded_by))
            .options(selectinload(Recipe.users))
            .options(selectinload(Recipe.images))
        )
    
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

    if params["time-taken"]:
      query = query.filter(Recipe.timetaken < params["max_time_taken"])

    query = query.options(selectinload(Recipe.name)).options(selectinload(Recipe.uploaded_by))

    return self.db.paginate(query, per_page=Queries.PER_PAGE)