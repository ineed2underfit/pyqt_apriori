"""
Service layer modules.

Currently exposes AprioriService which wraps the Bayes Apriori pipeline so that
UI handlers can orchestrate it without touching CLI logic directly.
"""

from .apriori_service import AprioriService  # noqa: F401
