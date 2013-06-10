import requests
import lxml.html
from StringIO import StringIO
from unidecode import unidecode
from Parser import Parser
import urllib2
import re

class Extractor:
	def __init__(self):
		self.blacklist = ['article', 'wikipedia', 'wiki', 'birth', 'people from', 'from', 'category', 'categories', 'pages', '.php', 'stubs', 'death', 'people', 'template']
		pass

	def getAPIdata(self, topic, prop):
		try:
			url = 'http://en.wikipedia.org/w/api.php?action=parse&page=' + topic.replace(' ', '+') + '&prop=' + prop + '&section=0&format=json&redirects'
			result_json = requests.get(url).json()
			return result_json['parse'][prop]
		except KeyError:
			print "no {0} data for name {1}".format(prop, topic)
			return None
		except requests.ConnectionError:
			print "failed to connect for {0} for name {1}".format(prop, topic)
			return None

	def extract(self, topic):
		keyword_set = set()
		category_set = set()
		link_set = set()

		#categories
		category_json = self.getAPIdata(topic, 'categories')
		if category_json:
			for k in category_json:
				clean_c = self.clean(k['*'])
				if self.contains(clean_c, self.blacklist): pass
				else: category_set.add(clean_c)

		#text
		text_json = self.getAPIdata(topic, 'text')
		if text_json:
			text = text_json['*']
			tree = lxml.html.parse(StringIO(unidecode(text)))
			l = tree.xpath("//p/text()|//p/a/text()|//p/b/text()|//p/i/text()|//p/i/a/text()|//p/b/a/text()")
			alist = tree.xpath("//p/b/a/@href|//p/a/@href|//p/i/a/@href")
			for a in alist:
				clean_a = self.clean(a)
				if self.contains(clean_a, self.blacklist): pass
				else: link_set.add(clean_a.lower())
			s = self.clean(reduce(lambda x, y: x + ' ' + y, l))
			p = Parser()
			m, k, d = p.parseText(s)
			n = set()
			for b in m:
				found = False
				for a in link_set:
					if a.rfind(b) >= 0:
						found = True
						break
				if not found: n.add(b)
			keyword_set = set.union(n, link_set)
		
		return keyword_set, category_set, link_set

	def clean(self, s):
		if type(s) == unicode:
			s = unidecode(s)
		else:
			s = str(s)
		s = urllib2.unquote(s)
		s = re.sub(r'/wiki/', '', s)
		s = re.sub(r'_', ' ', s)
		s = re.sub(r'#.*', '', s)
		return s

	def contains(self, s, l):
		for i in l:
			if s.lower().rfind(i.lower()) >= 0:
				return True
		return False


	def containsCapitals(self, s):
		for i in s:
			if ord('A') <= ord(i) <= ord('Z'):
				return True
		return False

	def getType(self, topic):
		tags = topic
		pdict = {}
		for t in tags:
			parents = getParents(t)
			for p in parents:
				if pdict.has_key(p): pdict[p] += 1
				else: pdict[p] = 1
		first = sorted(pdict, key = lambda x: pdict[x], reverse = True)[0]
		print first, pdict[first]
