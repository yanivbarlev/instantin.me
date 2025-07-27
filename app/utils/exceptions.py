from fastapi import HTTPException, status


class StorefrontNotFoundError(HTTPException):
    """Exception raised when storefront is not found"""
    def __init__(self, detail: str = "Storefront not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class SlugAlreadyExistsError(HTTPException):
    """Exception raised when slug already exists"""
    def __init__(self, detail: str = "Slug already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedError(HTTPException):
    """Exception raised when user is not authorized"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(HTTPException):
    """Exception raised when validation fails"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class ProductNotFoundError(HTTPException):
    """Exception raised when product is not found"""
    def __init__(self, detail: str = "Product not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class OrderNotFoundError(HTTPException):
    """Exception raised when order is not found"""
    def __init__(self, detail: str = "Order not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InsufficientInventoryError(HTTPException):
    """Exception raised when there's insufficient inventory"""
    def __init__(self, detail: str = "Insufficient inventory"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class PaymentError(HTTPException):
    """Exception raised when payment processing fails"""
    def __init__(self, detail: str = "Payment processing failed"):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail)


class DropNotFoundError(HTTPException):
    """Exception raised when drop is not found"""
    def __init__(self, detail: str = "Drop not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class RaffleNotFoundError(HTTPException):
    """Exception raised when raffle is not found"""
    def __init__(self, detail: str = "Raffle not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class RaffleClosedError(HTTPException):
    """Exception raised when trying to enter a closed raffle"""
    def __init__(self, detail: str = "Raffle is closed"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class MaxTicketsExceededError(HTTPException):
    """Exception raised when user tries to buy more tickets than allowed"""
    def __init__(self, detail: str = "Maximum tickets per user exceeded"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail) 