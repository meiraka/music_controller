import unittest
import time
import random
import client

"""
test for client.py

requires mpd process on localhost:6600
and some songs in mpd library dir.
"""

class TestClientConfig(unittest.TestCase):
	def setUp(self):
		self.mpd = client.Client()

	def test_profiles(self):
		value = self.mpd.config.profiles
		self.assertIn([u'default',u'localhost',u'6600',False,u''],value)

	def test_default_profile(self):
		value = self.mpd.config.default_profile
		self.assertEqual(value,[u'default',u'localhost',u'6600',False,u''])


	
class TestClientConnection(unittest.TestCase):
	def setUp(self):
		self.mpd = client.Client()
	def test_message(self):
		self.mpd.connect()

class TestClientController(unittest.TestCase):
	def setUp(self):
		self.mpd = client.Client()
		self.mpd.connect()
	
	def test_play_current(self):
		self.mpd.playback.stop()
		self.mpd.playback.update()
		value = self.mpd.playback.status['state']
		self.assertEqual(value,u'stop')
		self.mpd.playback.play()
		self.mpd.playback.update()
		value = self.mpd.playback.status['state']
		self.assertEqual(value,u'play')
		self.mpd.playback.stop()

class TestClientLibrary(unittest.TestCase):
	def setUp(self):
		self.mpd = client.Client()
		self.mpd.connect()
		self.__updated = False
		self.mpd.library.bind(self.mpd.library.UPDATE,self.updated)
	
	def test_library(self):
		value = list(self.mpd.library)
		self.assertEqual(type(value),list)

	def test_update(self):
		self.__updated = False
		self.mpd.library.update()
		limit = 10
		while not self.__updated and limit > 0:
			self.mpd.playback.update()
			time.sleep(1)
			limit = limit -1

	def updated(self):
		self.__updated = True


class TestClientPlaylist(unittest.TestCase):
	def setUp(self):
		self.mpd = client.Client()
		self.mpd.connect()
	
	def test_list(self):
		value = list(self.mpd.playlist)
		self.assertEqual(type(value),list)

	def test_append(self):
		"""add random song to playlist."""
		append = self.mpd.library[int(len(self.mpd.library)*random.random())]
		self.mpd.playlist.append(append)
		self.assertEqual(self.mpd.playlist[-1][u'file'],append[u'file'])

	def test_extend(self):
		"""add random songs to playlist"""
		rand1 = int((len(self.mpd.library)-1)*random.random())
		rand2 = int(len(self.mpd.library)*random.random())
		while rand1 > rand2:
			rand2 = int(len(self.mpd.library)*random.random())
		extend = self.mpd.library[rand1:rand2]
		length = len(self.mpd.playlist)
		self.mpd.playlist.extend(extend)
		msg = str(rand1) + ' to ' + str(rand2) + ' length ' + str(length) + ' to ' + str(length) + '+' + str(len(extend)) + '='+str(len(self.mpd.playlist))
		self.assertEqual(extend[-1][u'file'],self.mpd.playlist[-1][u'file'],msg=msg)
		self.assertEqual(extend[0][u'file'],self.mpd.playlist[length][u'file'],msg=msg)
		self.assertEqual(length+len(extend),len(self.mpd.playlist),msg=msg)

	def test_delete(self):
		rand = int((len(self.mpd.playlist)-1)*random.random())
		song = self.mpd.playlist[rand]
		self.assertIn(song,self.mpd.playlist)
		del self.mpd.playlist[rand]
		self.assertNotIn(song,self.mpd.playlist)

	def test_delete_slice(self):
		rand1 = int((len(self.mpd.playlist)-1)*random.random())
		rand2 = int(len(self.mpd.playlist)*random.random())
		length = len(self.mpd.playlist)
		song1 = self.mpd.playlist[rand1]
		song2 = self.mpd.playlist[rand2]
		del self.mpd.playlist[rand1:rand2]
		self.assertNotIn(song1[u'file'],self.mpd.playlist)
		self.assertNotIn(song2[u'file'],self.mpd.playlist)

if __name__ == '__main__':
	unittest.main()
