from unidecode import unidecode
import re
import urllib2
class Util:
	def __init__(self):
		self.blacklist = ['article', 'wikipedia', 'wiki', 'birth', 'people from', 'from', 'category', 'categories', 'pages', '.php', 'stubs', 'death', 'people', 'template', 'wiktio', 'en.', 'file', 'help']
		self.CATEGORY = 'category'
		self.ARTICLE = 'topic'
		self.DISAMBIGUATION = 'disambiguation'
		self.SIBLING_REL = 'sibling'
		self.CATEGORY_REL = 'parent'
		self.DISAMB_REL = 'disambiguation'
		self.INF = 9999

	def _contains(self, s, l):
		for i in l:
			if s.lower().rfind(i.lower()) >= 0:
				return True
		return False

	def _clean(self, s):
		if type(s) == unicode:
			s = unidecode(s)
		else:
			s = unidecode(s.decode("utf-8", "ignore"))
		s = urllib2.unquote(s)
		s = re.sub(r'/wiki/', '', s)
		s = re.sub(r'_', ' ', s)
		s = re.sub(r'#.*', '', s)
		return s

	def _encode_str(self, s):
		if type(s) == unicode:
			return unidecode(s)
		else:
			return unidecode(s.decode("utf-8", "ignore"))
