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
		self.__song = None
		if active:
			client.playback.bind(client.playback.UPDATE,self.update)

	def update(self):
		""" Update song notify.

		get current playing song and call song().
		"""
		status = self.client.playback.status
		if status and u'song' in status and len(self.client.playlist)> int(status[u'song']):
			song = self.client.playlist[int(status[u'song'])]
			if not self.__song == song:
				self.__song = song
				self.song(song)



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
		except ImportError:
			NotifyBase.__init__(self,client,False)

	def song(self,song):
		title = song.format('%title%')
		desc = song.format('%artist%\n%album% %date%')
		img = song.artwork
		self.notify.update(title,desc,img)
		self.notify.set_timeout(4000)
		try:
			self.notify.show()
		except Exception,err:
			print err

class GrowlNotify(NotifyBase):
	def __init__(self,client):
		self.client = client
		self.__inited = False
		try:
			import gntp
			NotifyBase.__init__(self,client,True)
			self.reconnect()
		except ImportError:
			NotifyBase.__init__(self,client,False)
	

	def reconnect(self,*args,**kwargs):
		import gntp.notifier
		kwargs = dict(
			applicationName = APP_NAME,
			notifications = ["Song","Connection"],
			defaultNotifications = ["Song"],
			)
		if self.client.config.notify_growl_host and not self.client.config.notify_growl_host == 'localhost':
			kwargs['hostname'] = self.client.config.notify_growl_host
		if self.client.config.notify_growl_pass:
			kwargs['password'] = self.client.config.notify_growl_pass
		growl = gntp.notifier.GrowlNotifier(**kwargs)
		try:
			growl.register()
			self.growl = growl
			self.__inited = True
		except gntp.errors.NetworkError:
			pass

	def song(self,song):
		title = song.format('%title% %artist%')
		desc = song.format('%album% %date%')
		try:
			self.growl.notify(
				"Song",
				title=title,
				description=desc,
				sticky=False)
		except:
			pass


