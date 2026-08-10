# -*- coding: utf-8 -*-

"""Public package interface for the PyRepec client.

The package exposes :class:`Repec`, the main client for the RePEc API. Result
and error models are available from :mod:`pyrepec.models`.
"""

from .repec import Repec as Repec

__all__ = ["Repec"]
