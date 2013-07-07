import requests
import json
from py2neo import neo4j, cypher
import os
from util import Util
from reldatastore import RelDataStore
from fastdatastore import FastDataStore
from constants import *
from urlparse import urlparse

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
			return [d[0]['name'] for d in data], [d[0] for d in data]
		res = self.disambiguation_index.query("name:%s~" % word)
		if res:
			return [d[0]['name'] for d in res if d[0]], [d[0] for d in data]
		res = self.disambiguation_index.query("name:%s*" % word)
		if res:
			return [d[0]['name'] for d in res if d[0]], [d[0] for d in data]
		data, metadata = cypher.execute(self.graphdb, 'START root=node(*) WHERE root.name=~".*%s.*" RETURN root' % word)
		if data:
			return [d[0]['name'] for d in data], [d[0] for d in data]
		return [], []

	def get_syn_root(self, word):
		''' return the root node corresponding to the synonym word '''
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

		precise => list of (neo4j.Node, interest_level) objects
		vague => list of (string, interest_level) objects to be converted into (neo4j.Node, interest_level) objects
		'''
		new_vague = []
		for word, interest_level in vague:
			print "syn: ", word
			#try trivial synsets
			root = self.get_syn_root(word)
			if root:
				print "root: ", root
				node = getnode(root)
				resolved.append((node, interest_level))
			else:
				new_vague.append((word, interest_level))

		if not new_vague:
			if return_format == str and resolved:
				resolved = [(x[0]['name'], x[1]) for x in resolved]
			return resolved
			
		getnode = lambda x: self.graphdb.get_indexed_node('NODE', 'name', x)
		#first make list of precise node objects (by default already there)
		precise_nodes = []
		for p, interest in precise:
			if type(p) == neo4j.Node:
				precise_nodes.append((p, interest))
			else:
				n = getnode(p)
				if not n: return None
				else: precise_nodes.append((n, interest))

		#then start the steps of disambiguation
		resolved = []
		for word, interest_level in new_vague:
			print 'vague word: ', word
			
			#try all possible meanings via disambiguation index
			meanings, meaning_nodes = self.get_all_meanings(word)
			if meanings and meaning_nodes and precise_nodes:
				#a disambiguation node exists for this word
				scores = []
				for meaning, meaning_node in zip(meanings, meaning_nodes):
					scores.append((meaning_node, self.graph_distance([(meaning_node, interest_level)], precise_nodes)))
				min_score = min(scores, key = lambda x: x[1])[1]
				minlist = [(x[0], self.get_degree(x[0])) for x in scores if x[1] == min_score]
				resolved_meaning = max(minlist, key = lambda x: x[1])
				node = resolved_meaning[0]
				resolved.append((node, interest_level))
				continue

			if history:
				print "CHECKING HISTORY"
				history_nodes = [(getnode(x['interest']), x['interest_level']) for x in history]
				#a disambiguation node exists for this word
				scores = []
				for meaning, meaning_node in zip(meanings, meaning_nodes):
					scores.append((meaning_node, self.graph_distance([(meaning_node, interest_level)], history_nodes)))
				min_score = min(scores, key = lambda x: x[1])[1]
				minlist = [(x[0], self.get_degree(x[0])) for x in scores if x[1] == min_score]
				resolved_meaning = max(minlist, key = lambda x: x[1])
				node = resolved_meaning[0]
				resolved.append((node, interest_level))
				continue

			if meanings and meaning_nodes:
				resolved.append((meaning_nodes[0], interest_level))

		if return_format == str and resolved:
			resolved = [(x[0]['name'], x[1]) for x in resolved]

		return resolved

	def get_degree(self, node):
		data, metadata = cypher.execute(self.graphdb, 'start n=node:%s(name="%s") match n-[]-m return count(m)' % ('NODE', node['name']))
		return data[0][0]
		
	def get_shortest_path(self, n1, n2):
		'''least cost path from n1 to n2. Type of n1, n2 = neo4j.Node'''
		print n1, n2
		print n1['name'], n2['name']
		res = requests.post(self._url(n1._id) + '/path', data = json.dumps(self._template(n2._id)))
		res_json = res.json()
		if res.status_code == requests.codes.ok:
			#print res_json
			return res_json['weight'] + 1
		else:
			return self.INF

	def updateGraph(node_a, node_b, inc_a = 1, inc_b = 0, inc_ab = 0):
		'''
		wt_ab = [wt_ab * (wt_a + wt_b) + inc_ab * (wt_ab + 1)] / [wt_a + wt_b + (inc_a + inc_b - inc_ab) * (wt_ab + 1)]
		wt_a = wt_a + inc_a
		wt_b = wt_b + inc_b
		'''
		if not node_a: return False
		if node_b:
			#therefore, the a-b relationship has to be updated in a more special manner
			cypher.execute("""
					start n=node:NODE(name=%s), m=node:NODE(name=%s)
					match n-[r:sibling]-m
					set r.weight = [r.weight * (n.weight + m.weight) + %d * (r.weight + 1)] / [n.weight + m.weight + (%d + %d - %d) * (r.weight + 1)]""" % (node_a, node_b, inc_ab, inc_a, inc_b, inc_ab))
			#update b's relationships as well, dont touch its relationship with a
			cypher.execute("""
					start n=node:NODE(name=%s),
					match n-[r:sibling]-m
					where m.name != %s
					set r.weight = r.weight * (n.weight + m.weight) / [n.weight + m.weight + r.weight + 1]
					""" % (node_b, node_a))
			#update a's relationships as well, dont touch its relationship with b
			cypher.execute("""
					start n=node:NODE(name=%s),
					match n-[r:sibling]-m
					where m.name != %s
					set r.weight = r.weight * (n.weight + m.weight) / [n.weight + m.weight + r.weight + 1]
					""" % (node_a, node_b))
			#update a and b weights
			cypher.execute("""
					start n=node:NODE(name=%s), m=node:NODE(name=%s)
					set n.weight = n.weight + %d
					set m.weight = m.weight + %d
					""" % (node_a, node_b, inc_a, inc_b))
		else:
			#only update a's relationships
			cypher.execute("""
				start n=node:NODE(name=%s),
				match n-[r:sibling]-m
				set r.weight = r.weight * (n.weight + m.weight) / [n.weight + m.weight + r.weight + 1]
				""" % (node_a,))
			cypher.execute("""
					start n=node:NODE(name=%s)
					set n.weight = n.weight + %d
					""" % (node_a, inc_a))


	def graph_distance(self, target_nodes, present_nodes):
		'''
		target_nodes is a vector (lists) of node objects whose cumulative score is to be determined
		present_nodes is a vector of tuples of the form (<Node Object>, <interest level>)
		'''
		#target_nodes = [self.graphdb.get_indexed_node('NODE', 'name', x) for x in target]
		#present_nodes = [self.graphdb.get_indexed_node('NODE', 'name', x) for x in present]
		score_1 = 0
		score_2 = 0
		print "TN:", target_nodes
		print "PN:", present_nodes
		for tnode, tinterest in target_nodes:
			l = self.INF
			for pnode, pinterest in present_nodes:
				dist = self.get_shortest_path(tnode, pnode) / float(tinterest)
				if l > dist: l = dist
			if l != self.INF: score_1 += l
		score_1 /= float(len(target_nodes))
		for pnode, pinterest in present_nodes:
			l = self.INF
			for tnode, tinterest in target_nodes:
				dist = self.get_shortest_path(tnode, pnode) / float(pinterest)
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
				vague.append((kw, 1))
			else:
				m = getnode(kw)
				if m:
					precise.append((m, 1))
				else:
					vague.append((kw, 1))
		print "vague: ", vague
		print "precise: ", precise
		if vague:
			precise = self.disambiguate(precise, vague, ret)
		#precise now contains all nodes corresponding to the given keywords
		print "FINAL PRECISE:", precise
		s = self.graph_distance(precise, [(getnode(x['interest']), x['interest_level']) for x in ret])
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
