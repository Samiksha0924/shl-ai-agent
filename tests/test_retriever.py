from app.services.retriever import Retriever

retriever = Retriever()

results = retriever.search(
    "I need a cognitive and personality assessment for graduate software engineers",
    top_k=5,
)

print("=" * 80)

for i, assessment in enumerate(results, start=1):
    print(f"{i}. {assessment.name}")
    print(f"Score : {assessment.similarity_score:.4f}")
    print(f"Duration : {assessment.duration}")
    print(f"Remote : {assessment.remote}")
    print(f"Adaptive : {assessment.adaptive}")
    print("-" * 80)