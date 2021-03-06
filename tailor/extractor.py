# -*- coding: utf-8 -*-
import requests
import traceback
from util import Util


class Extractor(Util):
	def __init__(self):
		Util.__init__(self)
		self.blacklist += ['by country', 'by area', 'by region', 'by continent', 'user:', 'portal:', 'talk', 'name']

	def getWikiBacklinks(self, topic, filter = "redirects"):
		topic_url = topic.replace(' ', '+')
		url = 'http://en.wikipedia.org/w/api.php?action=query&list=backlinks&bltitle=' + topic_url + '&bllimit=max&blfilterredir=' + filter + '&format=json'
		backlink_set = set()
		try:
			backlink_json = requests.get(url).json()
			for k in backlink_json['query']['backlinks']:
				if self._contains(k['title'], self.blacklist):
					pass
				else: backlink_set.add(self._clean(k['title']))
		except Exception as e:
			print "getWikiBacklinks ERROR: ", e
		return backlink_set
	
	def getWikiCategories(self, topic):
		topic_url = topic.replace(' ', '+')
		url = 'http://en.wikipedia.org/w/api.php?action=parse&page=' + topic_url + '&prop=categories&format=json&redirects'
		category_set = set()
		try:
			category_json = requests.get(url).json()
			for k in category_json['parse']['categories']:
				if self._contains(k['*'], self.blacklist): pass
				else: category_set.add(self._clean(k['*']))
		except Exception as e:
			print "getWikiCategories ERROR: ", e
		return category_set
	
	def getWikiLinks(self, topic):
		topic_url = topic.replace(' ', '+')
		url = 'http://en.wikipedia.org/w/api.php?action=parse&page=' + topic_url + '&prop=links&section=0&format=json&redirects'
		link_set = set()
		try:
			result_json = requests.get(url).json()
			for l in result_json['parse']['links']:
				if self._contains(l['*'], self.blacklist): pass
				else: link_set.add(self._clean(l['*']))
		except Exception as e:
			print "getWikiLinks ERROR: ", e
		return link_set

	def getDisambiguationLinks(self, topic):
		topic_url = topic.replace(' ', '+')
		url = 'http://en.wikipedia.org/w/api.php?action=parse&page=' + topic_url + '&prop=links&format=json&redirects'
		link_set = set()
		try:
			result_json = requests.get(url).json()
			for l in result_json['parse']['links']:
				if self._contains(l['*'], self.blacklist): pass
				else: link_set.add(self._clean(l['*']))
		except Exception as e:
			print "getWikiLinks ERROR: ", e
		return link_set


	def getAllFromCategory(self, category):
		cat_url = category.replace(' ', '+')
		url = 'http://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:{0}&cmlimit=max&cmtype=page|subcat&format=json&redirects'.format(cat_url)
		page_set = set()
		cat_set = set()
		try:
			result_json = requests.get(url).json()
			for elem in result_json['query']['categorymembers']:
				if elem['title'].startswith('Category'):
					title = elem['title'].split(':')[1]
					if self._contains(title, self.blacklist): pass
					else: cat_set.add(self._clean(elem['title'].split(':')[1]))
				else:
					if self._contains(elem['title'], self.blacklist): pass
					else: page_set.add(self._clean(elem['title']))
		except Exception as e:
			print "getAllFromCategory ERROR: ", e
		return {'pages': page_set, 'categories': cat_set}

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
