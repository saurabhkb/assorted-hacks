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
		#self.graphdb.clear()
		#print "cleared database!"
		self.topic_index = self.graphdb.get_or_create_index(neo4j.Node, "topic")
		self.category_index = self.graphdb.get_or_create_index(neo4j.Node, "category")

	def crawl(self, start):
		#cleaner method names
		visit = lambda x: self.redis.sadd(self.seen_key, x)
		enqueue = lambda x: self.redis.sadd(self.queue_key, self.clean(x))

		limit = 1000000
		enqueue(start)
		node_batch = neo4j.WriteBatch(self.graphdb)
		rel_batch = neo4j.WriteBatch(self.graphdb)
		while self.redis.scard(self.queue_key) and limit > 0:
			success = False
			try:
				node_batch.clear()
				rel_batch.clear()
			except Exception as e:
				print e
				continue
			topic = self.redis.spop(self.queue_key)
			if topic and topic.strip() and not self.redis.sismember(self.seen_key, topic):
				visit(topic)
				node_batch.get_or_create_indexed_node(self.topic_index, 'name', topic, {'name': topic, 'type': 'topic'})
				print 'topic: ', topic
				try:
					keywords, categories, links = self.ex.extract(topic)
					success = True
				except Exception as e:
					success = False
					print e
				if success:
					for a in links:
						node_batch.get_or_create_indexed_node(self.topic_index, 'name', a, {'name': a, 'type': 'topic'})
						enqueue(a)
					for c in categories:
						node_batch.get_or_create_indexed_node(self.topic_index, 'name', c, {'name': c, 'type': 'category'})
					try:
						result = node_batch.submit()
						success = True
					except Exception as e:
						success = False
						print e
				if success:
					topic_node = result[0]
					for anode in result[1:1 + len(links)]:
						rel_batch.get_or_create((anode, 'sibling', topic_node, {}))
					for cnode in result[1 + len(links):]:
						rel_batch.get_or_create((anode, 'category', topic_node, {}))
					try:
						result = rel_batch.submit()
					except Exception as e:
						success = False
						print e
			limit -= 1

	def clean(self, name):
		if type(name) == unicode:
			return unidecode(name)
		else:
			return unidecode(name.decode("utf-8", "ignore"))
