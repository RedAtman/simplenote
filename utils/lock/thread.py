__version__ = "0.0.1"
__author__ = "redatman"
__date__ = "2024-08-03"
# TODO: ResultProcess unable to collect results yet


import logging
from multiprocessing import Process
from threading import Thread
from typing import Callable


logger = logging.getLogger()


class ResultExecutorMixin:
    start: Callable
    _target: Callable
    _args: tuple
    _kwargs: dict
    _result = None

    def run(self):
        try:
            if self._target is not None:
                self._result = self._target(*self._args, **self._kwargs)
        finally:
            del self._target, self._args, self._kwargs

    def join(self, *args):
        super().join(*args)  # type: ignore
        # logger.warning(getattr(self, "_result", None))
        return getattr(self, "_result", None)

    def get_result(self):
        self.start()
        return self.join()


ResultProcess = type("ResultProcess", (ResultExecutorMixin, Process), {})
ResultThread = type("ResultThread", (ResultExecutorMixin, Thread), {})


class OptimisticLockingError(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(f"Update failed due to concurrent modification: {key}")


class OptimisticLockingDict:

    def __init__(self, executor_cls=ResultThread):
        if issubclass(executor_cls, Process):
            from multiprocessing import Lock, Manager

            self.data = Manager().dict()
            self.lock = Lock()
        elif issubclass(executor_cls, Thread):
            from threading import Lock

            self.data = {}
            self.lock = Lock()
        else:
            raise ValueError(
                f"Unsupported executor class: {executor_cls}, must be either multiprocessing.Process or threading.Thread"
            )

    def _get(self, key):

        # logger.debug(("_get", os.getpid(), threading.current_thread().name, threading.current_thread().ident))
        with self.lock:
            if key in self.data:
                value, version = self.data[key]
                return value, version
            else:
                return None, None

    def get(self, key):
        logger.info(self.data)
        value, version = self._get(key)
        return value

    def _set(self, key, new_value, expected_version):
        # logger.warning((id(self.data), self.data))
        # logger.debug(("_set", os.getpid(), threading.current_thread().name, threading.current_thread().ident))
        with self.lock:
            if key in self.data:
                current_value, current_version = self.data[key]
                if current_version == expected_version:
                    self.data[key] = (new_value, current_version + 1)
                    return True
                else:
                    return False
            else:
                # If the key does not exist, initialize it
                self.data[key] = (new_value, 1)
                return True

    def set(self, key, new_value):
        return self._set(key, new_value, 0)

    def optimistic_update(self, key, new_value):
        # logger.warning((id(self), id(self.data)))
        # logger.warning((id(self), self))
        # logger.debug(f">>: {key} = {new_value}")
        value, version = self._get(key)
        # time.sleep(0.1)
        if value is not None:
            success = self._set(key, new_value, version)
            if success:
                logger.debug(f"Update successful: {key} from {value} to {new_value}")
            else:
                logger.debug(f"Update failed due to concurrent modification: {key} to {new_value}")
                raise OptimisticLockingError(key)
        else:
            # Initialize the key if it doesn't exist
            self.set(key, new_value)
            logger.debug(f"Initial set: {key} = {new_value}")
        return new_value

    # def update(self, key, new_value):
    #     with self.lock:
    #         return self.optimistic_update(key, new_value)


def test_multiple_updates(executor_cls):
    optimistic_dict = OptimisticLockingDict(executor_cls)
    logger.warning((id(optimistic_dict), id(optimistic_dict.data)))
    key = "name"

    # Initialize a key-value pair
    optimistic_dict.optimistic_update(key, "value1")

    # tasks = []
    results = set()

    # Simulate concurrent updates
    def concurrent_update():
        for i in range(6):
            task = executor_cls(target=optimistic_dict.optimistic_update, args=("name", i))
            import time

            # time.sleep(0.01)
            # tasks.append(task)
            # task.start()
            # result = task.join()
            result = task.get_result()
            logger.debug(result)
            results.add(result)

    logger.info(results)

    concurrent_update()
    last_result = optimistic_dict.get(key)
    expected_result = 5
    assert last_result == expected_result, f"Expected last value is {expected_result}, but got %s" % last_result
    expected_results = {0, 1, 2, 3, 4, 5}
    assert results == expected_results, f"Expected results is {expected_results}, but got {results}"


def run_tests():
    tests = {
        ("Test test_multiple_process_updates          ", test_multiple_updates, (ResultProcess,)),
        ("Test test_multiple_thread_updates           ", test_multiple_updates, (ResultThread,)),
    }

    for test_name, test, args in tests:
        try:
            prefix = f"Running [{test_name}]"
            test(*args)
            logger.info(f"{prefix} Succeeded")
        except AssertionError as e:
            logger.error(f"{prefix} Failed => {e}")
        except Exception as e:
            logger.critical(f"{prefix} Exception => {e}")


if __name__ == "__main__":
    from importlib import import_module

    import_module("utils.logger.init")
    run_tests()
