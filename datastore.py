from pymongo import MongoClient
import os

class Datastore:
	def __init__(self):
		mongourl = os.environ.get('MONGOLAB_URI')
		self.client = MongoClient(mongourl)

	def find_one(self, collection, *args, **kwargs):
		return self.client.db[collection].find_one(*args, **kwargs)

	def find(self, collection, spec = None, fields = None):
		return self.client.db[collection].find(spec, fields)

	def insert(self, collection, a):
		return self.client.db[collection].insert(a)

	def remove(self, collection, a):
		return self.client.db[collection].remove(a)

	def update(self, collection, query, update, option):
		return self.client.db[collection].update(query, update, option['upsert'])

	def distinct(self, collection, a):
		return self.client.db[collection].distinct(a)
