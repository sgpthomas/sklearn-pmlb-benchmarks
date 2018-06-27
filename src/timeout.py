import signal

class TimeoutError(Exception):
    pass

class timeout(object):
    def __init__(self, seconds):
        self.seconds = seconds

    def __call__(self, f):
        def _handle_timeout(signum, fname):
            raise TimeoutError()

        def wrapped_f(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(self.seconds)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wrapped_f
