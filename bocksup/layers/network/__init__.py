"""
Pachetul de rețea.

Acest pachet conține clasele care gestionează conexiunile la nivel 
de rețea pentru comunicarea cu serverele WhatsApp.
"""

from .connection import WhatsAppConnection

__all__ = ['WhatsAppConnection']