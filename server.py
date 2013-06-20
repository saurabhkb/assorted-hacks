from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask.ext.restful import Api, Resource, abort
import json
from unidecode import unidecode

from api import Api_manager
from security import SecurityManager
from constants import *
from datastore import DataStore

app = Flask(__name__)
api = Api(app)

SecurityM = SecurityManager()
DataM = DataStore()

'''users collection resource'''
class users(Resource):
	def __init__(self):
		self.key = SecurityM.check_header(request.headers)
		if self.key == -1:
			abort(401, status = FAILURE, message = AUTH_FAIL)

	def get(self):
		#get all users
		user_list = DataM.smembers("{0}:{1}".format(self.key, USERS))
		return jsonify(status = SUCCESS, users = list(user_list))

	def post(self):
		try:
			user_id = request.form['id']
			ret = DataM.sadd("{0}:{1}".format(self.key, USERS), user_id)
			return jsonify(status = SUCCESS, data = ret)
		except KeyError:
			abort(400, status = FAILURE, message = INVALID_ARG)

	def put(self):
		#error
		abort(405, status = FAILURE, message = INVALID_HTTP_VERB)

	def delete(self):
		#delete all users
		ret = DataM.delete("{0}:{1}".format(self.key, USERS))
		return jsonify(status = SUCCESS, data = ret)

'''user specific resource'''
class user(Resource):
	def __init__(self):
		self.key = SecurityM.check_header(request.headers)
		if self.key == -1:
			abort(401, status = FAILURE, message = AUTH_FAIL)

	def get(self, uri):
		#get details of <id> user
		if not DataM.sismember("{0}:{1}".format(self.key, USERS), uri):
			abort(404, status = FAILURE, message = USER_NOT_FOUND)
		interest_list = DataM.smembers("{0}:{1}:{2}".format(self.key, uri, INTERESTS))
		return jsonify(status = SUCCESS, interests = list(interest_list))

	def post(self, uri):
		#error
		return abort(405, status = FAILURE, error = INVALID_HTTP_VERB)

	def put(self, uri):
		#update user <id>'s data
		if not DataM.sismember("{0}:{1}".format(self.key, USERS), uri):
			abort(404, status = FAILURE, message = USER_NOT_FOUND)
		add_res = rem_res = []
		try:
			add = request.form['add']
			rem = request.form['rem']
			add_l = add.split(',')
			for add_elem in add_l:
				DataM.sadd("{0}:{1}:{2}".format(self.key, uri, INTERESTS), add_elem)
			add_res = add_l
			rem_l = rem.split(',')
			for rem_elem in rem_l:
				DataM.srem("{0}:{1}:{2}".format(self.key, uri, INTERESTS), rem_elem)
			rem_res = rem_l
		except:
			pass
		return jsonify(status = SUCCESS, added = add_res, removed = rem_res)

	def delete(self, uri):
		if not DataM.sismember("{0}:{1}".format(self.key, USERS), uri):
			abort(404, status = FAILURE, message = USER_NOT_FOUND)
		#delete user <id>
		ret_interests = DataM.delete("{0}:{1}:{2}".format(self.key, uri, INTERESTS))
		ret_user_set = DataM.srem("{0}:{1}".format(self.key, USERS), uri)
		return jsonify(status = SUCCESS, data = [ret_interests, ret_user_set])

api.add_resource(users, '/users')
api.add_resource(user, '/user/<uri>')
app.run(debug = True)
