from extractor import Extractor
import redis
import os
from py2neo import neo4j, cypher
from urlparse import urlparse
from util import Util
import sys

class Crawler(Util):
	def __init__(self):
		Util.__init__(self)

		redis_url = os.getenv('REDISCLOUD_URL', 'redis://localhost:6379')
		self.redis = redis.from_url(redis_url)
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
		self.rel_key = "REL_CREATED"
		self.node_key = "NODE_CREATED"
		self.max_tries = 5
		self.node_index = self.graphdb.get_or_create_index(neo4j.Node, 'NODE')
		self.topic_index = self.graphdb.get_or_create_index(neo4j.Node, self.ARTICLE)
		self.category_index = self.graphdb.get_or_create_index(neo4j.Node, self.CATEGORY)
		self.disambiguation_index = self.graphdb.get_or_create_index(neo4j.Node, self.DISAMBIGUATION)

	def incr_rel(self, a, b, r):
		try:
			x = sorted([a, b])
			key = r + ':' + x[0] + ':' + x[1]
			self.redis.incr(key, 1)
			self.redis.sadd(self.rel_key, key)
			return True
		except Exception as e:
			print "incr_rel: REDIS ERROR-------------------------", e
			return False
	
	def incr(self, a):
		try:
			self.redis.incr(a, 1)
			return True
		except Exception as e:
			print "incr: REDIS ERROR-------------------------", e
			return False
	
	def submit_batch(self, b):
		tries = self.max_tries
		while tries:
			try:
				b.submit()
				b.clear()
				return True
			except Exception as e:
				print e
			tries -= 1
		return False

	def NODE(self, b, x, t):
		#b.get_or_create_indexed_node(t, 'name', x, {'name': x, 'class': t})
		b.get_or_create_indexed_node(self.node_index, 'name', x, {'name': x, 'class': t, 'freq': 0})
	
	def traverse(self, root):
		seen_key = "URL_SEEN"
		queue_key = "URL_QUEUE"
		ex = Extractor()
		batch = neo4j.WriteBatch(self.graphdb)
		BATCH_LIM = 5000

		queue_empty = lambda: self.redis.scard(queue_key) == 0
		seen = lambda x: self.redis.sismember(seen_key, x)
		visit = lambda x: self.redis.sadd(seen_key, x)
		dequeue = lambda: self.redis.spop(queue_key)
		enqueue = lambda x: self.redis.sadd(queue_key, self._encode_str(x))
		#NODE = lambda b, x, t: b.get_or_create_indexed_node(t, 'name', x, {'name': x, 'class': t})
		REL = lambda b, n1, r, w, n2: b.get_or_create((n1, r, n2, {'class': r, 'weight': w}))

		num = 0
		enqueue(root)
		while not queue_empty():
			current = dequeue()
			print current
			if current and current.strip() and not seen(current):
				visit(current)
				result = ex.getAllFromCategory(current)
				self.NODE(batch, current, self.CATEGORY)
				if self.incr(current): pass
				else: break
				num += 1
				for page in result['pages']:
					print "{0}\tp:{1}".format(current, page)
					if self.incr_rel(page, current, self.CATEGORY_REL): pass
					else: break
					if self.incr(page): pass
					else: break
					self.NODE(batch, page, self.ARTICLE)
					num += 1
					links = ex.getWikiLinks(page)
					for a in links:
						try: print "{0}\tp:{1}\t{2}".format(current, page, a)
						except Exception as e: print e
						if self.incr_rel(a, page, self.SIBLING_REL): pass
						else: break
						if self.incr(a): pass
						else: break
						self.NODE(batch, a, self.ARTICLE)
						num += 1
				for subcat in result['categories']:
					try: print "{0}\tc:{1}".format(page, subcat)
					except Exception as e: print e
					if self.incr_rel(subcat, current, self.SUBCAT_REL): pass
					else: break
					if self.incr(subcat): pass
					else: break
					self.NODE(batch, subcat, self.CATEGORY)
					enqueue(subcat)
					num += 1
			if num >= BATCH_LIM:
				self.submit_batch(batch)
				num = 0
		if num > 0:
			self.submit_batch(batch)
			num = 0
		for k in self.redis.smembers(self.rel_key):
			nodes = k.split(":")
			rel = nodes[0]
			n1 = self.node_index.get('name', nodes[1])
			n2 = self.node_index.get('name', nodes[2])
			if n1 and n2:
				n1 = n1[0]
				n2 = n2[0]
			else:
				continue
			if rel in [self.DISAMB_REL, self.CATEGORY_REL, self.SUBCAT_REL]:
				w = 1
			else:
				try:
					num1_int_num2 = int(self.redis.get(k))
					num1 = int(self.redis.get(nodes[1]))
					num2 = int(self.redis.get(nodes[2]))
					w = num1_int_num2 / float(num1 + num2 - num1_int_num2)
				except Exception as e:
					print "ERROR:", e
					continue
			n1['freq'] = num1
			n2['freq'] = num2
			REL(batch, n1, rel, w, n2)
			num += 1

			if num >= BATCH_LIM:
				self.submit_batch(batch)
				num = 0
		if num > 0:
			self.submit_batch(batch)
			num = 0
		print "DONE>>>>>>>>>>>>>>>"


	def crawl(self, start):
		seen_key = "URL_SEEN"
		queue_key = "URL_QUEUE"
		ex = Extractor()
		batch = neo4j.WriteBatch(self.graphdb)
		BATCH_LIM = 1000
		#cleaner method names
		queue_empty = lambda: self.redis.scard(queue_key) == 0
		seen = lambda x: self.redis.sismember(seen_key, x)
		visit = lambda x: self.redis.sadd(seen_key, x)
		dequeue = lambda: self.redis.spop(queue_key)
		enqueue = lambda x: self.redis.sadd(queue_key, self._encode_str(x))
		NODE = lambda b, x, t: b.get_or_create_indexed_node(t, 'name', x, {'name': x, 'class': t})
		REL = lambda b, n1, r, w, n2: b.get_or_create((n1, r, n2, {'class': r, 'weight': w}))

		limit = 50000
		num = 0
		enqueue(start)
		while not queue_empty():
			topic = dequeue()
			if topic and topic.strip() and not seen(topic):
				visit(topic)
				print 'topic: ', topic
				result = ex.extract(topic)
				NODE(batch, topic, result['type'])
				self.incr(topic)
				num += 1
				if result['type'] == self.CATEGORY:
					pass
				elif result['type'] == self.ARTICLE:
					for a in result['links']:
						self.incr_rel(a, topic, self.SIBLING_REL)
						self.incr(a)
						NODE(batch, a, self.ARTICLE)
						num += 1
						if limit > 0:
							enqueue(a)
							limit -= 1
					for c in result['categories']:
						self.incr_rel(a, topic, self.CATEGORY_REL)
						NODE(batch, c, self.CATEGORY)
						num += 1
				elif result['type'] == self.DISAMBIGUATION:
					for a in result['links']:
						self.incr_rel(a, topic, self.DISAMB_REL)
						NODE(batch, a, self.DISAMBIGUATION)
						num += 1
			if num >= BATCH_LIM:
				batch.submit()
				batch.clear()
				num = 0
		if num > 0:
			batch.submit()
			batch.clear()
			num = 0
		batch.clear()
		for k in self.redis.smembers(self.rel_key):
			print k
			nodes = k.split(":")
			rel = nodes[0]
			n1 = self.topic_index.get('name', nodes[1])
			n2 = self.topic_index.get('name', nodes[2])
			if n1 and n2:
				n1 = n1[0]
				n2 = n2[0]
			else: continue
			if rel in [self.DISAMB_REL, self.CATEGORY_REL]:
				w = 1
			else:
				try:
					num1_int_num2 = int(self.redis.get(k))
					num1 = int(self.redis.get(nodes[1]))
					num2 = int(self.redis.get(nodes[2]))
					w = num1_int_num2 / float(num1 + num2 - num1_int_num2)
				except Exception as e:
					print "ERROR: ", e
					w = 1
			REL(batch, n1, rel, w, n2)
			num += 1

			if num >= BATCH_LIM:
				batch.submit()
				batch.clear()
				num = 0
		if num > 0:
			batch.submit()
			batch.clear()
			num = 0
