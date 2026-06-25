"""Resume plugin manifest."""

from backend.app.plugins.resume.models import ResumeExtraction
from backend.app.plugins.resume.extractor import ResumePlugin

MANIFEST = {
    "id": "resume",
    "name": "Resume",
    "version": "1.0.0",
    "description": "Parses resumes/CVs and extracts structured candidate information",
    "output_model": ResumeExtraction,
    "graph_worthy": True,
    "class": "backend.app.plugins.resume.extractor.ResumePlugin",
}