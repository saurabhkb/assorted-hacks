import nltk
from lxml import etree
import re
import sys
import urllib2

class Parser:
	def __init__(self):
		self.stopwords = []
		self.all_keywords = {}

	def loadStopWords(self, fn):
		f = open(fn, "r")
		for l in f:
			self.stopwords.append(l.strip().lower())
		f.close()

	def tag_pos(self, s):
		good = ['NN', 'NNS', 'NNP', 'NNPS', 'JJ']
		#pattern = "NP:{(<NN.*|ME_.*>)*(<NN.*>)+(<ME_.*|NN.*>)*}"
		#NNS:{<NN|JJ||ME_.*>*<NNS>|<NN|JJ|ME_.*>+}
		pattern = r"""
				JJ:{(<JJ|RB><COMMA|CC>*)+<NN|NNP|NNPS|NNS>+}
				THE:{(<ME_DT><NNP|NNPS>+<JJ|NN>*)}
				NP:{(<NN.*|ME_.*>)+}
				NN:{(<NN|NNS|JJ>)+<ME_.*>*(<NN|JJ>+<NNS>|<NN|JJ>*<NNS>|<NN|JJ>+)}
			"""
		chunker = nltk.RegexpParser(pattern)
		#print "Sentence: ", s
		tmppos = nltk.pos_tag(nltk.word_tokenize(s))
		#print tmppos
		if len(tmppos) == 0: return []
		pos = []
		#if tmppos[0][1] == 'NN': tmppos[0][0] = tmppos[0][0].lower()
		noun = False
		sent_start = True
		for i, word in enumerate(tmppos):
			word = list(word)
			if word[0].endswith("ing") and not self.iscapitalized(word[0]): word[1] = 'VBG'
			if word[1] in ['NN', 'NNS', 'JJ'] and not sent_start and self.iscapitalized(word[0]): word[1] = 'NNP'
			if word[1] == 'IN' and word[0].lower() in ['of', 'against']: word[1] = "ME_IN"
			if word[1] == 'DT' and word[0].lower() == 'the': word[1] = "ME_DT"
			if word[1] == 'JJ' and len(pos) > 0 and pos[-1][1] in ['ME_DT', 'ME_IN']: word[1] = 'NN'
			if word[1] == ',': word[1] = "COMMA"
			if word[1] == '.': sent_start = True
			else: sent_start = False
			pos.append((word[0], word[1]))
		result = chunker.parse(pos)
		#print result
		return result


	def parseText(self, s):
		good = ['NN', 'NNS', 'NNP', 'NNPS']
		text = self.preclean(s)
		keyword_list = []
		pos_dict = {}
		for sentence in nltk.sent_tokenize(text):
			result = self.tag_pos(sentence)
			keywords = []
			for res in result:
				if type(res) == tuple:
					if res[1] in good:
						w = self.clean(res[0])
						if w and len(w) > 0:
							keywords.append(w)
							if res[1] in ['NNP', 'NNPS']: pos_dict[w] = 'NNP'
							else: pos_dict[w] = 'NN'
				elif type(res) == nltk.tree.Tree:
					prop = False
					if len(res) >= 1:
						if res.node == "JJ":
							adjlist = []
							noun_phrase = ""
							for l in res.leaves():
								if l[1] in ['JJ']: adjlist.append(l[0])
								elif l[1] in ['NN', 'NNS', 'NNP', 'NNPS']: noun_phrase += " " + l[0]
							for adj in adjlist:
								keywords.append(adj + " " + noun_phrase)
						else:
							phrase = ""
							for i, w in enumerate(res.leaves()):
								if (i == 0 and w[1] in ['ME_IN', 'ME_DT']) or (i == len(res.leaves()) - 1 and w[1] in ['ME_DT', 'ME_IN']): pass
								else: phrase += w[0] + ' '
							phrase = self.clean(phrase)
							if phrase and len(phrase) > 0:
								keywords.append(phrase)
								if prop: pos_dict[phrase] = 'NNP'
								else: pos_dict[phrase] = 'NN'
			if len(keywords) > 0:
				keyword_list.append(keywords)
		merged_list = set()
		for k in keyword_list: merged_list = set.union(merged_list, set(k))
		return (merged_list, keyword_list, pos_dict)

	def parseFile(self, filename):
		f = open(filename, "r")
		text = f.read()
		f.close()
		return self.parseText(text)

	def parseURLText(self, url):
		g = Goose()
		article = g.extract(url = url)
		text = article.cleaned_text
		return self.parseText(text)
	
	def getURLText(self, url):
		g = Goose()
		article = g.extract(url = url)
		text = article.cleaned_text
		return text

	def update_keyword_list(self, kwl, kw):	#lkl - list of keyword lists, kl - keyword list, kw - keyword
		kw_max = None
		max_score = -1
		for kw_i in self.all_keywords:
			if kw_i.lower().rfind(kw.lower()) >= 0:
				if self.all_keywords[kw_i] > max_score:
					max_score = self.all_keywords[kw_i]
					kw_max = kw_i
		if kw_max:
			kwl.add(kw_max)
			self.all_keywords[kw_max] += 1
		else:
			kwl.add(kw)
			self.all_keywords[kw] = 1


	def preclean(self, s):
		s = urllib2.unquote(s)
		s = re.sub(r"[\[\]\(\)\*\+\~\`\=\":;]", " , ", s)
		s = re.sub(r"\'s", " owned ", s)
		s = re.sub(r"[\t]", " ", s)
		s = re.sub(r"[\n]", ", ", s)
		return s

	def clean(self, s):
		try:
			float(s.strip())
			return None
		except:
			pass
		months = r"\bJanuary\b[0-9\ ,]*|\bFebruary\b[0-9\ ,]*|\bMarch\b[0-9\ ,]*|\bApril\b[0-9\ ,]*|\bMay\b[0-9\ ,]*|\bJune\b[0-9\ ,]*|\bJuly\b[0-9\ ,]*|\bAugust\b[0-9\ ,]*|\bSeptember\b[0-9\ ,]*|\bOctober\b[0-9\ ,]*|\bNovember\b[0-9\ ,]*|\bDecember\b[0-9\ ,]*"
		mem = r"[0-9\ ]+(GB|MB|KB|MP)"
		s = re.sub(months, '', s)
		s = re.sub(mem, '', s)
		#print "BEFORE:", s
		#for word in self.stopwords:
		#	s = re.sub("(\ |^)" + word + "(\ |$)", "", s, flags=re.IGNORECASE)
		#print "AFTER:", s
		if s and self.iscapitalized(s): return s.strip()	#proper noun, so dont touch it!
		#if len(re.findall("series|species", s)) > 0: pass
		#elif s.endswith("ies"): s = s[:-3] + "y"
		#elif s.endswith("es") or (s.endswith("s") and not s.endswith("ss")): s = s[:-1]
		#elif s.endswith("ing"): s = s[:-3]
		return s.strip()

	def iscapitalized(self, s):
		c = s[0]
		if 65 <= ord(c) <= 90: return True
		return False

	def getAllKeywords(self, f):
		(title, cat, kwl) = self.parseFile(f)
		allset = set()
		for x in kwl:
			for i in x: allset.add(i)
		return allset
