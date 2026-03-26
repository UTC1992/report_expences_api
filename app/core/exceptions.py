class DomainError(Exception):
    """Base class for domain-level errors."""


class NotFoundError(DomainError):
    """Raised when an aggregate or entity does not exist."""


class ValidationError(DomainError):
    """Raised when domain or application validation fails."""


class DuplicateResourceError(DomainError):
    """Raised when a duplicate record would be persisted."""
