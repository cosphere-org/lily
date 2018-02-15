# -*- coding: utf-8 -*-

import importlib


def import_from_string(path):
    """
    Attempt to import a class from a string representation.

    From: django rest_framework

    """
    try:
        parts = path.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    except ImportError as e:
        msg = "Could not import '{}' for setting. {}: {}.".format(
            path, e.__class__.__name__, e)
        raise ImportError(msg)
