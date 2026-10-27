"""Kleine Ausnahmehierarchie für erwartete Fehler an Systemgrenzen."""

class ArgusGridError(Exception):
    """Gemeinsame Grundklasse für alle selbst definierten Projektfehler."""


class ConfigurationError(ArgusGridError):
    """Eine notwendige Einstellung fehlt oder ist ungültig."""


class APIConnectionError(ArgusGridError):
    """Ein Datenabruf ist an einem Netzwerk- oder HTTP-Problem gescheitert."""


class DataValidationError(ArgusGridError):
    """Eingaben oder gelieferte Daten sind für den Arbeitsschritt ungültig."""


class EmptyDatasetError(DataValidationError):
    """Für den aktuellen Arbeitsschritt sind keine Daten vorhanden."""