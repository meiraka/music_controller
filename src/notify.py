"""
Notifies Application status by on screen display.

"""

import string

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
		if active:
			client.playlist.bind(client.playlist.UPDATE_CURRENT,self.update)
			client.connection.bind(client.connection.SERVER_ERROR,self.error)

	def update(self,song):
		""" Update song notify.

		get current playing song and call song().
		"""
		self.song(song)

	def test(self):
		pass

	def song(self,song):
		pass

	def error(self,status):
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
		try:
			self.notify.show()
		except Exception,err:
			pass

	def error(self,error):
		try:
			self.notify.close()
		except:
			pass
		p,host,port,up,pa = self.client.connection.current
		title = _('MPD Server Error (%s)') % (host+':'+port)
		desc = _(error)
		self.notify.update(title,desc)
		if desc == error:
			desc = string.capwords(error)
		try:
			self.notify.show()
		except Exception,err:
			pass


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


