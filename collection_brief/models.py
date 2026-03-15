"""
Pydantic models for collection brief form configuration.

Mirrors the frontend TypeScript interfaces: FieldType, ChipOption, FormField, FormConfig.
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
]


class ChipOption(BaseModel):
    """Option for chip-select, select, radio, or checkbox fields."""

    label: str
    value: str


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
    defaultValue: Optional[str | list[str]] = None
    width: Optional[Literal["full", "half"]] = None


class FormConfig(BaseModel):
    """Complete form configuration (question_data schema)."""

    id: str
    title: str
    description: Optional[str] = None
    submitLabel: Optional[str] = None
    fields: list[FormField]
