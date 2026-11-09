"""Compatibility exports for the Django page views."""

from .helpers.analytics import pdf_download, pdf_view
from .helpers.home import home
from .helpers.matrix import matrix


__all__ = ["home", "matrix", "pdf_view", "pdf_download"]
