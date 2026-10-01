"""
Custom exception classes for the application.
"""
class BungeWatchError(Exception):
    """
    Base class for every custom exception.
    """
    def __init__(self, message: str, *, debug_context: dict | None = None):
        super().__init__(message)
        self.message = message
        # Extra detail for logs ONLY — never shown to end users
        self.debug_context = debug_context or {}


# ---------------------------------------------------------------------------
#                    REPOSITORY-LAYER ERRORS 
# ---------------------------------------------------------------------------

class ResourceNotFoundError(BungeWatchError):
    """
    Raised when a lookup by ID/key finds nothing.
    Repository functions should raise this instead of silently returning
    None or an empty list.
    """

    def __init__(self, entity: str, identifier):
        super().__init__(
            f"{entity} not found: {identifier}",
            debug_context={"entity": entity, "identifier": str(identifier)},
        )
        self.entity = entity
        self.identifier = identifier


class ResourceAlreadyExistsError(BungeWatchError):
    """
    Raised when a resource creation attempt would violate a uniqueness constraint.
    """

    def __init__(self, entity: str, field: str, value):
        super().__init__(
            f"{entity} with {field}='{value}' already exists",
            debug_context={"entity": entity, "field": field, "value": str(value)},
        )

# ---------------------------------------------------------------------------
# External service errors — "something outside our own code failed"
# ---------------------------------------------------------------------------

class ExternalServiceError(BungeWatchError):
    """
    Base for failures calling out to something we don't control (e.g. an API, a scraper, a database, etc.)
    """

    def __init__(self, service_name: str, message: str, *, original_error: Exception | None = None):
        super().__init__(
            f"{service_name} error: {message}",
            debug_context={"service": service_name, "original_error": str(original_error) if original_error else None},
        )
        self.service_name = service_name
        self.original_error = original_error


class AIModelError(ExternalServiceError):
    """Raised when the AI summarization call fails or returns invalid output
    after retries"""
    pass


class NotificationDeliveryError(ExternalServiceError):
    """Raised when WhatsApp/SMS dispatch fails.."""
    pass


class ScraperError(ExternalServiceError):
    """Raised when a scraper can't reach or parse a source site"""
    pass