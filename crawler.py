from extractor import Extractor
import os
from py2neo import neo4j, cypher
from urlparse import urlparse
from util import Util
import sys
import md5
from fastdatastore import FastDataStore

class Break(Exception): pass

class Crawler(Util):
	def __init__(self):
		Util.__init__(self)
		self.fdb = FastDataStore()

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
		self.disambiguation_index = self.graphdb.get_or_create_index(neo4j.Node, self.DISAMBIGUATION)

	def incr_rel(self, a, b, r):
		try:
			x = sorted([a, b])
			key = r + ':' + x[0] + ':' + x[1]
			self.fdb.incr(key, 1)
			self.fdb.sadd(self.rel_key, key)
			return True
		except Exception as e:
			raise Break
	
	def submit_batch(self, b):
		tries = self.max_tries
		while tries > 0:
			try:
				b.submit()
				b.clear()
				return True
			except Exception as e:
				print e
			tries -= 1
		return False

	def NODE(self, b, x, t):
		b.get_or_create_indexed_node(self.node_index, 'name', x, {'name': x, 'class': t})
			
	def spider(self, root, pages = True, subcategories = True, action = "traverse", preclean = False, depth = 1):
		if preclean: self.graphdb.clear()
		seen_key = "URL_SEEN"
		queue_key = "URL_QUEUE"
		ex = Extractor()
		batch = neo4j.WriteBatch(self.graphdb)
		BATCH_LIM = 50

		queue_empty = lambda: self.fdb.scard(queue_key) == 0
		seen = lambda x: self.fdb.sismember(seen_key, x)
		visit = lambda x: self.fdb.sadd(seen_key, x)
		dequeue = lambda: self.fdb.spop(queue_key)
		enqueue = lambda x: self.fdb.sadd(queue_key, self._encode_str(x))
		REL = lambda b, n1, r, w, n2: b.get_or_create((n1, r, n2, {'class': r, 'weight': w}))

		num = 0
		if action == "traverse":
			enqueue(root)
			while not queue_empty():
				current = dequeue()
				print current
				if current and current.strip() and not seen(current):
					visit(current)
					result = ex.getAllFromCategory(current)
					self.NODE(batch, current, self.CATEGORY)
					num += 1
					if pages:
						for page in result['pages']:
							print "{0}\tp:{1}".format(current[:15], page)
							self.incr_rel(page, current, self.CATEGORY_REL)
							self.NODE(batch, page, self.ARTICLE)
							num += 1
							links = ex.getWikiLinks(page)
							for a in links:
								print "{0}\tp:{1}\t{2}".format(current[:15], page, a)
								self.incr_rel(a, page, self.SIBLING_REL)
								self.NODE(batch, a, self.ARTICLE)
								num += 1
					if subcategories:
						for subcat in result['categories']:
							print "{0}\tc:{1}".format(current, subcat)
							self.incr_rel(subcat, current, self.SUBCAT_REL)
							self.NODE(batch, subcat, self.CATEGORY)
							enqueue(subcat)
							num += 1
				if num >= BATCH_LIM:
					self.submit_batch(batch)
					num = 0
		elif action == "crawl":
			enqueue(root)
			while not queue_empty():
				topic = dequeue()
				if topic and topic.strip() and not seen(topic):
					visit(topic)
					result = ex.extract(topic)
					depth -= 1
					self.NODE(batch, topic, result['type'])
					num += 1
					if result['type'] == self.CATEGORY:
						pass
					elif result['type'] == self.ARTICLE:
						for a in result['links']:
							self.incr_rel(a, topic, self.SIBLING_REL)
							print "adding: ", a
							self.NODE(batch, a, self.ARTICLE)
							num += 1
							if depth > 0:
								print "ENQUEUING", a
								enqueue(a)
						for c in result['categories']:
							self.incr_rel(a, topic, self.CATEGORY_REL)
							self.NODE(batch, c, self.CATEGORY)
							num += 1
					elif result['type'] == self.DISAMBIGUATION:
						for a in result['links']:
							self.incr_rel(a, topic, self.DISAMB_REL)
							self.NODE(batch, a, self.DISAMBIGUATION)
							num += 1
				if num >= BATCH_LIM:
					batch.submit()
					batch.clear()
					num = 0
		if num > 0:
			self.submit_batch(batch)
			num = 0
		print "FINISHED WITH THE NODES..."
		for k in self.fdb.smembers(self.rel_key):
			print "REL:", k
			nodes = k.split(":", 2)
			if len(nodes) != 3:
				print "bad...rel"
				continue
			rel = nodes[0]
			n1 = self.node_index.get('name', nodes[1])
			n2 = self.node_index.get('name', nodes[2])
			if n1 and n2:
				n1 = n1[0]
				n2 = n2[0]
			else:
				print "no nodes..."
				continue
			REL(batch, n1, rel, 1, n2)
			num += 1

			if num >= BATCH_LIM:
				self.submit_batch(batch)
				num = 0
		if num > 0:
			self.submit_batch(batch)
			num = 0
		print "DONE>>>>>>>>>>>>>>>"

	def add_disambiguation(self, a):
		ex = Extractor()
		ls = ex.getDisambiguationLinks(a + '_(disambiguation)')
		if ls:
			anode = self.graphdb.get_or_create_indexed_node(self.DISAMBIGUATION, 'name', a, {'name': a, 'class': self.DISAMBIGUATION})
			for l in ls:
				print "disambiguation link:", l
				lnode = self.graphdb.get_indexed_node('NODE', 'name', l)
				if lnode:
					print "creating disamb relation betn", a, ", ", l
					self.graphdb.create((anode, self.DISAMBIGUATION, lnode, {'class': self.DISAMBIGUATION, 'weight': 1}))

	def add_synset(self, word):
		ex = Extractor()
		word_id = md5.md5(word).hexdigest()
		if not self.fdb.get(word_id):
			self.fdb.set(ROOT + word_id, word)
		synset = ex.getWikiBacklinks(word)
		if synset:
			for synonym in synset:
				self.fdb.set(SYN + synonym.upper(), word_id)
