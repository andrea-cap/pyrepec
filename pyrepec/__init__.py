# -*- coding: utf-8 -*-

"""
Main package for pyrepec

This is module contain the main class, `RePEc` and misc supporting
code: Exceptions and error messages.

The RePEc authors' API is documented here: https://ideas.repec.org/api.html

"""

from .repec import Repec as Repec

__all__ = ["Repec"]
