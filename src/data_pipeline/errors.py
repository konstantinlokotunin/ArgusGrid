"""
errors.py
Zentrale Definition anwendungsspezifischer Ausnahmen (Custom Exceptions) für das ArgusGrid Projekt.
"""

class ArgusGridError(Exception):
    """Basis-Ausnahme für das gesamte Projekt."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message

class APIConnectionError(ArgusGridError):
    """Wird geworfen, wenn die REST-APIs von ENTSO-E/G nicht erreichbar sind."""
    pass

class DataValidationError(ArgusGridError):
    """Wird geworfen, wenn Datenzeilen korrupt sind."""
    pass