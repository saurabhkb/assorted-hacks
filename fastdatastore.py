import redis
import os
class FastDataStore():
	"""mainly for flexibility purposes."""
	def __init__(self):
		redis_url = os.getenv('REDISCLOUD_URL', 'redis://localhost:6379')
		self.redis = redis.from_url(redis_url)
		self.redis.flushdb() #remember to remove this!

	def get(self, k):
		return self.redis.get(k)

	def set(self, k, v):
		return self.redis.set(k, v)

	def incr(self, k, inc):
		return self.redis.incr(k, inc)

	def sadd(self, name, elem):
		return self.redis.sadd(name, elem)

	def scard(self, name):
		return self.redis.scard(name)

	def sismember(self, name, elem):
		return self.redis.sismember(name, elem)

	def spop(self, name):
		return self.redis.spop(name)

	def smembers(self, name):
		return self.redis.smembers(name)
