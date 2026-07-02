from app.models.requirement import Requirement


class RequirementValidator:
    """
    Determines whether we have enough information
    to recommend assessments or need clarification.
    """

    def validate(
        self,
        requirement: Requirement,
    ) -> tuple[bool, list[str]]:

        missing = []

        # Mandatory fields
        if not requirement.role:
            missing.append("role")

        if not requirement.purpose:
            missing.append("purpose")

        # Confidence safeguard
        if (
            requirement.confidence is not None
            and requirement.confidence < 0.70
        ):
            missing.append("confidence")

        return len(missing) == 0, missing