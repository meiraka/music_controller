#!/usr/bin/python

"""
notifies MusicController status by on screen display.
"""

APP_NAME = u'MusicController'

class NotifyBase(object):
	"""
	base class for notificator.

	Properties:
		send -- toggle on/off notify interface.
		active -- False if this object can not use in this environment(ex. notify module does not installed).
	"""
	def __init__(self,client,active):
		self.__cached = dict(
			send=False,
			active=active
			)

	def test(self):
		pass

	def song(self,song):
		pass

	def __readwrite(key):
		def get(self):
			return self.__cached[key]
		def set(self,value):
			self.__cached[key] = value
		return (get,set)

	send = property(*__readwrite('send'))
	active = property(__readwrite('active')[0])


class NotifyOSD(NotifyBase):
	def __init__(self,client):
		self.client = client
		try:
			import pynotify
			pynotify.init(APP_NAME)
			self.notify = pynotify.Notification(APP_NAME,u'Connecting Server',None)
			NotifyBase.__init__(self,client,True)
			client.playback.bind(client.playback.UPDATE,self.update)
		except ImportError:
			NotifyBase.__init__(self,client,False)

	def update(self):
		status = self.client.playback.status
		if status and u'song' in status and len(self.client.playlist)> int(status[u'song']):
			self.song(self.client.playlist[int(status[u'song'])])

	def song(self,song):
		title = song.format('%title% %artist%')
		desc = song.format('%album% %date%')
		self.notify.update(title,desc,None)
		self.notify.show()
