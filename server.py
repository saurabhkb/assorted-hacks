from flask import Flask
from flask import render_template
from flask import request
import json
from unidecode import unidecode
from api import Api_manager
from constants import *

app = Flask(__name__)
manager = Api_manager()

@app.route('/add_user', methods = ['GET'])
def add_user():
	api_key = request.args.get(API_KEY)
	user_id = request.args.get(USER_ID)
	if not manager.authenticate(api_key):
		return manager.error(AUTH_FAIL, 'could not validate api_key. are you sure it is correct?')
	if not manager.valid(user_id):
		return manager.error(INVALID_ARG, 'there is an error in one of your arguments')
	return manager.success('successfully created user with user_id: {0}'.format(user_id))

@app.route('/score', methods = ['GET'])
def score():
	
app.run(debug = True)
