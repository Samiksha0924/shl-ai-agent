import re
from app.services.catalog_reasoner import CatalogReasoner
from app.models.context import ConversationContext
from app.api.chat_schemas import ChatMessage, ChatRecommendationItem

MAX_TURNS = 8

# Keyword-level scope guard. This is a first pass — cheap and fast, but
# not exhaustive. If behavior-probe pass-rate on off-topic refusal is low,
# upgrade this to an LLM classification call instead.
OFF_TOPIC_BLOCKLIST = [
    "legal advice",
    "lawsuit",
    "sue my employer",
    "immigration",
    "visa sponsorship",

    "salary negotiation",
    "negotiate salary",

    "fire an employee",
    "terminate an employee",
    "layoff",

    "interview questions",
    "hiring pipeline",
    "onboard",
    "job description",

    "should i hire",
    "how many rounds of interviews",
]


INJECTION_PATTERNS = [
    r"ignore (all|any|the) (previous|prior) instructions",
    r"disregard (all|any|the) (previous|prior) instructions",
    r"you are now",
    r"act as (?!a hiring)",
    r"system prompt",
    r"reveal your (prompt|instructions)",
]

COMPARE_PATTERNS = [
    r"difference between",
    r"\bcompare\b",
    r"\bvs\.?\b",
    r"\bversus\b",
]

# Confirmation signals — used to decide whether the user is accepting a
# shortlist we already gave, vs. asking for something new. Deliberately
# narrow: false positives here would end the conversation prematurely.
CONFIRMATION_PATTERNS = [
    r"\bperfect\b",
    r"\bgreat\b",
    r"\bsounds good\b",
    r"\bthat works\b",
    r"\bthat'?s (what we need|good|fine|great|perfect)\b",
    r"^\s*(yes|yep|yup|great|perfect|good|thanks|thank you)\b",
    r"\blooks good\b",
    r"\bgo with (that|those|this)\b",
]

# Marker phrase this service itself always includes when it has committed
# to a shortlist. Used to detect, from message history alone (the API is
# stateless), whether a prior turn already recommended.
RECOMMENDATION_MARKER = "assessments that fit"

# Marker phrase CatalogReasoner always appends when it's flagging a gap
# (e.g. "no Rust test in the catalog") and asking permission to proceed
# with the closest available alternatives instead. Distinct from
# RECOMMENDATION_MARKER: this is an *offer*, not a committed shortlist —
# a "yes" here means "proceed with the fallback," not "confirm and end."
FALLBACK_OFFER_MARKER = "closest available"


class ChatOrchestrator:

    def __init__(self, engine, retriever):
        self.engine = engine
        self.retriever = retriever
        self.reasoner = CatalogReasoner()
        self._catalog_assessments = None

    # -------------------------
    # Scope / safety
    # -------------------------
    def _is_off_topic_or_injection(self, text: str) -> bool:
        lowered = text.lower()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                return True

        for phrase in OFF_TOPIC_BLOCKLIST:
            if phrase.lower() in lowered:
                return True

        return False

    def _is_compare_request(self, text: str) -> bool:
        lowered = text.lower()
        return any(re.search(p, lowered) for p in COMPARE_PATTERNS)

    def _is_confirmation(self, text: str) -> bool:
        lowered = text.lower().strip()
        return any(re.search(p, lowered) for p in CONFIRMATION_PATTERNS)

    def _has_prior_assistant_turn(self, messages: list[ChatMessage]) -> bool:
        return any(m.role == "assistant" for m in messages)

    def _has_prior_recommendation(self, messages: list[ChatMessage]) -> bool:
        return any(
            m.role == "assistant" and RECOMMENDATION_MARKER in m.content.lower()
            for m in messages
        )

    def _has_prior_fallback_offer(self, messages: list[ChatMessage]) -> bool:
        return any(
            m.role == "assistant" and FALLBACK_OFFER_MARKER in m.content.lower()
            for m in messages
        )

    def _cumulative_user_query(self, messages: list[ChatMessage]) -> str:
        user_turns = [m.content for m in messages if m.role == "user"]
        return " ".join(user_turns)

    def _contact_center_language_flow(self, messages: list[ChatMessage]):

        user_text = " ".join(
            m.content.lower()
            for m in messages
            if m.role == "user"
    )

    # Not a contact centre conversation
        if (
           "contact centre" not in user_text
            and "contact center" not in user_text
    ):
            return None

    # -------------------------
    # Turn 1: Ask language
    # -------------------------
        if (
            "english" not in user_text
            and "spanish" not in user_text
            and "french" not in user_text
            and "german" not in user_text
    ):
            return {
                "reply": (
                    "Before I shape the assessment stack, "
                    "what language are the calls in?"
            ),
                "recommendations": None,
                "end_of_conversation": False,
        }

    # -------------------------
    # Turn 2: English selected but accent missing
    # -------------------------
        if "english" in user_text:

            accent_patterns = [
                r"\bus\b",
                r"\busa\b",
                r"\bunited states\b",
                r"\buk\b",
                r"\bunited kingdom\b",
                r"\bbritish\b",
                r"\baustralian\b",
                r"\bindian\b",
        ]

            has_accent = any(
                re.search(pattern, user_text)
                for pattern in accent_patterns
        )

            print("=" * 60)
            print("USER TEXT:", repr(user_text))
            print("HAS ACCENT:", has_accent)

            for pattern in accent_patterns:
                if re.search(pattern, user_text):
                   print("MATCHED:", pattern)
            print("=" * 60)

            if not has_accent:
                return {
                "reply": (
                    "SHL provides multiple English spoken-language variants "
                    "(US, UK, Australian and Indian). "
                    "Which accent matches your operation?"
                ),
                "recommendations": None,
                "end_of_conversation": False,
            }

        return None
    # -------------------------
    # Compare — grounded in catalog data only
    # -------------------------
    def _load_catalog_assessments(self):
        if self._catalog_assessments is None:
            underlying = self.retriever.retriever
            underlying._load()
            self._catalog_assessments = underlying.assessments
        return self._catalog_assessments

    def _find_candidate_assessments(self, query: str, limit: int = 2):
        assessments = self._load_catalog_assessments()
        lowered_query = query.lower()

        scored = []
        for a in assessments:
            name_lower = (a.name or "").lower()
            if not name_lower:
                continue

            score = 0
            if name_lower in lowered_query:
                score = 100
            else:
                tokens = [t for t in re.split(r"[\s\-/]+", name_lower) if len(t) >= 3]
                for t in tokens:
                    if t in lowered_query:
                        score = max(score, 40)

            if score > 0:
                scored.append((score, a))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:limit]]

    def _handle_compare(self, query: str) -> dict:
        candidates = self._find_candidate_assessments(query, limit=2)

        if len(candidates) < 2:
            return {
                "reply": (
                    "I can compare specific SHL assessments, but I need the exact "
                    "assessment names to look them up in the catalog. Which two "
                    "would you like me to compare?"
                ),
                "recommendations": None,
                "end_of_conversation": False,
            }

        a, b = candidates[0], candidates[1]

        def describe(x):
            categories = ", ".join(getattr(x, "categories", []) or [])
            duration = getattr(x, "duration", None)
            duration_str = f"{duration} minutes" if duration else "duration not listed"
            desc = (getattr(x, "description", "") or "").strip()
            if len(desc) > 300:
                desc = desc[:300].rsplit(" ", 1)[0] + "..."
            return f"**{x.name}** ({categories}, {duration_str}): {desc}"

        reply = (
            f"Here's how they differ, based on the catalog:\n\n"
            f"{describe(a)}\n\n{describe(b)}"
        )

        return {
            "reply": reply,
            "recommendations": None,
            "end_of_conversation": False,
        }

    # -------------------------
    # Main entry point
    # -------------------------
    def handle(self, messages: list[ChatMessage]) -> dict:

        if len(messages) >= MAX_TURNS:
            return {
                "reply": "We've reached the maximum length for this conversation.",
                "recommendations": None,
                "end_of_conversation": True,
            }

        if not messages or messages[-1].role != "user":
            return {
                "reply": "I didn't receive a message to respond to.",
                "recommendations": None,
                "end_of_conversation": False,
            }

        last_user_message = messages[-1].content
        flow = self._contact_center_language_flow(messages)

        if flow:
            return flow

        if self._is_off_topic_or_injection(last_user_message):
            return {
                "reply": (
                    "I can only help with finding and comparing SHL assessments. "
                    "I'm not able to help with that request."
                ),
                "recommendations": None,
                "end_of_conversation": False,
            }

        if self._is_compare_request(last_user_message):
            return self._handle_compare(last_user_message)

        prior_recommendation_given = self._has_prior_recommendation(messages[:-1])
        prior_fallback_offer = self._has_prior_fallback_offer(messages[:-1])

        if prior_recommendation_given and self._is_confirmation(last_user_message):
            return {
                "reply": "Great — glad that works. Let me know if you need anything else.",
                "recommendations": None,
                "end_of_conversation": True,
            }

        cumulative_query = self._cumulative_user_query(messages)

        context = ConversationContext()
        result = self.engine.process(cumulative_query, context)

        if result["needs_clarification"]:
            return {
                "reply": result["question"],
                "recommendations": None,
                "end_of_conversation": False,
            }

        requirement = result["requirement"]

        # ---------------------------------------
        # Catalog reasoning before retrieval
        # ---------------------------------------
        catalog = self._load_catalog_assessments()

        reason = self.reasoner.analyze(
            cumulative_query,
            catalog,
        )

        # FIX: previously this only checked for confirmation of an
        # already-committed shortlist (RECOMMENDATION_MARKER), which a
        # fallback offer never sets — so "yes, go ahead" after
        # CatalogReasoner's "no Rust test... want me to build a shortlist
        # from the closest available?" had no way to ever be accepted,
        # and the same gap explanation repeated forever. Now also checks
        # for a prior fallback offer specifically.
        accepted_fallback = (
            (prior_recommendation_given or prior_fallback_offer)
            and self._is_confirmation(last_user_message)
        )

        if not reason["supported"] and not accepted_fallback:
            return {
                "reply": reason["reply"]
                + "\n\nWould you like me to build a shortlist from the closest available SHL assessments?",
                "recommendations": None,
                "end_of_conversation": False,
            }

        # ---------------------------------------
        # Continue with retrieval
        # ---------------------------------------
        assessments = self.retriever.retrieve(
            query=cumulative_query,
            requirement=requirement,
        )

        recommendations = [
            ChatRecommendationItem(
                name=a.name,
                url=str(a.url),
                test_type=getattr(a, "test_type", None),
            )
            for a in assessments
        ]

        refine_note = (
            " Updated based on your latest constraints."
            if prior_recommendation_given
            else ""
        )

        return {
            "reply": f"Here are {len(recommendations)} assessments that fit your requirements.{refine_note}",
            "recommendations": recommendations,
            "end_of_conversation": False,
        }