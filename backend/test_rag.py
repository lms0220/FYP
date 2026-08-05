from services.llm_service import generate_scam_explanation
from services.rag_service import retrieve_context

TEST_INPUT = "Your bank account has been suspended. Click this link to verify."


if __name__ == "__main__":
    context = retrieve_context(TEST_INPUT, k=3)
    print("Retrieved context:")
    for item in context:
        print(f"- {item['source']} (score={item['score']})")

    print("\nLLM explanation:")
    print(generate_scam_explanation(TEST_INPUT, context))
