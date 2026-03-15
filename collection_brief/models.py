"""
Pydantic models for collection brief form configuration.

Mirrors the frontend TypeScript interfaces: FieldType, ChipOption, NestedChipOption,
FormField, FormConfig.
"""

from typing import Literal, Optional

from pydantic import BaseModel


FieldType = Literal[
    "chip-select",
    "text",
    "number",
    "select",
    "checkbox",
    "textarea",
    "radio",
    "tag-input",
    "nested-chip-select",
]


class ChipOption(BaseModel):
    """Option for chip-select, select, radio, or checkbox fields."""

    label: str
    value: str


class NestedChipOption(BaseModel):
    """Option for nested-chip-select fields; can have children for hierarchy."""

    label: str
    value: str
    multiSelect: Optional[bool] = None
    children: Optional[list["NestedChipOption"]] = None


NestedChipOption.model_rebuild()


class FormField(BaseModel):
    """Single form field definition."""

    id: str
    type: FieldType
    label: str
    required: Optional[bool] = None
    description: Optional[str] = None
    placeholder: Optional[str] = None
    prefix: Optional[str] = None
    multiSelect: Optional[bool] = None
    options: Optional[list[ChipOption]] = None
    nestedOptions: Optional[list[NestedChipOption]] = None
    defaultValue: Optional[str | list[str]] = None
    width: Optional[Literal["full", "half"]] = None
    maxTags: Optional[int] = None


class FormConfig(BaseModel):
    """Complete form configuration (question_data schema)."""

    id: str
    title: str
    description: Optional[str] = None
    submitLabel: Optional[str] = None
    fields: list[FormField]
    readOnly: Optional[bool] = None
