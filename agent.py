"""Self-learning chat agent: Mem0 long-term memory + a feedback loop.

How it learns (the model's weights never change, its memory does):
  1. Before every reply, it searches memory for relevant facts and lessons.
  2. After every reply, the exchange is saved so Mem0 can extract new facts.
  3. You can give feedback: /good or /bad <what it should have done>.
     Feedback is stored as explicit lessons and used on future questions.

Commands: /good   /bad <correction>   /memories   /quit
"""
import os
import time

from dotenv import load_dotenv
from mem0 import Memory
from google import genai
from google.genai import types

load_dotenv()

# --- Free setup: Google Gemini (key from aistudio.google.com/app/apikey) ---
# Put GOOGLE_API_KEY=... in your .env file. No OpenAI key needed.
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
MODEL = os.getenv("MODEL", "gemini-3.8-flash")  # change in .env if this one is not free for you

# Chat replies: Google's own library (same one Mem0 uses). 60-second timeout.
client = genai.Client(
    api_key=GOOGLE_API_KEY,
    http_options=types.HttpOptions(timeout=60000),
)

# Memory: Mem0 using Gemini for extraction + embeddings, stored locally in ./mem0_db
memory = Memory.from_config(
    {
        "llm": {
            "provider": "gemini",
            "config": {"model": MODEL, "api_key": GOOGLE_API_KEY, "temperature": 0.2},
        },
        "embedder": {
            "provider": "gemini",
            "config": {
                "model": "models/gemini-embedding-001",
                "api_key": GOOGLE_API_KEY,
                "embedding_dims": 768,
            },
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "self_learning_agent",
                "path": "./mem0_db",
                "embedding_model_dims": 768,
            },
        },
    }
)


def recall(query: str, user_id: str, k: int = 5) -> list[str]:
    res = memory.search(query=query, filters={"user_id": user_id}, top_k=k)
    items = res["results"] if isinstance(res, dict) else res
    return [r["memory"] for r in items]


def chat(message: str, user_id: str) -> str:
    memories = recall(message, user_id)
    memory_block = "\n".join(f"- {m}" for m in memories) or "- (nothing yet)"
    system = (
        "You are a helpful assistant that improves over time.\n"
        "Below are things you have learned about this user and lessons from "
        "past feedback. Apply them when relevant.\n"
        f"Memory:\n{memory_block}"
    )
    # Retry up to 3 times: Google sometimes says "high demand" (503) for a moment.
    answer = None
    for attempt in range(3):
        try:
            reply = client.models.generate_content(
                model=MODEL,
                contents=message,
                config=types.GenerateContentConfig(system_instruction=system),
            )
            answer = reply.text or "(no answer returned)"
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))

    # Save the exchange so Mem0 can extract durable facts from it.
    # If saving fails (e.g. Google is busy), still show the answer.
    try:
        memory.add(
            [{"role": "user", "content": message}, {"role": "assistant", "content": answer}],
            user_id=user_id,
        )
    except Exception as e:
        print(f"(Could not save to memory this time: {e})")
    return answer


def save_lesson(text: str, user_id: str) -> None:
    memory.add([{"role": "user", "content": text}], user_id=user_id)


def show_memories(user_id: str) -> None:
    res = memory.get_all(filters={"user_id": user_id})
    items = res["results"] if isinstance(res, dict) else res
    if not items:
        print("  (no memories yet)")
    for m in items:
        print(f"  - {m['memory']}")


def main() -> None:
    user_id = input("User name (memories are kept per user): ").strip() or "demo_user"
    print("Chat started. Commands: /good  /bad <correction>  /memories  /quit")
    last_q, last_a = None, None

    while True:
        text = input("\nYou: ").strip()
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/memories":
            show_memories(user_id)
            continue
        if text == "/good":
            if last_q:
                save_lesson(
                    f"The user liked this kind of answer. Question: {last_q[:200]} "
                    f"Answer style that worked: {last_a[:300]}",
                    user_id,
                )
                print("Noted, I'll keep doing that.")
            continue
        if text.startswith("/bad"):
            correction = text[4:].strip()
            if last_q and correction:
                save_lesson(
                    f"Lesson: for a question like '{last_q[:200]}', my answer was "
                    f"not good. The user wanted: {correction}",
                    user_id,
                )
                print("Lesson saved. I'll apply it next time.")
            else:
                print("Usage: /bad <what I should have done>")
            continue

        answer = chat(text, user_id)
        last_q, last_a = text, answer
        print(f"\nAI: {answer}")


if __name__ == "__main__":
    main()