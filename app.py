"""Web chat interface for the self-learning agent (Streamlit).

Run with:  streamlit run app.py
It reuses the memory and chat logic from agent.py.
"""
import streamlit as st

from agent import chat, memory, save_lesson

st.set_page_config(page_title="Self-Learning Agent", page_icon="🧠")
st.title("🧠 Self-Learning Agent")
st.caption("It remembers what you tell it and learns from your feedback.")


def get_memories(uid: str) -> list[str]:
    res = memory.get_all(filters={"user_id": uid})
    items = res["results"] if isinstance(res, dict) else res
    return [m["memory"] for m in items]


# Who is chatting (memories are kept per user name)
user_id = st.sidebar.text_input("User name", value="test").strip() or "test"

# Reset the on-screen chat when the user name changes
if st.session_state.get("user") != user_id:
    st.session_state.user = user_id
    st.session_state.messages = []
    st.session_state.last_q = None
    st.session_state.last_a = None

# Show the conversation so far
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# New message
prompt = st.chat_input("Ask something...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = chat(prompt, user_id)
            except Exception as e:  # show errors in the page instead of crashing
                answer = f"Sorry, something went wrong: {e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_q = prompt
    st.session_state.last_a = answer

# Feedback on the latest answer
if st.session_state.get("last_q"):
    st.divider()
    col_good, col_bad = st.columns([1, 3])
    if col_good.button("👍 Good answer"):
        save_lesson(
            f"The user liked this kind of answer. Question: "
            f"{st.session_state.last_q[:200]} Answer style that worked: "
            f"{st.session_state.last_a[:300]}",
            user_id,
        )
        st.toast("Noted, I'll keep doing that.")
    with col_bad.form("bad_form", clear_on_submit=True):
        correction = st.text_input("👎 What should it have done instead?")
        if st.form_submit_button("Submit correction") and correction.strip():
            save_lesson(
                f"Lesson: for a question like '{st.session_state.last_q[:200]}', "
                f"my answer was not good. The user wanted: {correction.strip()}",
                user_id,
            )
            st.toast("Lesson saved. I'll apply it next time.")

# Sidebar: what the agent has learned so far
with st.sidebar:
    st.subheader("What I remember")
    try:
        saved = get_memories(user_id)
        if saved:
            for item in saved:
                st.write(f"- {item}")
        else:
            st.write("Nothing yet. New memories can take a few seconds to appear.")
    except Exception as e:
        st.write(f"Could not load memories: {e}")
