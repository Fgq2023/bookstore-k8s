"""Pydantic request/response validation schemas."""
from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationError


def format_validation_errors(exc: ValidationError) -> dict:
    """Convert Pydantic ValidationError into a user-friendly dict.

    Example output:
        {"field": "quantity", "message": "must be >= 1"}
    """
    errors = exc.errors()
    if not errors:
        return {"message": "Validation failed"}
    first = errors[0]
    loc = first.get("loc", [])
    field = loc[-1] if loc else "request"
    msg = first.get("msg", "Invalid value")
    # Replace pydantic-isms with friendlier wording
    msg = msg.replace("Input should be ", "must be ")
    msg = msg.replace("greater than ", "> ")
    msg = msg.replace("greater than or equal to ", ">= ")
    msg = msg.replace("less than ", "< ")
    msg = msg.replace("less than or equal to ", "<= ")
    return {"field": field, "message": msg}


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class CartAddRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    book_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)


class CartUpdateRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)


class OrderCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


class PaymentRequest(BaseModel):
    order_id: int = Field(..., gt=0)


class AdminStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r'^(pending|confirmed|shipped|delivered|cancelled)$')


class BookCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=10, max_length=20)
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(default=0, ge=0)


class BookUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=255)
    isbn: str | None = Field(default=None, min_length=10, max_length=20)
    price: float | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)


class BookListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)

    @field_validator('per_page', mode='before')
    @classmethod
    def cap_per_page(cls, v):
        return min(int(v), 100)


class OrderListQuery(BaseModel):
    session_id: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)

    @field_validator('per_page', mode='before')
    @classmethod
    def cap_per_page(cls, v):
        return min(int(v), 100)
