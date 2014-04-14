import requests
import json
from py2neo import neo4j, cypher
import os
from util import Util
from reldatastore import RelDataStore
from fastdatastore import FastDataStore
from constants import *
from urlparse import urlparse
from math import *
from extractor import Extractor
from parser import Parser

class Learner(Util):
	def __init__(self):
		'''
		initializes:
		1. graph database connection
		2. datastore connection
		3. graph database indices required
		4. url and templates for interaction with the graph database REST API
		'''
		Util.__init__(self)
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
		self.node_index = self.graphdb.get_or_create_index(neo4j.Node, 'NODE')
		self.disambiguation_index = self.graphdb.get_or_create_index(neo4j.Node, self.DISAMBIGUATION)
		self._url = lambda present_node: 'http://localhost:7474/db/data/node/{0}'.format(present_node)
		self._template = lambda target_node: {
			"to" : self._url(target_node),
			"relationships": {
				"type": "sibling"
			},
			"cost_property": "weight",
			"algorithm" : "dijkstra"
		}
		self.DataM = RelDataStore()

	def get_all_meanings(self, word):
		'''
		Get all meanings as assigned by the disambiguation index (should be very fast! approx O(1) hopefully)
		If that fails, get all meanings given by the following regex: <word>*
		If even that fails, get all meanings fuzzily equal to <word> using Levenshtein distance or soundex
		If even THAT fails, return an error saying no meanings and ask the user what the hell he meant to say

		word => string keyword to get all possible neo4j objects for
		'''
		print "WORD:", word
		data, metadata = cypher.execute(self.graphdb, 'start n=node:%s(name="%s") match n-[]-m return m' % (self.DISAMBIGUATION, word))
		if data:
			print data
			return [d[0] for d in data]
		res = self.disambiguation_index.query("name:%s~" % word)
		if res:
			print res
			return [d[0] for d in data]
		res = self.disambiguation_index.query("name:%s*" % word)
		if res:
			print res
			return [d[0] for d in data]
		data, metadata = cypher.execute(self.graphdb, 'START root=node(*) WHERE root.name=~".*%s.*" RETURN root' % word)
		if data:
			print data
			return [d[0] for d in data]
		return []

	def get_syn_root(self, word):
		''' return the root node corresponding to the synonym word '''
		print word
		word = word.upper().replace(' ', '_')
		fdb = FastDataStore()
		word_id = fdb.get(SYN + word)
		if not word_id: return None
		else: return fdb.get(ROOT + word_id)

	def disambiguate(self, precise, vague, history = None, return_format = neo4j.Node):
		'''
		disambiguate will try to disambiguate the keywords in vague based on the following information in order
		1. the values in precise
		2. if that fails, the values already present in uid's interests in the datastore
		3. if even that fails, random choice

		precise => list of neo4j.Node objects
		vague => list of string objects to be converted into neo4j.Node objects
		'''
		getnode = lambda x: self.graphdb.get_indexed_node('NODE', 'name', x)
		new_vague = []
		resolved = []
		for word in vague:
			#try trivial synsets
			root = self.get_syn_root(word)
			if root:
				resolved.append(getnode(root))
				continue

			root = getnode(word)
			if root:
				resolved.append(root)
				continue
			new_vague.append(word)

		if not new_vague:
			if return_format == str and resolved:
				resolved = [x['name'] for x in resolved]
			return resolved
			
		#first make list of precise node objects (by default already there)
		precise_nodes = []
		for p in precise:
			if type(p) == neo4j.Node:
				precise_nodes.append(p)
			else:
				n = getnode(p)
				if not n: new_vague.append(p)
				else: precise_nodes.append(n)

		#then start the steps of disambiguation
		for word in new_vague:
			#try all possible meanings via disambiguation index
			meaning_nodes = self.get_all_meanings(word)
			if meaning_nodes and precise_nodes:
				print "CHECKING CONTEXT"
				#a disambiguation node exists for this word
				scores = [{'node': meaning_node, 'dist': self.graph_distance([meaning_node], precise_nodes)} for meaning_node in meaning_nodes]
				print [(x['node']['name'], x['dist']) for x in scores]
				min_dist = min(scores, key = lambda x: x['dist'])['dist']
				minlist = [{'node': x['node'], 'deg': self.get_degree(x['node'])} for x in scores if x['dist'] == min_dist]
				node = max(minlist, key = lambda x: x['deg'])['node']
				print "resolved: ", node['name']
				resolved.append(node)
				continue

			if history:
				print "CHECKING HISTORY"
				history_nodes = [getnode(x['interest']) for x in history]
				#a disambiguation node exists for this word
				scores = [{'node': meaning_node, 'dist': self.graph_distance([meaning_node], history_nodes)} for meaning_node in meaning_nodes]
				min_dist = min(scores, key = lambda x: x['dist'])['dist']
				minlist = [{'node': x['node'], 'deg': self.get_degree(x['node'])} for x in scores if x['dist'] == min_dist]
				node = max(minlist, key = lambda x: x['deg'])['node']
				resolved.append(node)
				continue

			if meaning_nodes:
				resolved.append(meaning_nodes[0])

		if return_format == str and resolved:
			resolved = [x['name'] for x in resolved]

		print "resolved:", resolved
		return resolved

	def get_degree(self, node):
		data, metadata = cypher.execute(self.graphdb, 'start n=node:%s(name="%s") match n-[]-m return count(m)' % ('NODE', node['name']))
		return data[0][0]
		
	def get_shortest_path(self, n1, n2):
		'''least cost path from n1 to n2. Type of n1, n2 = neo4j.Node'''
		res = requests.post(self._url(n1._id) + '/path', data = json.dumps(self._template(n2._id)))
		res_json = res.json()
		if res.status_code == requests.codes.ok:
			#print res_json
			return res_json['length'] + 1
		else:
			return self.INF

	def graph_distance(self, target_nodes, present_nodes):
		'''
		target_nodes is a vector (lists) of node objects whose cumulative score is to be determined
		present_nodes is a vector of <Node Object>s
		'''
		#target_nodes = [self.graphdb.get_indexed_node('NODE', 'name', x) for x in target]
		#present_nodes = [self.graphdb.get_indexed_node('NODE', 'name', x) for x in present]
		score_1 = 0
		score_2 = 0
		for tnode in target_nodes:
			l = self.INF
			for pnode in present_nodes:
				dist = self.get_shortest_path(tnode, pnode)
				if l > dist: l = dist
			if l != self.INF: score_1 += l
		score_1 /= float(len(target_nodes))
		for pnode in present_nodes:
			l = self.INF
			for tnode in target_nodes:
				dist = self.get_shortest_path(tnode, pnode)
				if l > dist: l = dist
			if l != self.INF: score_2 += l
		score_2 /= float(len(present_nodes))
		return (score_1 + score_2) / float(2)

	def score_all(self, key, uid, kwlist):
		'''
		score all keywords together
		'''
		ret, length = self.DataM.get_interests_for_user_for_key(key, uid, interest_types = (SUPPLIED, GENERATED))
		print ret
		getnode = lambda x: self.graphdb.get_indexed_node('NODE', 'name', x)
		precise = []
		vague = []
		#precise => list of (neo4j.Node, interest_level) objects
		#vague => list of (string, interest_level) objects to be converted into a neo4j.Node
		print kwlist
		for kw in kwlist:
			n = self.graphdb.get_indexed_node(self.DISAMBIGUATION, 'name', kw)
			if n:
				vague.append(kw)
			else:
				m = getnode(kw)
				if m:
					precise.append(m)
				else:
					vague.append(kw)
		print "vague: ", vague
		print "precise: ", precise
		if vague:
			precise = self.disambiguate(precise, vague, ret)
		#precise now contains all nodes corresponding to the given keywords
		print "FINAL PRECISE:", precise
		s = self.graph_distance(precise, [getnode(x['interest']) for x in ret])
		return 1 / float(s)

	def get_related(self, word, limit = 10, return_format = str):
		'''returns top <limit> nodes most closely related to <word>'''
		data, metadata = cypher.execute(self.graphdb, 'start n=node:NODE(name="%s") match n-[r:sibling]-m return m, r.weight order by r.weight desc limit %d' % (word, limit))
		if data:
			if return_format == str:
				return sorted([(self._encode_str(d[0]['name']), d[1]) for d in data])
			elif return_format == neo4j.Node:
				return sorted([(d[0], d[1]) for d in data], key = lambda x: x[0])
		else:
			return None

	def getSemanticDistance(self, a, b):
		na = self.graphdb.get_indexed_node('NODE', 'name', a)
		nb = self.graphdb.get_indexed_node('NODE', 'name', b)
		if na and nb:
			return self.get_shortest_path(na, nb)
		else:
			return -1

	def extract_keyphrases(self, data, type = "text"):
		p = Parser()
		if type == "text":
			return list(p.parseText(data)[0])
		elif type == "url":
			return list(p.parseURLText(data)[0])

	def getURLText(self, url):
		p = Parser()
		return p.getURLText(url)
