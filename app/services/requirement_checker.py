from app.models.requirement import Requirement


class RequirementChecker:
    """
    Checks whether we have enough information
    to recommend assessments.
    """

    def find_missing(self, requirement: Requirement) -> list[str]:

        missing = []

        # FIX: the spec's own expected clarifying question is
        # "Please provide the job level, role, or years of experience" —
        # an OR, not a strict requirement for `role` specifically. The
        # previous version required `role` alone, which meant a query
        # like "CXOs, director-level positions, 15+ years experience"
        # (role=None, job_levels=['Director'], experience_level='Senior')
        # kept re-asking "which role?" forever, even though the audience
        # was already clearly specified via job level + experience.
        has_role = bool(requirement.role)
        has_job_level = bool(requirement.job_levels)
        has_experience = bool(requirement.experience_level)

        if not (has_role or has_job_level or has_experience):
            missing.append("audience")

        if not requirement.purpose:
            missing.append("purpose")

        return missing

    def is_complete(self, requirement: Requirement) -> bool:
        return len(self.find_missing(requirement)) == 0