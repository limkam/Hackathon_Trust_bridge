from fastapi import HTTPException, status


class TrustBridgeException(HTTPException):
    """Base exception for TrustBridge API."""
    pass


class CertificateNotFound(TrustBridgeException):
    def __init__(self, certificate_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate {certificate_id} not found"
        )


class StartupNotFound(TrustBridgeException):
    def __init__(self, startup_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup {startup_id} not found"
        )


class UserNotFound(TrustBridgeException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )


class InvalidCredentials(TrustBridgeException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


class BlockchainError(TrustBridgeException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Blockchain error: {message}"
        )


class UnauthorizedAccess(TrustBridgeException):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

