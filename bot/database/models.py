from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    user_id: int
    username: Optional[str]
    status: str  # 'guest', 'pending', 'verified', 'rejected'
    name: Optional[str] = None
    age: Optional[int] = None
    document_photo: Optional[str] = None

@dataclass
class Verification:
    user_id: int
    name: str
    age: int
    document_photo: str
    activity: str
    status: str  # 'pending', 'verified', 'rejected'

@dataclass
class Order:
    order_id: Optional[int]
    user_id: int
    item: str
    price: float
    address: str
    status: str  # 'pending', 'taken', 'completed'
    drop_id: Optional[int] = None