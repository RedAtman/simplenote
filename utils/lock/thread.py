__version__ = "0.0.2"
__author__ = "redatman"
__date__ = "2024-08-06"
# TODO: ResultProcess unable to collect results yet


import logging
from multiprocessing import Process
from threading import Thread
from typing import Any, Callable


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

    def __init__(self, key: str, value: Any, version: int, expected_version: int) -> None:
        super().__init__(
            f"Failed to concurrent update key `{key}` to value `{value}`, version `{version}` expected version `{expected_version}`"
        )


class OptimisticLockingDict:

    def __init__(self, executor_cls: Any = None):

        if executor_cls is None:
            from threading import Lock

            self.data = {}
            self.lock = Lock()
        elif issubclass(executor_cls, Process):
            from multiprocessing import Lock, Manager

            self.data = Manager().dict()
            self.lock = Lock()
        else:
            from threading import Lock

            self.data = {}
            self.lock = Lock()
        # elif issubclass(executor_cls, Thread):
        logger.info((id(self), id(self.data)))

    def _get(self, key):
        """
        Returns (value, version)
        """
        # logger.info(self.data)
        # logger.debug(("_get", os.getpid(), threading.current_thread().name, threading.current_thread().ident))
        with self.lock:
            if key in self.data:
                return self.data[key]
            else:
                return None, None

    def get(self, key):
        value, version = self._get(key)
        return value

    def _set(self, key, new_value, expected_version):
        logger.info((key, new_value, expected_version))
        # logger.warning((id(self.data), self.data))
        # logger.debug(("_set", os.getpid(), threading.current_thread().name, threading.current_thread().ident))
        with self.lock:
            if key in self.data:
                current_value, current_version = self.data[key]
                if current_version != expected_version:
                    raise OptimisticLockingError(key, new_value, current_version, expected_version)
                current_version += 1
            else:
                # self.data[key] = (new_value, 0)
                current_version = 0
            self.data[key] = (new_value, current_version)
            return self.data[key]

    def optimistic_update(self, key, new_value):
        # logger.warning((id(self), self, id(self.data)))
        value, expected_version = version = self._get(key)
        import time

        time.sleep(0.1)
        if value is None:
            # Initialize the key if it doesn't exist
            expected_version = 0
            logger.debug(f"Set: {key} = {new_value}, expected_version = {expected_version}")
        self._set(key, new_value, expected_version)
        return new_value

    async def optimistic_update_async(self, key, new_value):
        return self.optimistic_update(key, new_value)

    # def update(self, key, new_value):
    #     with self.lock:
    #         return self.optimistic_update(key, new_value)


# Simulate concurrent updates
# def _concurrent_update(optimistic_dict: OptimisticLockingDict, key: str):
#     import time

#     results = set()
#     for i in range(6):
#         result = optimistic_dict.optimistic_update(key, i)
#         # result = partial_fn(i)
#         # time.sleep(0.01)
#         logger.debug(result)
#         results.add(result)

#     return results


def _concurrent_update(partial_fn, get_result, key: str):
    import time

    results = set()
    for i in range(6):
        result = get_result(partial_fn, key, i)
        # time.sleep(0.01)
        logger.debug(result)
        results.add(result)

    return results


def _test_concurrent_update(results):
    from functools import partial

    # last_result = optimistic_dict.get(key)
    # expected_result = 5
    # assert last_result == expected_result, f"Expected last value is {expected_result}, but got %s" % last_result
    expected_results = {0, 1, 2, 3, 4, 5}
    assert isinstance(
        results, type(expected_results)
    ), f"Expected results type is {type(expected_results)}, but got {type(results)}"
    assert results == expected_results, f"Expected results is {expected_results}, but got {results}"


def test_concurrent_update(executor_cls=None):
    key = "name"

    def get_result(partial_fn, key, i):
        return partial_fn(args=(key, i))

    optimistic_dict = OptimisticLockingDict(executor_cls=executor_cls)
    results = _concurrent_update(lambda args: optimistic_dict.optimistic_update(*args), get_result, key)
    _test_concurrent_update(results)


def test_multiple_concurrent_update(executor_cls):
    from functools import partial

    optimistic_dict = OptimisticLockingDict(executor_cls=executor_cls)
    partial_fn = partial(executor_cls, target=optimistic_dict.optimistic_update)
    key = "name"

    def get_result(partial_fn, key, i):
        task = partial_fn(args=(key, i))
        task.start()
        return task.join()

    results = _concurrent_update(partial_fn=partial_fn, get_result=get_result, key=key)
    last_result = optimistic_dict.get(key)
    expected_result = 5
    assert last_result == expected_result, f"Expected last value is {expected_result}, but got %s" % last_result
    _test_concurrent_update(results)


def run_tests():
    tests = {
        ("Test test_concurrent_update                 ", test_concurrent_update, ()),
        # ("Test test_multiple_process_updates          ", test_multiple_concurrent_update, (ResultProcess,)),
        # ("Test test_multiple_thread_updates           ", test_multiple_concurrent_update, (ResultThread,)),
    }

    for test_name, test, args in tests:
        try:
            prefix = f"Running [{test_name}]"
            test(*args)
            logger.info(f"{prefix} Succeeded")
        except AssertionError as e:
            logger.exception(e)
            logger.error(f"{prefix} Failed => {e}")
        except Exception as e:
            logger.exception(e)
            logger.critical(f"{prefix} Exception => {e}")


if __name__ == "__main__":
    from importlib import import_module

    import_module("utils.logger.init")
    run_tests()
