from pymongo import MongoClient
import os

class Datastore:
	def __init__(self):
		mongourl = os.environ.get('MONGOLAB_URI')
		self.client = MongoClient(mongourl)
		print "CREATED DATASTORE CLIENT!", self.client
		self.db = self.client.get_default_database()

	def find_one(self, collection, *args, **kwargs):
		return self.db[collection].find_one(*args, **kwargs)

	def find(self, collection, spec = None, fields = None):
		return self.db[collection].find(spec, fields)

	def insert(self, collection, a):
		return self.db[collection].insert(a)

	def remove(self, collection, a):
		return self.db[collection].remove(a)

	def update(self, collection, query, update, option):
		return self.db[collection].update(query, update, option['upsert'])

	def distinct(self, collection, a):
		return self.db[collection].distinct(a)
