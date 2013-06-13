from extractor import Extractor
import sys
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
		self.sibling_index = self.graphdb.get_or_create_index(neo4j.Relationship, "sibling")
		self.parent_index = self.graphdb.get_or_create_index(neo4j.Relationship, "parent")

	def crawl(self, start):
		#cleaner method names
		visit = lambda x: self.redis.sadd(self.seen_key, x)
		enqueue = lambda x: self.redis.sadd(self.queue_key, self.clean(x))

		limit = 1000000
		enqueue(start)
		while self.redis.scard(self.queue_key) and limit > 0:
			batch = neo4j.WriteBatch(self.graphdb)
			topic = self.redis.spop(self.queue_key)
			if topic and topic.strip() and not self.redis.sismember(self.seen_key, topic):
				visit(topic)
				batch.get_or_create_indexed_node('topic', 'name', self.clean(topic), {'name': self.clean(topic), 'type': 'topic'})
				print 'topic: ', topic
				keywords, categories, links = self.ex.extract(topic)
				for i, a in enumerate(links):
					batch.get_or_create_indexed_node('topic', 'name', self.clean(a), {'name': self.clean(a), 'type': 'topic'})
					batch.get_or_create_indexed_relationship('sibling', 'type', 'sibling', 0, 'sibling', i + 1, {'type': 'sibling', 'weight': 1})
					enqueue(a)
				'''for j, c in enumerate(categories):
					batch.get_or_create_indexed_node('category', 'name', self.clean(c), {'name': self.clean(c), 'type': 'category'})
					batch.get_or_create_indexed_relationship('parent', 'type', 'parent', 0, 'parent', j + len(links) + 1, {'type': 'parent', 'weight': 1})'''
			try:
				batch.submit()
			except Exception as e:
				print e
				sys.exit(1)
			limit -= 1

	def clean(self, name):
		return unidecode(name.decode("utf-8", "ignore"))
