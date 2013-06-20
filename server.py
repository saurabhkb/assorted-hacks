from flask import Flask
from flask import render_template
from flask import request
import json
from unidecode import unidecode
from api import Api_manager
from constants import *

app = Flask(__name__)

@app.route('/users/', methods = ['GET', 'POST', 'PUT', 'DELETE'])
def users():
	if request.method == 'GET':
		#get all users
		return 'getting all users!'
	if request.method == 'POST':
		#add new user
		return 'adding new user'
	if request.method == 'PUT':
		#error
		return 'error!'
	if request.method == 'DELETE':
		#delete all users
		return 'deleting user!'

@app.route('/user/<id>', methods = ['GET', 'POST', 'PUT', 'DELETE'])
def user(id):
	if request.method == 'GET':
		#get details of <id> user
		return 'getting user!' + id
	if request.method == 'POST':
		#error
		return 'adding new user'
	if request.method == 'PUT':
		#update user <id>'s data
		return 'error!'
	if request.method == 'DELETE':
		#delete user <id>
		return 'deleting user!'
@app.route('/synonyms/', methods = ['GET', 'POST', 'PUT', 'DELETE'])
def synonyms():
	if request.method == 'GET':
		#get all synonyms
		return 'getting user!'
	if request.method == 'POST':
		#add new synonym
		return 'adding new user'
	if request.method == 'PUT':
		#error
		return 'error!'
	if request.method == 'DELETE':
		#delete all synonyms
		return 'deleting user!'

@app.route('/synonym/<id>', methods = ['GET', 'POST', 'PUT', 'DELETE'])
def synonym(id):
	if request.method == 'GET':
		#get synonym
		return 'getting user!'
	if request.method == 'POST':
		#error
		return 'adding new user'
	if request.method == 'PUT':
		#update synonym <id>'s data
		return 'error!'
	if request.method == 'DELETE':
		#delete synonym <id>
		return 'deleting user!'

@app.route('/stopwords/', methods = ['GET', 'POST', 'PUT', 'DELETE'])
def stopwords():
	if request.method == 'GET':
		#get all stopwords
		return 'getting user!'
	if request.method == 'POST':
		#add new stopword
		return 'adding new user'
	if request.method == 'PUT':
		#error
		return 'error!'
	if request.method == 'DELETE':
		#delete all stopwords
		return 'deleting user!'

@app.route('/stopword/<id>', methods = ['GET', 'POST', 'PUT', 'DELETE'])
def stopword(id):
	if request.method == 'GET':
		#get stopword
		return 'getting user!'
	if request.method == 'POST':
		#error
		return 'adding new user'
	if request.method == 'PUT':
		#update stopword <id>'s data
		return 'error!'
	if request.method == 'DELETE':
		#delete stopword <id>
		return 'deleting user!'

app.run(debug = True)
