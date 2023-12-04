#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

@app.before_request
def is_logged_in():
    open_access = ['login', 'check_session', 'signup']
    if request.endpoint not in open_access and not session.get('user_id'):
        return {'error': 'unauthorized'}, 401

class Signup(Resource):
    def post(self):
        username = request.get_json().get('username')
        password = request.get_json().get('password')
        image_url = request.get_json().get('image_url')
        bio = request.get_json().get('bio')
        
        user = User(username=username, image_url=image_url, bio=bio)
        user.password_hash = password
        try:
            db.session.add(user)
            db.session.commit()
            session['user_id']=user.id
            return user.to_dict(), 201
        except IntegrityError:
            return {"error": "422 Unprocessable entity"}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session['user_id']
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return user.to_dict(), 200
        return {}, 401

class Login(Resource):
    def post(self):
        username = request.get_json().get('username')
        password = request.get_json().get('password')
        user = User.query.filter(User.username == username).first()

        if user:
            if user.authenticate(password):
                session['user_id']=user.id
                return user.to_dict(), 200
        return {"error": "unauthorized"}, 401

class Logout(Resource):
    def delete(self):
        session['user_id']=None
        return {}, 204
        
class RecipeIndex(Resource):
    def get(self):
        user = User.query.filter(User.id == session['user_id']).first()
        return [recipe.to_dict() for recipe in user.recipes], 200

    def post(self):
        form = request.get_json()
        title = form['title']
        instructions = form['instructions']
        minutes_to_complete = form['minutes_to_complete']
        
        try:
            recipe = Recipe(title=title, instructions=instructions, minutes_to_complete=minutes_to_complete, user_id=session['user_id'])
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except IntegrityError:
            return {'error': 'unprocessable entity'}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)