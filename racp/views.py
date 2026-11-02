"""Compatibility exports for the Django page views."""

from .pages.analytics import pdf_download, pdf_view
from .pages.home import home
from .pages.matrix import matrix


__all__ = ["home", "matrix", "pdf_view", "pdf_download"]
