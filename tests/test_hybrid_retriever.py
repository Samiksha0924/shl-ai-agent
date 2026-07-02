from app.models.requirement import Requirement
from app.services.hybrid_retriever import HybridRetriever

retriever = HybridRetriever()

requirement = Requirement(

    role="Software Engineer",

    purpose="Hiring",

    job_levels=["Graduate"],

    remote_testing=True,
)

results = retriever.retrieve(

    query="Graduate software engineer cognitive assessment",

    requirement=requirement,

)

print()

for r in results:

    print("--------------------------------")

    print(r.name)

    print("Similarity :", round(r.similarity_score, 3))

    print("Final Score:", round(r.final_score, 3))

    print("Remote:", r.remote)

    print("Adaptive:", r.adaptive)