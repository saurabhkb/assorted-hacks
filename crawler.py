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
			self.graphdb = neo4j.GraphDatabaseService()
		self.graphdb.clear()
		self.topic_index = self.graphdb.get_or_create_index(neo4j.Node, "topic")
		self.category_index = self.graphdb.get_or_create_index(neo4j.Node, "category")

	def crawl(self, start):
		#cleaner method names
		visit = lambda x: self.redis.sadd(self.seen_key, x)
		enqueue = lambda x: self.redis.sadd(self.queue_key, self.clean(x))
		get_create_node = lambda x, typ: self.topic_index.get_or_create('name', x, {'name': x, 'type': 'topic'}) if typ == 'topic' else self.category_index.get_or_create('name', x, {'name': x, 'type': 'category'})
		create_rel = lambda x, typ, y: self.graphdb.get_or_create_relationships((x, typ, y, {'weight': 1}))

		enqueue(start)
		while self.redis.scard(self.queue_key):
			topic = self.redis.spop(self.queue_key)
			if topic and topic.strip() and not self.redis.sismember(self.seen_key, topic):
				visit(topic)
				topic_node = get_create_node(topic, 'topic')
				print 'topic: ', topic
				keywords, categories, links = self.ex.extract(topic)
				for a in links:
					a_node = get_create_node(a, 'topic')
					rel = self.graphdb.match_one(start_node = a_node, rel_type = None, end_node = topic_node, bidirectional = True)
					if not rel: create_rel(a_node, 'sibling', topic_node)
					else:
						orig_wt = rel.get_properties()['weight']
						rel.set_properties({'weight': orig_wt + 1})
					enqueue(a)
				for c in categories:
					c_node = get_create_node(c, 'category')
					get_create_rel(c_node, 'parent', topic_node)
					rel = self.graphdb.match_one(start_node = c_node, end_node = topic_node, bidirectional = True)
					if not rel: create_rel(c_node, 'sibling', topic_node)
					else:
						orig_wt = rel.get_properties()['weight']
						rel.set_properties({'weight': orig_wt + 1})

	def clean(self, name):
		clean_name = ""
		if type(name) == unicode:
			clean_name = unidecode(name)
		else:
			clean_name = str(name)
		return clean_name
