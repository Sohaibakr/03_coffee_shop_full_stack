import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from database.models import db_drop_and_create_all, setup_db, Drink
from auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()

    short = []
    for drink in drinks:
        short.append(drink.short())

    return jsonify({"success": True, "drinks": short})


'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    long_drinks = [drink.long() for drink in drinks]

    return jsonify({"success": True, "drinks": long_drinks})


'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=["POST"])
@requires_auth('post:drinks')
def post_drinks(payload):
    json_body = request.get_json()
    title = json_body.get('title', None)
    recipe = json_body.get('recipe', None)

    if (title is None) or (recipe is None):
        abort(400)

    drink_recipe = json.dumps([recipe])
    drink = Drink(title=title, recipe=drink_recipe)

    try:
        drink.insert()
    except:
        abort(422)

    return jsonify({"success": True, "drinks": drink.long()})


'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    drink = Drink.query.filter(Drink.id == str(id)).one_or_none()

    if drink is None:
        abort(404)

    json_body = request.get_json()
    title = json_body.get('title', None)
    recipe = json_body.get('recipe', None)

    if (title is not None):
        drink.title = title
    if (recipe is not None):
        drink.recipe = recipe

    try:
        drink.update()
    except Exception as e:
        abort(422)

    return jsonify({"success": True, "drinks": [drink.long()]})


'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    drink = Drink.query.filter(Drink.id == str(id)).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except Exception as e:
        abort(422)

    return jsonify({"success": True, "delete": id})


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Sorry you are unauthorized!"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Sorry you cannot access this resources"
    }), 403


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "We couldn't find what you are looking for!"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Your request is not well formated!"
    }), 400


@app.errorhandler(422)
def unprocessable_entity(error):
    return jsonify({
        "success": False,
        "message": "Sorry, we coludn't proccess your request"
    }), 422


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify("Sorry you are unauthorized " + str(error)), 401
