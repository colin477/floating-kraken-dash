"""
Custom exception classes for better error handling
"""

class PasswordValidationError(Exception):
    """Raised when password validation fails"""
    def __init__(self, message: str, errors: list = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)

class EmailAlreadyExistsError(Exception):
    """Raised when attempting to create user with existing email"""
    def __init__(self, message: str = "Email already registered"):
        self.message = message
        super().__init__(self.message)

class UserCreationError(Exception):
    """Raised when user creation fails for database or system reasons"""
    def __init__(self, message: str = "Failed to create user"):
        self.message = message
        super().__init__(self.message)