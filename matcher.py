import requests
class Matcher:
	def __init__(self):
		self.INF = 9999
		self.url = lambda present_node: 'http://localhost:7474/db/data/node/{0}'.format(present_node)
		self.template = lambda target_node: {
			"method" : "POST",
			"to" : "/node/{0}",
			"algorithm" : "shortestPath".format(target_node)
		}

	def score(graphdb, target, present):
		'''target and present are two vectors (lists) of keywords'''
		target_nodes = [graphdb.get_indexed_node('topic', 'name', x) for x in target]
		present_nodes = [graphdb.get_indexed_node('topic', 'name', x) for x in present]
		score = 0
		for tnode in target_nodes:
			l = self.INF
			for pnode in present:
				try:
					res = requests.post(self.url(pnode._id), data = self.template(pnode._id))
					if res.status_code == requests.code.server_error:
						pass
					elif res.status_code == requests.code.not_found:
						pass
					elif res.status_code == requests.code.ok:
						res_json = res.json()
						if l > len(res_json['nodes']): l = len(res_json['nodes'])
				except Exception as e:
					print "score: ", e
					print target, ", ", present
			if l != self.INF: score += l
		return score
