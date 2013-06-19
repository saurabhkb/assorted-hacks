import requests
import json
from py2neo import neo4j
from util import Util

class Matcher(Util):
	def __init__(self):
		Util.__init__(self)
		self.url = lambda present_node: 'http://localhost:7474/db/data/node/{0}'.format(present_node)
		self.template = lambda target_node: {
			"to" : self.url(target_node),
			"cost_property": "weight",
			"algorithm" : "dijkstra"
		}
		self.template = lambda target_node: {
			"to" : self.url(target_node),
			"max_depth": 5,
			"algorithm" : "shortestPath"
		}

	def wiki_disambiguate(self, word):
		'''disambiguate @word'''
		url = 'http://en.wikipedia.org/w/api.php?action=parse&prop=links&format=json&page={0}_(disambiguation)&redirects'.format(word)
		res = requests.get(url)
		res_json = res.json()
		try:
			return [self._clean(x['*']) for x in res_json['parse']['links'] if not self._contains(x['*'], self.blacklist)]
		except Exception as e:
			print e
			return []

	def get_shortest_path(self, n1, n2):
		'''least cost path from n1 to n2'''
		res = requests.post(self.url(n1._id) + '/path', data = json.dumps(self.template(n2._id)))
		if res.status_code == requests.codes.ok:
			return len(res_json['nodes'])
		else:
			print res.status_code
			print res.text
			return self.INF

	def score(self, graphdb, target, present):
		'''target and present are two vectors (lists) of keywords'''
		target_nodes = [graphdb.get_indexed_node(self.ARTICLE, 'name', x) for x in target]
		present_nodes = [graphdb.get_indexed_node(self.ARTICLE, 'name', x) for x in present]
		score_1 = 0
		score_2 = 0
		for tnode in target_nodes:
			l = self.INF
			for pnode in present_nodes:
				dist = get_shortest_path(tnode, pnode)
				if l > dist: l = dist
			if l != self.INF: score_1 += l
		score_1 /= float(len(target))
		for pnode in present_nodes:
			l = self.INF
			for tnode in target_nodes:
				dist = get_shortest_path(tnode, pnode)
				if l > dist: l = dist
			if l != self.INF: score_2 += l
		score_2 /= float(len(present))
		return score_1 + score_2


m = Matcher()
#print m.wiki_disambiguate('Ring')
#g = neo4j.GraphDatabaseService()
#print "HFD"
#print m.score(g, ['Google', 'Motorola Mobility'], ['Facebook'])
