from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask.ext.restful import Api, Resource, abort, reqparse
import json
from unidecode import unidecode

from api import Api_manager
from learner import Learner
from security import SecurityManager
from constants import *
from datastore import DataStore

app = Flask(__name__)
api = Api(app)

SecurityM = SecurityManager()
DataM = DataStore()
LearnM = Learner()

'''users collection resource'''
class users(Resource):
	def __init__(self):
		self.key = SecurityM.check_header(request.headers)
		if self.key == -1:
			abort(401, status = FAILURE, message = AUTH_FAIL)
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('id', type = str)

		#the following two lines are only for debugging purposes!
		self.parser.add_argument('key', type = str)
		if self.parser.parse_args()['key']: self.key = self.parser.parse_args()['key']

	def get(self):
		#get all users
		user_list = DataM.get_users_for_key(self.key)
		return jsonify(status = SUCCESS, users = list(user_list))

	def post(self):
		user_id = self.parser.parse_args()['id']
		if not user_id: abort(400, status = FAILURE, message = INVALID_ARG)
		num = DataM.create_user_for_key(self.key, user_id)
		return jsonify(status = SUCCESS, rows_affected = num)

	def put(self):
		#error
		abort(405, status = FAILURE, message = INVALID_HTTP_VERB)

	def delete(self):
		#delete all users
		num = DataM.rem_all_users_for_key(self.key)
		return jsonify(status = SUCCESS, rows_affected = num)

'''user specific resource'''
class user(Resource):
	def __init__(self):
		self.key = SecurityM.check_header(request.headers)
		if self.key == -1:
			abort(401, status = FAILURE, message = AUTH_FAIL)
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('add', type = str, default = [])
		self.parser.add_argument('rem', type = str, default = [])
		self.parser.add_argument('action', type = str, default = 'read')
		self.parser.add_argument('keyword_args', type = str, default = "")
		self.parser.add_argument('url_args', type = str, default = "")

		#the following two lines are only for debugging purposes!
		self.parser.add_argument('key', type = str)
		if self.parser.parse_args()['key']: self.key = self.parser.parse_args()['key']

	def get(self, uri):
		#get details of <id> user
		if not DataM.is_user_for_key(self.key, uri):
			abort(404, status = FAILURE, message = RESOURCE_NOT_FOUND)

		args = self.parser.parse_args()
		if args['action'] == 'read':
			interest_list, length = DataM.get_interests_for_user_for_key(self.key, uri, interest_types = (SUPPLIED))
			return jsonify(status = SUCCESS, uid = uri, num = length, interests = list(interest_list))

		elif args['action'] == 'interest_score':
			resp = {}
			kws_toscore = args['keyword_args']
			s = LearnM.score_all(kws_toscore.split(DELIM))
			return jsonify(status = SUCCESS, uid = uri, num = length, score = overall)

		elif args['action'] == 'classify':
			kw_toclassify = args['keyword_args']
			if kw_toclassify:
				pass
			url_toclassify = args['url_args']
			if url_toclassify:
				pass

		elif args['action'] == 'generate':
			interest_list, length = DataM.get_interests_for_user_for_key(self.key, uri, interest_types = (GENERATED))
			return jsonify(status = SUCCESS, uid = uri, num_interests = length, interests = list(interest_list))

		abort(400, status = FAILURE, message = INVALID_ARG)	#control should not reach here except in case of error

	def post(self, uri):
		#error
		return abort(405, status = FAILURE, error = INVALID_HTTP_VERB)

	def put(self, uri):
		#update user <id>'s data
		if not DataM.is_user_for_key(self.key, uri):
			abort(404, status = FAILURE, message = RESOURCE_NOT_FOUND)
		args = self.parser.parse_args()
		for add_elem in args['add'].split(DELIM):
			DataM.add_interest_for_user_for_key(self.key, uri, add_elem)
		for rem_elem in args['rem'].split(DELIM):
			DataM.rem_interest_for_user_for_key(self.key, uri, rem_elem)
		return jsonify(status = SUCCESS, added = args['add'], removed = args['rem'])

	def delete(self, uri):
		#delete user <id>
		if not DataM.is_user_for_key(self.key, uri):
			abort(404, status = FAILURE, message = RESOURCE_NOT_FOUND)
		num = DataM.rem_user_for_key(self.key, uri)
		return jsonify(status = SUCCESS, rows_affected = num)


api.add_resource(users, '/users')
api.add_resource(user, '/user/<uri>')
app.run(debug = True)
