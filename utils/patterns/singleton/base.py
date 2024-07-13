"""
Design pattern: Singleton
设计模式: 单例模式
"""


class _Singleton:
    """Singleton class, can be inherited by other classes."""

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            # cls.__instance = super(_Singleton, cls).__new__(cls)
            # cls.__instance = object.__new__(cls)
        return cls.__instance


Singleton = type("SingleTon", (_Singleton,), {})

if __name__ == "__main__":
    Singleton = type("SingleTon", (_Singleton,), {})
    singleton_obj = Singleton("obj")
    print(singleton_obj)
    print(id(singleton_obj))
    singleton_obj2 = Singleton("obj2")
    print(singleton_obj2)
    print(id(singleton_obj2))
    print(singleton_obj == singleton_obj2)
    print(singleton_obj is singleton_obj2)
    print("-----" * 10)
    SingletonSecond = type("SingleTon", (_Singleton,), {})
    singleton_second = SingletonSecond("obj")
    for subclass in _Singleton.__subclasses__():
        print({subclass: getattr(subclass, "_Singleton__instance")})
    print(singleton_obj == singleton_second)
    print(singleton_obj is singleton_second)
