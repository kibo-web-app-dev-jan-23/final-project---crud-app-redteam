from flask import Flask, render_template, request, abort
from queries import Queries
from models import db
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///../database_name'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../products.db"

# enable logging SQL queries
# app.config["SQLALCHEMY_ECHO"] = True

# initialize the app with the extension
db.init_app(app)
queries = Queries(db)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/recipe/<recipe_id>")
def show_product(recipe_id):
    product = queries.select_product_with_details(recipe_id)
    if not product:
        abort(404, "No product with that id")
    return render_template("recipe.html.html", product=product)






app.run(host='0.0.0.0', port=81)
