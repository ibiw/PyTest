"""
Python Decorator
"""
from functools import wraps
import time


def timer(func):
    """A timer decorator"""

    @wraps(func)  # wraps of funtools make sure the return function name
    def rapper(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        print('Time used of {} is: {:.2f}'.format(func.__name__, time.time() - start_time))
    return rapper


def double_rapper(func):
    """a double decorators test"""
    @wraps(func)
    def rapper(*args, **kwargs):
        print('I am going to run {}'.format(func.__name__))
        func(*args, **kwargs)
        print('{} finished'.format(func.__name__))
    return rapper


@timer
@double_rapper
def test(time_wait):
    """a test function"""
    time.sleep(time_wait)
    print('Sleep {} seconds'.format(time_wait))


@timer
@double_rapper
def greeting(name):
    """another decorator test"""
    print('Hello ', name)


greeting('Ryan')

test(3)
