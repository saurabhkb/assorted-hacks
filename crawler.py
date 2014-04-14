from extractor import Extractor
import os
from py2neo import neo4j, cypher
from urlparse import urlparse
from util import Util
import sys
import md5
from fastdatastore import FastDataStore
from math import log

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
		self.BATCH_LIM = 50
		self.counter = 0
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
	
	def updateBatch(self, b, type = neo4j.Node, node = None, rel = None):
		def submit_batch():
			tries = self.max_tries
			while tries > 0:
				try:
					b.submit()
					b.clear()
					self.counter = 0
					return True
				except Exception as e:
					print e
				tries -= 1
			return False	
		if type == neo4j.Node and node:
			b.get_or_create_indexed_node(self.node_index, 'name', node['name'], {'name': node['name'], 'class': node['class']})
		elif type == neo4j.Relationship and rel:
			b.get_or_create((rel['node1'], rel['rel'], rel['node2'], {'class': rel['rel'], 'weight': rel['weight']}))
		else: return submit_batch()

		self.counter += 1
		if self.counter > self.BATCH_LIM:
			return submit_batch()

			
	def spider(self, root, pages = True, subcategories = True, action = "traverse", preclean = False, depth = 1):
		if preclean: self.graphdb.clear()
		seen_key = "URL_SEEN"
		queue_key = "URL_QUEUE"
		ex = Extractor()
		batch = neo4j.WriteBatch(self.graphdb)

		queue_empty = lambda: self.fdb.scard(queue_key) == 0
		seen = lambda x: self.fdb.sismember(seen_key, x)
		visit = lambda x: self.fdb.sadd(seen_key, x)
		dequeue = lambda: self.fdb.spop(queue_key)
		enqueue = lambda x: self.fdb.sadd(queue_key, self._encode_str(x))

		if action == "traverse":
			enqueue(root)
			while not queue_empty():
				current = dequeue()
				print current
				if current and current.strip() and not seen(current):
					visit(current)
					result = ex.getAllFromCategory(current)
					self.updateBatch(batch, type = neo4j.Node, node = {'name': current, 'class': self.CATEGORY})
					if pages:
						for page in result['pages']:
							print "{0}\tp:{1}".format(current[:15], page)
							self.incr_rel(page, current, self.CATEGORY_REL)
							self.updateBatch(batch, type = neo4j.Node, node = {'name': page, 'class': self.ARTICLE})
							links = ex.getWikiLinks(page)
							for a in links:
								print "{0}\tp:{1}\t{2}".format(current[:15], page, a)
								self.incr_rel(a, page, self.SIBLING_REL)
								self.updateBatch(batch, type = neo4j.Node, node = {'name': a, 'class': self.ARTICLE})
					if subcategories:
						for subcat in result['categories']:
							print "{0}\tc:{1}".format(current, subcat)
							self.incr_rel(subcat, current, self.SUBCAT_REL)
							self.updateBatch(batch, type = neo4j.Node, node = {'name': subcat, 'class': self.CATEGORY})
							enqueue(subcat)
		elif action == "crawl":
			enqueue(root)
			while not queue_empty():
				topic = dequeue()
				if topic and topic.strip() and not seen(topic):
					visit(topic)
					result = ex.extract(topic)
					depth -= 1
					self.updateBatch(batch, type = neo4j.Node, node = {'name': topic, 'class': result['type']})
					if result['type'] == self.CATEGORY:
						pass
					elif result['type'] == self.ARTICLE:
						for a in result['links']:
							self.incr_rel(a, topic, self.SIBLING_REL)
							print "adding: ", a
							self.updateBatch(batch, type = neo4j.Node, node = {'name': a, 'class': self.ARTICLE})
							if depth > 0: enqueue(a)
						for c in result['categories']:
							self.incr_rel(a, topic, self.CATEGORY_REL)
							self.updateBatch(batch, type = neo4j.Node, node = {'name': c, 'class': self.CATEGORY})
					elif result['type'] == self.DISAMBIGUATION:
						for a in result['links']:
							self.incr_rel(a, topic, self.DISAMB_REL)
							self.updateBatch(batch, type = neo4j.Node, node = {'name': a, 'class': self.DISAMBIGUATION})
		print "FINISHED WITH THE NODES..."
		for k in self.fdb.smembers(self.rel_key):
			print "REL:", k
			try:
				nodes = k.split(":", 2)
				rel = nodes[0]
				n1 = self.node_index.get('name', nodes[1])[0]
				n2 = self.node_index.get('name', nodes[2])[0]
				self.updateBatch(batch, type = neo4j.Relationship, rel = {'node1': n1, 'rel': rel, 'weight': 1, 'node2': n2})
			except Exception as e:
				print "REL EXCEPTION: ", e
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

	def getWikiDist(self, a, b):
		a = a.replace(' ', '_')
		b = b.replace(' ', '_')
		e = Extractor()
		sa = e.getWikiBacklinks(a, filter = "nonredirects")
		sb = e.getWikiBacklinks(b, filter = "nonredirects")
		n1 = log(max(len(sa), len(sb)))
		n2 = log(len(set.intersection(sa, sb)))
		d1 = log(10 ** 7)
		d2 = log(min(len(sa), len(sb)))
		extra1 = extra2 = 0
		#if a in sb: extra1 = log(10 ** 7 / len(sb))
		#if b in sa: extra2 = log(10 ** 7 / len(sa))
		try:
			return (n1 - n2) / float(d1 - d2)
		except ZeroDivisionError as e:
			print e
			return self.INF
