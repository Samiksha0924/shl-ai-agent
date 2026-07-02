import json
import re

from app.llm.groq_client import GroqClient
from app.llm.prompts import REQUIREMENT_EXTRACTION_PROMPT
from app.models.requirement import Requirement
from app.validators.requirement_validator import RequirementValidator


class RequirementExtractor:

    def __init__(self):
        self.client = GroqClient()
        self.validator = RequirementValidator()

    def _safe_json_parse(self, response: str):
        """
        Extract JSON safely from LLM response.
        """

        if not response:
            raise ValueError("Empty LLM response")

        cleaned = response.strip()
        cleaned = re.sub(r"```json", "", cleaned)
        cleaned = re.sub(r"```", "", cleaned)

        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            pass

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except (json.JSONDecodeError, TypeError):
                pass

        raise ValueError(f"Invalid LLM response:\n{response}")

    def _normalize(self, data: dict) -> dict:
        """
        Normalize LLM output into Requirement model fields.

        Never invent defaults.
        Missing information should remain None or [] so the
        clarification flow can detect it correctly.
        """

        return {
            "role": data.get("role"),
            "purpose": data.get("purpose"),
            "experience_level": data.get("experience_level"),
            "job_levels": data.get("job_levels", []),
            "skills": data.get("skills", []),
            "assessment_types": data.get("assessment_types", []),
            "max_duration": data.get(
                "max_duration",
                data.get("duration")
            ),
            "language": data.get("language"),
            "remote_testing": data.get(
                "remote_testing",
                data.get("remote")
            ),
            "adaptive_testing": data.get(
                "adaptive_testing",
                data.get("adaptive")
            ),
            "additional_constraints": data.get(
                "additional_constraints",
                []
            ),
            "confidence": data.get("confidence", 1.0),
        }

    def _empty_requirement(self) -> Requirement:
        """
        Returned only if extraction completely fails.
        """

        return Requirement(
            role=None,
            purpose=None,
            experience_level=None,
            job_levels=[],
            skills=[],
            assessment_types=[],
            max_duration=None,
            language=None,
            remote_testing=None,
            adaptive_testing=None,
            additional_constraints=[],
            confidence=0.0,
        )

    def extract(self, query: str) -> Requirement:

        response = self.client.chat(
            REQUIREMENT_EXTRACTION_PROMPT,
            query,
        )

        data = self._safe_json_parse(response)

        data = self._normalize(data)

        requirement = Requirement.model_validate(data)

        valid, errors = self.validator.validate(requirement)

        if not valid:
            print(
                "Requirement incomplete, waiting for clarification:",
                errors,
            )

        return requirement

    def extract_safe(self, query: str) -> Requirement:

        try:
            return self.extract(query)

        except Exception as e:

            print("Extractor failed:", e)

            return self._empty_requirement()