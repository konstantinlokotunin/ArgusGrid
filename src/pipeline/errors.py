"""
errors.py
Zentrale Sammlung anwendungsspezifischer Ausnahmen (Custom Exceptions).
"""

class PipelineError(Exception):
    """Basis-Exception für das ESG Data Sentinel."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message

class InvalidFileFormat(PipelineError):
    """Wird ausgelöst, wenn das Dateiformat kein CSV ist."""
    pass


class DataValidationError(PipelineError):
    """Wird ausgelöst, wenn eine Zeile kritische Fehler aufweist."""
    pass


class EmptyDatasetError(PipelineError):
    """Wird ausgelöst, wenn das Dataset nach der Filterung leer ist."""
    pass