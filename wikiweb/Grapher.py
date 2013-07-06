from py2neo import neo4j, cypher
import os
from urlparse import urlparse

class Grapher:
	def __init__(self):
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
		self.topic_index = self.graphdb.get_or_create_index(neo4j.Node, "topic")
		self.category_index = self.graphdb.get_or_create_index(neo4j.Node, "category")

	def getRelatedNodes(self, topic):
		topic = topic.replace(' ', '_')
		query = "start n = node(*) match n-[r1:sibling]-m1 where has(n.name) and n.name = '{0}' return m1.name order by r1.weight desc".format(topic)
		data, metadata = cypher.execute(self.graphdb, query)
		return data
