# -*- coding: utf-8 -*-


def singleton_decorator(cls):
    instance = {}

    def _singleton(*args, **kwargs):
        if cls not in instance:
            instance[cls] = cls(*args, **kwargs) 
        print(instance)
        return instance[cls]
    return _singleton
