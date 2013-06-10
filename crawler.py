from extractor import Extractor
import redis
import os
from py2neo import neo4j, cypher
from urlparse import urlparse
from unidecode import unidecode

class Crawler:
	def __init__(self):
		self.ex = Extractor()

		redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
		self.redis = redis.from_url(redis_url)
		self.seen_key = "URL_SEEN"
		self.queue_key = "URL_QUEUE"
		self.redis.flushdb()

		if os.environ.get('NEO4J_URL'):
			graph_db_url = urlparse(os.environ.get('NEO4J_URL'))
			neo4j.authenticate(
				"{host}:{port}".format(host = graph_db_url.hostname, port = graph_db_url.port),
				graph_db_url.username, graph_db_url.password
			)
			self.graphdb = neo4j.GraphDatabaseService(
				'http://{host}:{port}/db/data'.format(host = graph_db_url.hostname, port = graph_db_url.port)
			)
		else:
			print "DJSLKJDSLFS"
			self.graphdb = neo4j.GraphDatabaseService()
		self.graphdb.clear()
		print "cleared database!"
		self.topic_index = self.graphdb.get_or_create_index(neo4j.Node, "topic")
		self.category_index = self.graphdb.get_or_create_index(neo4j.Node, "category")

	def get_create_rel(self, a_node, rtype, b_node):
		try:
			r = self.graphdb.get_or_create_relationships((a_node, rtype, b_node))[0]
			if r.get_properties().has_key('weight'):
				r.set_properties({'weight': r.get_properties()['weight'] + 1, 'type': rtype})
				print "weight: ", r.get_properties()['weight'] + 1
			else:
				r.set_properties({'weight': 1, 'type': rtype})
		except Exception as e:
			print a_node['name'], a_node._id, b_node['name'], b_node._id
			print "get_create_rel ERROR:", e

	def get_create_node(self, n, typ):
		try:
			nod = self.graphdb.get_or_create_indexed_node(typ, 'name', self.clean(n), {'name': self.clean(n), 'type': typ})
			return nod
		except Exception as e:
			print n, typ
			print "get_create_node ERROR:", e
			return None

	def crawl(self, start):
		#cleaner method names
		visit = lambda x: self.redis.sadd(self.seen_key, x)
		enqueue = lambda x: self.redis.sadd(self.queue_key, self.clean(x))

		limit = 1000000
		enqueue(start)
		while self.redis.scard(self.queue_key) and limit > 0:
			topic = self.redis.spop(self.queue_key)
			if topic and topic.strip() and not self.redis.sismember(self.seen_key, topic):
				visit(topic)
				topic_node = self.get_create_node(topic, 'topic')
				print 'topic: ', topic
				keywords, categories, links = self.ex.extract(topic)
				if topic_node:
					for a in links:
						a_node = self.get_create_node(a, 'topic')
						self.get_create_rel(a_node, 'sibling', topic_node)
						enqueue(a)
					for c in categories:
						c_node = self.get_create_node(c, 'category')
						self.get_create_rel(c_node, 'parent', topic_node)
			limit -= 1

	def clean(self, name):
		return unidecode(name.decode("utf-8", "ignore"))
