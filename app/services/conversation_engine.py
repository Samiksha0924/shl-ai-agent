from app.llm.requirement_extractor import RequirementExtractor
from app.models.context import ConversationContext
from app.models.requirement import Requirement
from app.state_machine.state import ConversationState

from app.services.requirement_checker import RequirementChecker
from app.services.clarification_service import ClarificationService


class ConversationEngine:

    def __init__(self):
        self.extractor = RequirementExtractor()
        self.checker = RequirementChecker()
        self.clarifier = ClarificationService()

    def _merge_requirements(
        self,
        existing: Requirement,
        new: Requirement,
    ) -> Requirement:
        """
        Merge newly extracted information into the existing requirement.
        Never overwrite existing values with None or empty lists.
        """

        # Simple fields
        for field in [
            "role",
            "purpose",
            "experience_level",
            "max_duration",
            "language",
            "remote_testing",
            "adaptive_testing",
        ]:
            value = getattr(new, field)

            if value not in [None, "", []]:
                setattr(existing, field, value)

        # Merge list fields
        for field in [
            "skills",
            "assessment_types",
            "job_levels",
            "additional_constraints",
        ]:
            old = getattr(existing, field)
            new_values = getattr(new, field)

            merged = list(dict.fromkeys(old + new_values))

            setattr(existing, field, merged)

        existing.confidence = max(
            existing.confidence,
            new.confidence,
        )

        return existing

    def process(
        self,
        user_message: str,
        context: ConversationContext,
    ):

        context.turns += 1

        context.history.append(user_message)

        extracted = self.extractor.extract_safe(user_message)

        print("NEW EXTRACTION:", extracted.model_dump())

        merged = self._merge_requirements(
            context.requirements,
            extracted,
        )

        context.requirements = merged

        print("MERGED REQUIREMENT:", merged.model_dump())

        try:
            missing = self.checker.find_missing(merged)
        except Exception as e:
            print("Checker failed:", e)
            missing = []

        if missing:

            context.state = ConversationState.COLLECTING_REQUIREMENTS

            return {
                "needs_clarification": True,
                "question": self.clarifier.generate(missing),
            }

        context.state = ConversationState.READY_FOR_RETRIEVAL

        return {
            "needs_clarification": False,
            "requirement": merged,
        }