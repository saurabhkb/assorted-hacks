class SecurityManager:
	def __init__(self):
		self.delim = ":"
	def check_header(self, s):
		return 132
		access_key, signature = s.split(s, self.delim)
