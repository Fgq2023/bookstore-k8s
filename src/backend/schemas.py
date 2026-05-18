"""Pydantic request/response validation schemas."""
from pydantic import BaseModel, Field, EmailStr, field_validator


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
