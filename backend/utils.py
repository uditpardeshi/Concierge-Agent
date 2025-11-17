# TODO: Refactor this mess later
import time
import random

def generate_id():
    # Quick hack for unique IDs
    return f"{int(time.time())}_{random.randint(1000, 9999)}"

def safe_get(d, key, default=None):
    # Because I keep forgetting to check if keys exist
    try:
        return d[key]
    except (KeyError, TypeError):
        return default

# This function is probably overkill but whatever
def retry_on_failure(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise e
            time.sleep(0.5)  # Wait a bit before retry