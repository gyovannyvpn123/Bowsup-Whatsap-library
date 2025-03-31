"""
Registration module for WhatsApp.

This module provides functionality for registering a new WhatsApp account,
including requesting a verification code via SMS or voice call and validating
the code to receive account credentials.
"""

from bocksup.registration.client import RegistrationClient

__all__ = ['RegistrationClient']