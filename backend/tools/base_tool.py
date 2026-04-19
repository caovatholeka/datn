"""
1. base_tool.py
Abstract base class cho tất cả các tool trong hệ thống.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract interface buộc tất cả tools phải implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tên định danh duy nhất của tool."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Mô tả chức năng của tool, dùng để LLM hiểu khi nào gọi tool này."""
        ...

    @abstractmethod
    def run(self, **kwargs: Any) -> dict:
        """
        Thực thi logic nghiệp vụ của tool.
        Returns: dict chuẩn hóa với ít nhất key 'status'.
        KHÔNG BAO GIỜ để exception thoát ra ngoài.
        """
        ...

    def __repr__(self) -> str:
        return f"<Tool name='{self.name}'>"
