from app.models.requirement import Requirement
from app.services.retriever import Retriever


class HybridRetriever:

    def __init__(self):
        self.retriever = Retriever()

    def _safe_list(self, value):
        """Ensures we always work with a list."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _is_valid_candidate(self, assessment, requirement: Requirement):

        assessment_job_levels = self._safe_list(getattr(assessment, "job_levels", None))

        # If job level exists → must match at least one
        if requirement.job_levels:
            if not any(
                level in assessment_job_levels
                for level in requirement.job_levels
            ):
                return False

        return True

    def retrieve(
        self,
        query: str,
        requirement: Requirement,
        top_k: int = 10,
    ):

        # STEP 1: widen FAISS search
        candidates = self.retriever.search(
            query,
            top_k=30,
        )

        filtered = []

        for assessment in candidates:

            # HARD FILTER (safe)
            if not self._is_valid_candidate(assessment, requirement):
                continue

            # SAFE similarity score
            score = getattr(assessment, "similarity_score", 0.0)

            # Job level boost
            assessment_job_levels = self._safe_list(getattr(assessment, "job_levels", None))

            if (
                requirement.job_levels
                and any(
                    level in assessment_job_levels
                    for level in requirement.job_levels
                )
            ):
                score += 0.20

            # Remote preference
            if (
                getattr(requirement, "remote_testing", False)
                and getattr(assessment, "remote", False)
            ):
                score += 0.05

            # Adaptive preference
            if (
                getattr(requirement, "adaptive_testing", False)
                and getattr(assessment, "adaptive", False)
            ):
                score += 0.05

            # Duration HARD FILTER: "under X minutes" is a disqualifying
            # constraint, not a soft preference. Anything over gets dropped.
            max_duration = getattr(requirement, "max_duration", None)
            assessment_duration = getattr(assessment, "duration", None)
            if max_duration and assessment_duration is not None:
                if assessment_duration > max_duration:
                    continue

            # Assessment type / category penalty (e.g. "cognitive" -> "A").
            # Requires the catalog scraper to populate assessment.test_type.
            requirement_types = self._safe_list(getattr(requirement, "assessment_types", None))
            assessment_type = getattr(assessment, "test_type", None)
            if requirement_types and assessment_type not in requirement_types:
                score -= 0.25

            # HARD PENALTY for role mismatch
            if requirement.role:
                assessment_name = (getattr(assessment, "name", "") or "").lower()
                if requirement.role.lower() not in assessment_name:
                    score -= 0.25

            assessment.__dict__["final_score"] = score

            filtered.append(assessment)

        # fallback safety: if EVERYTHING got filtered out, don't silently
        # ignore constraints — relax only the role/category penalty, but
        # keep respecting job_levels and max_duration since those are
        # explicit user-stated constraints.
        if not filtered:
            relaxed = []
            for assessment in candidates:
                max_duration = getattr(requirement, "max_duration", None)
                assessment_duration = getattr(assessment, "duration", None)
                if max_duration and assessment_duration is not None:
                    if assessment_duration > max_duration:
                        continue
                relaxed.append(assessment)
            return relaxed[:5] if relaxed else candidates[:5]

        filtered.sort(
            key=lambda x: getattr(x, "final_score", 0),
            reverse=True,
        )

        return filtered[:5]