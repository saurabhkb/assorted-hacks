import MySQLdb
import json
from constants import *
class RelDataStore():
	def __init__(self):
		self.conn = MySQLdb.connect(HOST, USER, PASSWORD, DB_NAME)
		self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
	
	def get_users_for_key(self, key):
		self.cursor.execute('select `uid` from `user` where `key` = %s' % (key))
		rows = self.cursor.fetchall()
		return rows

	def create_user_for_key(self, key, uid):
		num_rows = self.cursor.execute('insert into `user` (`key`, `uid`) values (%s, %s) where not exists (select * from `user` where `key` = %s and `uid` = %s)' % (key, uid, key, uid))
		self.conn.commit()
		return num_rows

	def rem_user_for_key(self, key, val):
		num_rows = self.cursor.execute('delete * from `user` where `key` = %s and `uid` = %s' % (key, val)) #cascading delete into data table
		self.conn.commit()
		return num_rows

	def rem_all_users_for_key(self, key):
		num_rows = self.cursor.execute('delete * from `user` where `key` = %s' % (key)) #cascading delete
		self.conn.commit()
		return num_rows

	def is_user_for_key(self, key, uid):
		return self.cursor.execute('select * from `user` where `key` = %s and `uid` = %s' % (key, uid)) == 1L

	def get_interests_for_user_for_key(self, key, uid, interest_types):
		if SUPPLIED in interest_types and GENERATED in interest_types:
			num_rows = self.cursor.execute('select `interest`, `frequency`, `last_access`, `interest_level`, if(`type` = 0, "supplied", "generated") as source from `data` where `key` = %s and `uid` = %s' % (key, uid))
		elif SUPPLIED in interest_types:
			num_rows = self.cursor.execute('select `interest`, `frequency`, `last_access`, `interest_level`, if(`type` = 0, "supplied", "generated") as source from `data` where `key` = %s and `uid` = %s and `type` = %d' % (key, uid, SUPPLIED_ID))
		elif GENERATED in interest_types:
			num_rows = self.cursor.execute('select `interest`, `frequency`, `last_access`, `interest_level`, if(`type` = 0, "supplied", "generated") as source from `data` where `key` = %s and `uid` = %s and `type` = %d' % (key, uid, GENERATED_ID))
		rows = self.cursor.fetchall()
		return rows, num_rows
		
	def add_interest_for_user_for_key(self, key, uid, add_int):
		timestamp = int(time.time())
		num_rows = self.cursor.execute('insert into `data` (`key`, `uid`, `interest`, `interest_level`, `frequency`, `last_access`, `type`) values (%s, %s, %s, %f, %s, %s, %d) on duplicate key update `frequency` = `frequency` + 1, `interest_level` = `interest_level` + 1' % (key, uid, add_int, 1, 1, timestamp, SUPPLIED_ID))
		self.conn.commit()
		return num_rows

	def rem_interest_for_user_for_key(self, key, val, rem_int):
		num_rows = self.cursor.execute('delete from `data` where `key` = %s and `uid` = %s and `interest` = %s' % (key, val, rem_int))
		self.conn.commit()
		return num_rows
