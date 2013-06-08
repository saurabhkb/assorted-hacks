from extractor import Extractor
import redis


class Crawler:
	def __init__(self, name = "localhost"):
		self.ex = Extractor()
		self.redis = redis.Redis(name)
		self.seen_key = "URL_SEEN"
		self.queue_key = "URL_QUEUE"
		self.redis.flushdb()

	def crawl(self, start):
		self.redis.sadd(self.queue_key, start)
		while self.redis.scard and i > 0:
			topic = self.redis.spop(self.queue_key)
			print topic
			if topic and not self.redis.sismember(self.seen_key, topic):
				self.redis.sadd(self.seen_key, topic)
				keywords, categories, links = self.ex.extract(topic)
				for t in links:
					self.redis.sadd(self.queue_key, t)
