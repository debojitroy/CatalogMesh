from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Product(Strict):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    title: str = Field(min_length=2, max_length=300)
    description: str = Field(default="", max_length=1200)
    source_category: str = Field(default="", max_length=200)
    brand: str = Field(default="", max_length=100)


class Supplier(Strict):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(default="Custom feed", max_length=80)
    products: list[Product] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_products(self):
        if len({p.id for p in self.products}) != len(self.products):
            raise ValueError("Product IDs must be unique within a supplier")
        return self


class Category(Strict):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    path: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=2, max_length=400)


class Marketplace(Strict):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(default="Custom taxonomy", max_length=80)
    version: str = Field(min_length=1, max_length=40)
    categories: list[Category] = Field(min_length=2, max_length=10000)

    @model_validator(mode="after")
    def unique_categories(self):
        ids = [c.id for c in self.categories]
        if len(set(ids)) != len(ids) or "unmatched" in ids:
            raise ValueError("Category IDs must be unique; unmatched is reserved")
        paths = [c.path for c in self.categories]
        if len(set(paths)) != len(paths) or "unmatched" in paths:
            raise ValueError("Category paths must be unique; unmatched is reserved")
        return self


class MappingRequest(Strict):
    supplier_ids: list[str] = Field(min_length=1, max_length=20)
    marketplace_ids: list[str] = Field(min_length=1, max_length=20)
    mode: Literal["recorded", "live"] = "recorded"


class ReviewRequest(Strict):
    category_id: str
    note: str = Field(min_length=2, max_length=500)
