"""
Base classes for application.

"""

class Object(object):
    def __init__(self):
        self.__binds = {}
    def bind(self,event,function):
        """Binds a function to the event.
        """
        if not self.__binds.has_key(event):
            self.__binds[event] = []
        if self.__binds[event].count(function) == 0:
            self.__binds[event].append(function)

    def unbind(self,event,function):
        """Unbinds a function from the event.
        """
        while not self.__binds[event].count(function) == 0:
            self.__binds[event].remove(function)
            
    def call(self,event,*args,**kwargs):
        """raise event with given args.
        """
        if self.__binds.has_key(event):
             for function in self.__binds[event]:
                function(*args,**kwargs)

