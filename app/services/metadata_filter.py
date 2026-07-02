from app.models.assessment import Assessment
from app.models.requirement import Requirement


class MetadataFilter:

    def filter(
        self,
        assessments: list[Assessment],
        requirement: Requirement,
    ) -> list[Assessment]:

        filtered = assessments

        # Job Level
        if requirement.job_levels:

            filtered = [
                a for a in filtered
                if any(
                    jl.lower() in [x.lower() for x in a.job_levels]
                    for jl in requirement.job_levels
                )
            ]

        # Duration
        if requirement.max_duration:

            filtered = [
                a for a in filtered
                if (
                    a.duration is None
                    or a.duration <= requirement.max_duration
                )
            ]

        # Remote
        if requirement.remote_testing is True:

            filtered = [
                a for a in filtered
                if a.remote
            ]

        # Adaptive
        if requirement.adaptive_testing is True:

            filtered = [
                a for a in filtered
                if a.adaptive
            ]

        return filtered