class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, entity: str, entity_id: int):
        super().__init__(404, "not_found", "Resource not found")


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(400, "validation_error", message)


class AuthError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(401, "auth_error", message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(403, "forbidden", message)
