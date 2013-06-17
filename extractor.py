import requests
import lxml.html
from StringIO import StringIO
import traceback
from util import Util


class Extractor(Util):
	def __init__(self):
		Util.__init__(self)

	def getWikiCategories(self, topic):
		topic_url = topic.replace(' ', '+')
		url = 'http://en.wikipedia.org/w/api.php?action=parse&page=' + topic_url + '&prop=categories&format=json&redirects'
		category_json = requests.get(url).json()
		category_set = set()
		for k in category_json['parse']['categories']:
			category_set.add(self._clean(k['*']))
		return category_set
	
	def getWikiLinks(self, topic):
		topic_url = topic.replace(' ', '+')
		url = 'http://en.wikipedia.org/w/api.php?action=parse&page=' + topic_url + '&prop=links&section=0&format=json&redirects'
		result_json = requests.get(url).json()
		link_set = set()
		for l in result_json['parse']['links']:
			link_set.add(self._clean(l['*']))
		return link_set

	def extract(self, topic):
		TYPE = self.ARTICLE	#default
		if topic.startswith('Category'):
			TYPE = self.CATEGORY
			return {'type': TYPE, 'links': None, 'categories': None}
		else:
			cat = self.getWikiCategories(topic)
			if cat.intersection(set(['All_article_disambiguation_pages', 'All_disambiguation_pages', 'Disambiguation_pages'])):
				TYPE = self.DISAMBIGUATION
			links = self.getWikiLinks(topic)
			cat1 = [x for x in cat if not self._contains(x, self.blacklist)]
			links1 = [x for x in links if not self._contains(x, self.blacklist)]
			return {'type': TYPE, 'links': links1, 'categories': cat1}
