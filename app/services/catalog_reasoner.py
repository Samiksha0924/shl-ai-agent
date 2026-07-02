from typing import List

from app.models.assessment import Assessment


class CatalogReasoner:
    """
    Checks whether requested technologies/skills exist
    in the SHL catalog before retrieval.

    If not, returns a recruiter-style explanation
    instead of blindly retrieving semantic matches.
    """

    def analyze(
        self,
        query: str,
        assessments: List[Assessment],
    ) -> dict:

        import re

        query_lower = query.lower()

        # -----------------------------
        # Technologies we actually care about
        # -----------------------------
        TECH_KEYWORDS = {
            "python",
            "java",
            "javascript",
            "typescript",
            "rust",
            "golang",
            "go",
            "c",
            "c++",
            "c#",
            "dotnet",
            ".net",
            "spring",
            "springboot",
            "django",
            "flask",
            "react",
            "angular",
            "vue",
            "node",
            "nodejs",
            "node.js",
            "sql",
            "mysql",
            "postgresql",
            "oracle",
            "mongodb",
            "redis",
            "linux",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "terraform",
            "ansible",
            "networking",
            "cybersecurity",
            "sap",
            "salesforce",
            "mulesoft",
        }

        # Remove punctuation
        words = re.findall(r"[a-zA-Z0-9.+#-]+", query_lower)

        keywords = [
            word
            for word in words
            if word in TECH_KEYWORDS
        ]

        if not keywords:
            return {"supported": True}

        # -----------------------------
        # Build searchable catalog
        # -----------------------------
        catalog_text = []

        for assessment in assessments:

            text = " ".join(
                [
                    assessment.name or "",
                    getattr(assessment, "description", "") or "",
                    " ".join(getattr(assessment, "categories", []) or []),
                ]
            ).lower()

            catalog_text.append(text)

        missing = []

        for keyword in keywords:

            exists = any(keyword in text for text in catalog_text)

            if not exists:
                missing.append(keyword)

        if not missing:
            return {"supported": True}

        reply = (
            "SHL's catalog doesn't currently contain assessments specifically for: "
            + ", ".join(missing)
            + ". "
            "I'll recommend the closest available assessments instead."
        )

        return {
            "supported": False,
            "reply": reply,
        }