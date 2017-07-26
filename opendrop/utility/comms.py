from collections import namedtuple

from opendrop.utility.events import Event, PersistentEvent

class UniqueVariable:
    pass

PipeQueueItem = namedtuple("PipeQueueItem", ("name", "value", "on_shift"))
WaitingListener = namedtuple("PipeQueueItem", ("target", "event"))

class Pipe(object):
    EMPTY = UniqueVariable()
    CLOSED = UniqueVariable()

    def __init__(self):
        self.queue = []

        self.waiting_listeners = []

        self.on_change = Event()
        self.on_close = PersistentEvent()

        self.closed = False

    def add_waiting(self, target, event):
        self.waiting_listeners.append(WaitingListener(target=target, event=event))

    def get_waiting(self, target):
        for i, waiting_listener in enumerate(self.waiting_listeners):
            if waiting_listener.target == target:
                del self.waiting_listeners[i]

                return waiting_listener

    def queue_push(self, name, v, on_shift):
        self.queue.append(PipeQueueItem(name=name, value=v, on_shift=on_shift))

    def queue_shift(self, name=None):
        for i, item in enumerate(self.queue):
            if item.name == name:
                del self.queue[i]
                return item

    def push(self, v, name=None):
        if self.closed:
            return Pipe.CLOSED

        on_shift_event = PersistentEvent()

        waiting_listener = self.get_waiting(target=name)

        if waiting_listener:
            waiting_listener.event.fire(v)
            on_shift_event.fire()
        else:
            self.queue_push(name, v, on_shift_event)

        return on_shift_event

    def shift(self, name=None, blocking=False):
        if self.closed:
            return Pipe.CLOSED

        item = self.queue_shift(name)
        val = item and item.value

        if blocking:
            on_receive = PersistentEvent()

            if val:
                on_receive.fire(val)
            else:
                self.add_waiting(target=name, event=on_receive)

            return on_receive
        else:
            return val or Pipe.EMPTY

    def close(self):
        self.on_close.fire()

        for waiting_listener in self.waiting_listeners:
            waiting_listener.event.fire(Pipe.CLOSED)
