import json

from app.services.json_cleaner import JsonCleaner
import re
from pathlib import Path
from typing import List

from app.core.constants import RAW_DATA_PATH
from app.models.assessment import Assessment
from app.services.logger import app_logger


class CatalogLoader:
    """
    Loads, validates and normalizes the SHL catalog.
    """

    # Maps SHL's human-readable category labels ("keys" in the raw
    # catalog) onto the single-letter test_type codes used elsewhere in
    # the pipeline (Requirement.assessment_types, category-match scoring
    # in HybridRetriever, and the /chat test_type field). An assessment
    # can carry multiple "keys" (e.g. both "Knowledge & Skills" and
    # "Simulations") — we take the first recognized one as the primary
    # type, since downstream code expects a single code per assessment.
    CATEGORY_TO_TEST_TYPE = {
        "Ability & Aptitude": "A",
        "Personality & Behavior": "P",
        "Knowledge & Skills": "K",
        "Simulations": "S",
        "Biodata & Situational Judgment": "B",
        "Competencies": "C",
        "Development & 360": "D",
        "Assessment Exercises": "S",
    }

    def __init__(self, catalog_path: Path | None = None):
        self.catalog_path = catalog_path or RAW_DATA_PATH / "catalog.json"

    def load(self) -> List[Assessment]:
        """
        Load catalog and return normalized Assessment objects.
        """
        app_logger.info(f"Loading catalog from {self.catalog_path}")

    
        clean_json = JsonCleaner.clean(self.catalog_path)

        raw_catalog = json.loads(clean_json)

        assessments: List[Assessment] = []

        for record in raw_catalog:
            try:
                assessment = self._normalize(record)
                assessments.append(assessment)

            except Exception as ex:
                app_logger.error(
                    f"Failed to load assessment "
                    f"{record.get('entity_id','UNKNOWN')} : {ex}"
                )

        app_logger.info(f"Loaded {len(assessments)} assessments")

        return assessments

    def _normalize(self, record: dict) -> Assessment:

        duration = self._parse_duration(
            record.get("duration", "")
        )

        adaptive = self._parse_bool(
            record.get("adaptive", "")
        )

        remote = self._parse_bool(
            record.get("remote", "")
        )

        test_type = self._resolve_test_type(
            record.get("keys", [])
        )

        embedding_text = self._build_embedding_text(record)

        return Assessment(

            entity_id=str(record.get("entity_id")),

            name=record.get("name", ""),

            url=record.get("link"),

            description=record.get("description", ""),

            categories=record.get("keys", []),

            job_levels=record.get("job_levels", []),

            languages=record.get("languages", []),

            duration=duration,

            remote=remote,

            adaptive=adaptive,

            status=record.get("status", "Unknown"),

            test_type=test_type,

            embedding_text=embedding_text,
        )

    @classmethod
    def _resolve_test_type(cls, keys: list) -> str | None:
        for key in keys or []:
            mapped = cls.CATEGORY_TO_TEST_TYPE.get(key)
            if mapped:
                return mapped
        return None

    @staticmethod
    def _parse_duration(duration: str):

        match = re.search(r"\d+", duration)

        if match:
            return int(match.group())

        return None

    @staticmethod
    def _parse_bool(value: str):

        return str(value).strip().lower() in {
            "yes",
            "true",
            "1",
        }

    @staticmethod
    def _build_embedding_text(record: dict) -> str:

        return f"""
Assessment Name:
{record.get("name","")}

Description:
{record.get("description","")}

Categories:
{", ".join(record.get("keys",[]))}

Job Levels:
{", ".join(record.get("job_levels",[]))}

Languages:
{", ".join(record.get("languages",[]))}

Duration:
{record.get("duration","")}

Remote:
{record.get("remote","")}

Adaptive:
{record.get("adaptive","")}
""".strip()