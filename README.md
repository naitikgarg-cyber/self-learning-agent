# Self-Learning Agent (Mem0 + Gemini + feedback loop)

A small chat agent that improves over time. It uses Mem0 for long-term memory and
Google Gemini (free tier) for answers. The model's weights don't change; the agent
learns by saving facts and lessons, and retrieving them on future questions.

Inspired by Dave Ebbelaar's tutorial "How to Build Self-Learning AI Agents
(Python Tutorial)" (YouTube).

## How it learns

1. Before each reply, it searches memory for relevant facts and lessons.
2. After each reply, the exchange is saved and Mem0 extracts durable facts.
3. You can give feedback: `/good` or `/bad <what it should have done>`.
   Feedback is stored as lessons and used on future questions.

Commands: `/good`  `/bad <correction>`  `/memories`  `/quit`

## Setup

1. Install Python 3.10+.
2. Create and activate a virtual environment, then install packages:

       python -m venv .venv
       .venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
       pip install -r requirements.txt

3. Get a free Gemini API key at https://aistudio.google.com/app/apikey
4. Copy `.env.example` to `.env` and put your key in it:

       GOOGLE_API_KEY=your-key-here
       MODEL=gemini-3.5-flash-lite

   Never commit `.env` to Git (it is listed in `.gitignore`).
5. Run:

       python agent.py

Use the same user name each time so the agent keeps your memories.

## Notes

- Memories are stored locally in the `mem0_db` folder. Delete it to reset the agent.
- Model names change over time. If you get a 404 "model not found" error,
  check the error text for the suggested replacement and update `MODEL` in `.env`.
- On the free tier you may hit rate limits (429). Wait a few minutes and retry.
- Warnings about spaCy or fastembed are optional extras and can be ignored.

## Ideas for next steps

- Replace manual `/good` and `/bad` with an automatic signal (tests passing, LLM judge).
- Compare answers with memory on and off over a fixed set of test questions.
- Add tools (web search, code execution) so the agent can learn from more than chat.