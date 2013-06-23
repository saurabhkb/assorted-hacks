import requests
import json
from py2neo import neo4j, cypher
import os
from util import Util
from datastore import DataStore
from constants import *

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
			"cost_property": "weight",
			"algorithm" : "dijkstra"
		}
		self.DataM = DataStore()

	def get_all_meanings(self, word):
		'''
		Get all meanings as assigned by the disambiguation index (should be very fast! approx O(1) hopefully)
		If that fails, get all meanings given by the following regex: <word>*
		If even that fails, get all meanings fuzzily equal to <word> using Levenshtein distance or soundex
		If even THAT fails, return an error saying no meanings and ask the user what the hell he meant to say
		'''
		data, metadata = cypher.execute(self.graphdb, 'start n=node:%s(name="%s") match n-[]-m return m' % (self.DISAMBIGUATION, word))
		if data: return [d[0]['name'] for d in data]
		data, metadata = cypher.execute(self.graphdb, 'match n
		res = self.disambiguation_index.query("name:%s~" % word)
		if res: return [d[0]['name'] for d in res]
		res = self.disambiguation_index.query("name:%s*" % word)
		if res: return res						#even more hopefully control should not reach here
		return None							#wasted time and computation and in the end a useless result

	def disambiguate(self, key, uid, precise, vague):
		'''
		disambiguate will try to disambiguate the keywords in vague based on the following information in order
		1. the values in precise
		2. if that fails, the values already present in uid's interests in the datastore
		3. if even that fails, random choice
		'''
		precise_nodes = [(self.graphdb.get_indexed_node('NODE', 'name', x), x['interest_level']) for x in ret]
		resolved = []
		for word in vague:
			meanings = self.get_all_meanings(word)
			scores = []
			for meaning in meanings:
				scores.append((meaning, self.graph_distance([(self.graphdb.get_indexed_node('NODE', 'name', x), 1) for x in precise])))
			resolved_meaning = min(scores, key = lambda x: x[1])[0]
			resolved.append(resolved_meaning)
		precise += resolved
		return precise

	def get_shortest_path(self, n1, n2):
		'''least cost path from n1 to n2'''
		res = requests.post(self._url(n1._id) + '/path', data = json.dumps(self._template(n2._id)))
		res_json = res.json()
		if res.status_code == requests.codes.ok:
			print res_json['weight']
			return res_json['length']
		else:
			print res.status_code
			print res.text
			return self.INF

	def graph_distance(self, target_nodes, present_nodes):
		'''
		target_nodes is a vector (lists) of node objects whose cumulative score is to be determined
		present_nodes is a vector of tuples of the form (<Node Object>, <interest level>)
		'''
		#target_nodes = [self.graphdb.get_indexed_node('NODE', 'name', x) for x in target]
		#present_nodes = [self.graphdb.get_indexed_node('NODE', 'name', x) for x in present]
		score_1 = 0
		score_2 = 0
		for tnode in target_nodes:
			l = self.INF
			for pnode in present_nodes:
				dist = self.get_shortest_path(tnode, pnode[0]) * pnode[1]
				if l > dist: l = dist
			if l != self.INF: score_1 += l
		score_1 /= float(len(target))
		for pnode in present_nodes:
			l = self.INF
			for tnode in target_nodes:
				dist = self.get_shortest_path(tnode, pnode[0]) * pnode[1]
				if l > dist: l = dist
			if l != self.INF: score_2 += l
		score_2 /= float(len(present))
		return (score_1 + score_2) / float(2)

	def score_all(self, key, uid, kwlist):
		'''
		score all keywords together
		'''
		precise = []
		vague = []
		ret, length = self.DataM.get_interests_for_user_for_key(key, uid, interest_types = (SUPPLIED, GENERATED))

		for kw in kwlist:
			n = self.graphdb.get_indexed_node('NODE', 'name', kw)
			if not n: vague.append(n)
			else: precise.append(n)
		if vague:
			precise = self.disambiguate(key, uid, precise, vague)
		#precise now contains all nodes corresponding to the given keywords
		s = self.graph_distance(precise, [(self.graphdb.get_indexed_node('NODE', 'name', x['interest']), x['interest_level']) for x in ret])
