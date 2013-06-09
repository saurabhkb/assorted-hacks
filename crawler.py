from extractor import Extractor
import redis
import os
from py2neo import neo4j, cypher
from urlparse import urlparse

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
				graph_db_url.username, graph_db_url.passowrd
			)
			self.graphdb = neo4j.GraphDatabaseService(
				'http://{host}:{port}/db/data'.format(host = graph_db_url.hostname, port = graph_db_url.port)
			)
		else:
			self.graphdb = neo4j.GraphDatabaseService()
		self.graphdb.clear()
		self.topic_index = self.graphdb.get_or_create_index(neo4j.Node, "topic")
		self.category_index = self.graphdb.get_or_create_index(neo4j.Node, "category")

	def crawl(self, start):
		#cleaner method names
		visit = lambda x: self.redis.sadd(self.seen_key, x)
		enqueue = lambda x: self.redis.sadd(self.queue_key, x)
		get_create_node = lambda x, typ: self.topic_index.get_or_create('name', x, {'name': x, 'type': 'topic'}) if typ == 'topic' else self.category_index.get_or_create('name', x, {'name': x, 'type': 'category'})
		get_create_rel = lambda x, typ, y: self.graphdb.get_or_create_relationships((x, typ, y, {'weight': 1}))

		enqueue(start)
		i = 5
		while self.redis.scard(self.queue_key) and i > 0:
			topic = self.redis.spop(self.queue_key)
			if topic and topic.strip() and not self.redis.sismember(self.seen_key, topic):
				visit(topic)
				topic_node = get_create_node(topic, 'topic')
				keywords, categories, links = self.ex.extract(topic)
				for a in links:
					a_node = get_create_node(a, 'topic')
					get_create_rel(a_node, 'sibling', topic_node)
					enqueue(a)
				for c in categories:
					c_node = get_create_node(c, 'category')
					get_create_rel(c_node, 'parent', topic_node)
			i -= 1
