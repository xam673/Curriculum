class AppError(Exception):
    """Base error for the business logic layer. main.py turns it into an HTTP response."""
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class PermissionDeniedError(AppError):
    status_code = 403