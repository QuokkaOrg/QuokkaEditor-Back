import time
from contextlib import contextmanager


@contextmanager
def timed_execution():
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Code executed in {elapsed_time:.4f} seconds.")
