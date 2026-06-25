"""Pydantic models for resume extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.plugins.base_models import PluginExtractionResult


class Experience(BaseModel):
    company: str = Field(description="Company name")
    role: str = Field(description="Job title/role")
    start_date: str = Field(description="Employment start date")
    end_date: str = Field(description="Employment start date")
    total_experience: int = Field(description="Total experience")
    duration: str = Field(description="Employment duration (e.g., '2020-2023')")
    description: str = Field(
        default="", description="Job description and responsibilities"
    )


class Education(BaseModel):
    institution: str = Field(description="School or university name")
    degree: str = Field(description="Degree obtained (e.g., B.Tech, MBA)")
    year: str = Field(description="Graduation year or period")


class ResumeExtraction(PluginExtractionResult):
    candidate_name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address")
    phone: str = Field(default="", description="Phone number")
    skills: list[str] = Field(
        default_factory=list, description="List of technical and soft skills"
    )
    experience: list[Experience] = Field(
        default_factory=list, description="Work experience entries"
    )
    education: list[Education] = Field(
        default_factory=list, description="Education history"
    )
