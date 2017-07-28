from abc import ABCMeta, abstractmethod
import bisect
from six import add_metaclass

import timeit
import threading

import cv2
from PIL import Image

from opendrop.constants import ImageSourceOption

from opendrop.utility.vectors import Vector2
from opendrop.utility.events import Event, PersistentEvent

class WaitUntil(object):
    def __init__(self, until=None, after=None):
        self.start = timeit.default_timer()

        if until is not None:
            self.until = until
        elif after is not None:
            self.until = self.start + after
        else:
            raise ValueError("either 'until', or 'after' must be specified")

    @property
    def time_left(self):
        now = timeit.default_timer()
        
        return max(self.until - now, 0)

class Throttler(object):
    """
        Throttler class, used for regulating the pace of a loop. Initialise with an 'interval'
        parameter that specifies the target duration of a loop and call Throttler.lap(), to return
        the needed wait time in seconds tha the loop should hold for to meet the average interval
        time specified. .lap() may return a negative value if the interval given is too short or
        the loop is taking too long to execute.

        Example:

            import random, time

            throttler = Throttler(1)

            for i in range(10):
                # Some task that takes an indeterminant amount of time
                time.sleep(random.uniform(0, 0.5))

                time.sleep(max(0, throttler.lap()))

                print(i)

    """
    def __init__(self, interval):
        self.target_avg_lap_time = interval

        self.lap_start = None
        self.split = 0

    def lap(self):
        if self.lap_start is not None:
            lap_time = timeit.default_timer() - self.lap_start

            self.split += lap_time - self.target_avg_lap_time

            self.lap_start = timeit.default_timer()

            return self.target_avg_lap_time - self.split
        else:
            self.lap_start = timeit.default_timer()
            return self.target_avg_lap_time

class FrameIterator(object):
    def __init__(self, image_source, num_frames=float("inf"), interval=-1, loop=False):
        # If recorded source, reset the playback head to 0
        if isinstance(image_source, RecordedSource):
            image_source.scrub(0)

        self.image_source = image_source

        self.frames_left = num_frames
        self.interval = interval
        self.loop = loop

        self.timestamp_offset = None

        self.throttler = interval != -1 and Throttler(interval)

    def __iter__(self):
        return self

    def __next__(self):
        if self.frames_left > 0:
            timestamp, image = self.image_source.read()

            if timestamp is None and image is None:
                raise StopIteration

            if self.timestamp_offset is None:
                # timestamp_offset is used so the first image timestamp is 0, and subsequent
                # timestamps are relative to the first image
                self.timestamp_offset = -timestamp

            timestamp += self.timestamp_offset

            if self.frames_left: self.frames_left -= 1
        else:
            raise StopIteration

        if self.frames_left > 0:
            if isinstance(self.image_source, LiveSource):
                hold_for = self.throttler and self.throttler.lap() or 0

                if hold_for < 0:
                    print(
                        "[WARNING] Iterator not keeping up with specified interval ({:.2f}s behind)"
                        .format(-hold_for)
                    )
            elif isinstance(self.image_source, RecordedSource):
                hold_for = self.interval

                if hold_for is not None:
                    self.image_source.skip(hold_for, wrap_around=self.loop)
                else: # Interval not specified, skip by one frame
                    self.image_source.skip_index(1, wrap_around=self.loop)
        else:
            hold_for = 0

        return_values = (
            timestamp,
            image,
            WaitUntil(after=hold_for)
        )

        return return_values

    # For Python2 support
    next = __next__

class FrameIterable(object):
    def __init__(self, image_source, **opts):
        self.image_source = image_source

        self.opts = opts

    def __iter__(self):
        return FrameIterator(self.image_source, **self.opts)

@add_metaclass(ABCMeta)
class ImageSource(object):
    def __init__(self):
        self.released = False

    def frames(self, *args, **kwargs):
        return FrameIterable(self, *args, **kwargs)

    @property
    def size(self):
        # May not be the most optimized way to retrieve size of a source but unless another method
        # is overriden, this will do.
        timestamp, image = self.read()
        if image:
            with image as image:
                return Vector2(image.size)
        else:
            return Vector2(0, 0)

    @abstractmethod
    def read(self):
        if self.released:
            raise ValueError(
                "Can't read from {}, object is released".format(self.__class__.__name__)
            )

    @abstractmethod
    def release(self):
        print("[DEBUG] Releasing {}".format(self.__class__.__name__))
        self.released = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

@add_metaclass(ABCMeta)
class LiveSource(ImageSource):
    def __init__(self, **kwargs):
        super(LiveSource, self).__init__(**kwargs)

@add_metaclass(ABCMeta)
class RecordedSource(ImageSource):
    def __init__(self, loop=False, **kwargs):
        super(RecordedSource, self).__init__(**kwargs)

        self.emulated_time = 0

    @abstractmethod
    def skip(self, by, wrap_around=False): pass

    @abstractmethod
    def scrub(self, to, wrap_around=False): pass

class USBCameraSource(LiveSource):
    MAX_RETRY_READ_ATTEMPTS = 5

    def __init__(self, camera_index, **kwargs):
        super(USBCameraSource, self).__init__(**kwargs)

        self.busy = threading.Lock()

        with self.busy:
            self.vc = cv2.VideoCapture(camera_index)

            if not self.vc.isOpened():
                raise ValueError(
                    "OpenCV failed to create a VideoCapture on index {}".format(camera_index)
                )

        print("[DEBUG] VideoCapture started, {0}x{1}".format(*self.size))

    def read(self):
        with self.busy:
            super(USBCameraSource, self).read()

            for i in range(self.MAX_RETRY_READ_ATTEMPTS):
                # Sometimes VideoCapture fails to read, so just retry a few times
                rval, im_array = self.vc.read()
                timestamp = timeit.default_timer()
                if rval:
                    # Pixel array comes in at BGR format, Pillow expects RGB
                    im_array = cv2.cvtColor(im_array, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(im_array)
                    return timestamp, image
                else:
                    print("[DEBUG] VideoCapture failed, retrying...({})".format(i))

            raise ValueError(
                "OpenCV VideoCapture failed to read image"
            )

    def release(self):
        with self.busy:
            super(USBCameraSource, self).release()
            self.vc.release()

class LocalImages(RecordedSource):
    def __init__(self, filenames, timestamps=None, interval=1, **kwargs):
        super(LocalImages, self).__init__(**kwargs)

        if not isinstance(filenames, (tuple, list)):
            filenames = (filenames,)

        self.filenames = filenames

        if timestamps is None:
            timestamps = list(i*interval for i in range(self.num_images))
        elif timestamps[0] != 0:
                raise ValueError(
                    "'timestamps' must be begin with 0"
                )

        self.timestamps = timestamps

    @property
    def next_frame_interval(self):
        curr_index = self.curr_index
        if curr_index >= self.num_images - 1 or curr_index < 0:
            # Currently at last index (or past index range), there is no next frame, or index is
            # less than 0
            return 0
        else:
            return self.timestamps[curr_index + 1] - self.timestamps[curr_index]

    @property
    def curr_index(self):
        return self.index_from_timestamp(self.emulated_time)

    @property
    def length_time(self):
        return self.timestamps[-1]

    @property
    def num_images(self):
        return len(self.filenames)

    def index_from_timestamp(self, timestamp):
        if timestamp < 0 or timestamp > self.length_time:
            return -1

        if self.num_images == 1:
            return 0
        else:
            index = bisect.bisect(self.timestamps, timestamp) - 1

        return index

    def timestamp_from_index(self, index):
        try:
            return self.timestamps[index]
        except IndexError:
            return -1

    def read(self):
        super(LocalImages, self).read()

        try:
            timestamp = self.emulated_time
            curr_index = self.curr_index

            if curr_index < 0 or curr_index > self.num_images - 1:
                raise IndexError

            filename = self.filenames[self.curr_index]

            image = Image.open(filename)
            return timestamp, image
        except IndexError:
            self.release()
            return None, None

    def set_emulated_time(self, t, wrap_around=False):
        if wrap_around:
            if self.length_time == 0:
                t = 0
            else:
                t %= self.length_time

        self.emulated_time = t

    def skip(self, by, wrap_around=False):
        self.set_emulated_time(self.emulated_time + by, wrap_around=wrap_around)

    def skip_index(self, by, wrap_around=False):
        curr_index = self.curr_index
        new_index = curr_index + by

        if wrap_around:
            new_index %= self.num_images

        new_time = self.timestamp_from_index(new_index)

        self.scrub(new_time)

    def scrub(self, to, wrap_around=False):
        self.set_emulated_time(to, wrap_around=wrap_around)

    def release(self):
        super(LocalImages, self).release()
        # No need to release anything


def load(desc, source_type, **opts):
    if source_type == ImageSourceOption.LOCAL_IMAGES:

        return LocalImages(filenames=desc, **opts)

    elif source_type == ImageSourceOption.USB_CAMERA:

        return USBCameraSource(camera_index=desc, **opts)

    elif source_type == ImageSourceOption.FLEA3:

        raise NotImplementedError
