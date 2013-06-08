import requests
import lxml.html
from StringIO import StringIO
from unidecode import unidecode
from Parser import Parser
import urllib2
import re
class Extractor:
	def __init__(self):
		self.blacklist = ['article', 'wikipedia', 'wiki', 'birth', 'people from', 'from', 'category', 'categories', 'pages', '.php']
		pass

	def createUrl(self, topic, prop):
		return 'http://en.wikipedia.org/w/api.php?action=parse&page=' + topic.replace(' ', '+') + '&prop=' + prop + '&format=json&redirects'

	def extract(self, topic):
		cat = requests.get(self.createUrl(topic, 'categories'))
		cj = cat.json()
		catlist = []
		for k in cj['parse']['categories']:
			c = k['*']
			clean_c = self.clean(c)
			if self.contains(clean_c, self.blacklist): pass
			else: catlist.append(clean_c)
		r = requests.get(self.createUrl(topic, 'text'))
		j = r.json()
		text = j['parse']['text']['*']
		tree = lxml.html.parse(StringIO(unidecode(text)))
		l = tree.xpath("//p/text()|//p/a/text()|//p/b/text()|//p/i/text()|//p/i/a/text()|//p/b/a/text()")
		alist = tree.xpath("//p/b/a/@href|//p/a/@href|//p/i/a/@href")
		atextlist = tree.xpath("//p/b/a/text()|//p/a/text()|//p/i/a/text()")
		cleanalist = set()
		for a, txt in zip(alist, atextlist):
			if self.containsCapitals(txt):
				cleanalist.add(self.clean(a))
			else:
				cleanalist.add(self.clean(a).lower())
		s = reduce(lambda x, y: x + ' ' + y, l)
		s = self.clean(s)
		p = Parser()
		m, k, d = p.parseText(s)
		n = set()
		for b in m:
			found = False
			for a in cleanalist:
				if a.rfind(b) >= 0:
					found = True
					break
			if not found: n.add(b)
		return sorted(set.union(n, cleanalist)), set(catlist), set(cleanalist)

	def clean(self, s):
		if type(s) == unicode:
			s = unidecode(s)
		else:
			s = str(s)
		s = urllib2.unquote(s)
		s = re.sub(r'/wiki/', '', s)
		s = re.sub(r'_', ' ', s)
		return s

	def contains(self, s, l):
		for i in l:
			if s.lower().rfind(i.lower()) >= 0:
				return True
		return False


	def containsCapitals(self, s):
		for i in s:
			if 65 <= ord(i) <= 90:
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
