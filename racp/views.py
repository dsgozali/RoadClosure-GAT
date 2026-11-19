"""Compatibility exports for the Django page views."""

from .helpers.analytics import pdf_download, pdf_view
from .helpers.home import home
from .helpers.matrix import matrix
from .helpers.test import test


__all__ = ["home", "test", "matrix", "pdf_view", "pdf_download"]
