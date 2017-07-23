"""
    Really simple implementation of coroutines
"""

import inspect

from opendrop.utility.events import Event, PersistentEvent

import threading

class UniqueVariable:
    pass

# Constants

EXIT = UniqueVariable()

class Coroutine(object):
    def __init__(self, gen, reply):

        # self.alive = True
        self.gen = gen
        self.lock = threading.RLock()

        self.reply = reply

    def close(self, *args, **kwargs):
        print("waiting to close")
        with self.lock:
            print("closing")
            self.gen.close()

    def step(self, send_value = None):
        with self.lock:
            if not self.reply.is_set():
                try:
                    yield_value = self.gen.send(send_value)

                    if yield_value == EXIT or \
                       isinstance(yield_value, tuple) and len(yield_value) and yield_value[0] == EXIT:
                        if isinstance(yield_value, tuple):
                            send_value = yield_value[1:]

                            if len(send_value) == 1:
                                send_value = send_value[0]
                            elif len(send_value) == 0:
                                send_value = None

                        self.gen.close()
                        raise StopIteration
                    elif isinstance(yield_value, (Event, Coroutine)):
                        event = None

                        if isinstance(yield_value, Event):
                            event = yield_value
                        elif isinstance(yield_value, Coroutine):
                            event = yield_value.reply

                        def cb(*args, **kwargs):
                            if len(args) == 1:
                                args = args[0]

                            if kwargs:
                                gen.throw(
                                    ValueError,
                                    "Can't yield on an event that has been fired with keyword arguments"
                                )
                            #print("Fired {}, continueing...".format(cb))
                            self.step(send_value = args)
                        #print("Binding from... {0} to... {1}".format(cb, yield_value))
                        event.bind_once(cb)
                    else:
                        # Didn't yield a supported type, do nothing and pass it back
                        self.step(send_value = yield_value)
                except StopIteration:
                    self.reply(send_value)

def co(function):
    if inspect.isgeneratorfunction(function):
        def wrapper(*args, **kwargs):
            reply = PersistentEvent()
            gen = function(*args, **kwargs)

            new_co = Coroutine(gen, reply)
            new_co.step()

            return new_co
        return wrapper
    else: # Do nothing
        return function
