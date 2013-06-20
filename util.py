from unidecode import unidecode
import re
import urllib2
class Util:
	def __init__(self):
		self.URL_BASE = "http://en.wikipedia.org/w/api.php"
		self.blacklist = ['article', 'wikipedia', 'wiki', 'birth', 'people from', 'from', 'category', 'categories', 'pages', '.php', 'stubs', 'death', 'people', 'template', 'wiktio', 'en.', 'file', 'help', 'stub']
		self.CATEGORY = 'category'
		self.ARTICLE = 'topic'
		self.DISAMBIGUATION = 'disambiguation'
		self.SIBLING_REL = 'sibling'
		self.CATEGORY_REL = 'parent'
		self.SUBCAT_REL = 'subcat'
		self.DISAMB_REL = 'disambiguation'
		self.INF = 9999

	def _contains(self, s, l):
		for i in l:
			if s.lower().rfind(i.lower()) >= 0:
				return True
		return False

	def _clean(self, s):
		s = self._encode_str(s)
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
