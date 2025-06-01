import logging
from datetime import datetime
from pydantic.dataclasses import dataclass

import streamlit as st
import requests
from streamlit_feedback import streamlit_feedback

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%d-%m-%Y_%H')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)


@dataclass
class ChatMessage:
    """
    Dataclass used to store the role and content of a chat message.
    role should be either "user" or "assistant".
    """

    role: str
    content: str


def init_state() -> None:
    """
    Initialize the Streamlit session state.
    """
    init_dict = {
        "chat_history": [],
        "context": [],
    }

    for key, value in init_dict.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "session_id" not in st.session_state:
        resp = requests.post(
            url="http://medchat-backend:5050/start_session",
            json={"user_id": 1},  # Hard code to 1 for testing purposes
        )

        if resp.status_code == 200:
            st.session_state["session_id"] = resp.json()
        else:
            st.error("Failed to create a session. Check logs.")


def parse_context(context: list[dict]) -> str:

    sources = [
        f"['{chunk['title']}'](http://localhost:9090/{chunk['filename']}#page={chunk['start_page'] + 1})"
        for chunk in context
        if chunk.get("title") and chunk.get("authors")
    ]

    sources = set(sources)

    return sources


def _submit_feedback(user_response: bool, emoji=None):

    is_good = True if user_response["score"] == "👍" else False
    resp = requests.post(
        url="http://medchat-backend:5050/submit_feedback",
        json={
            "message_id": st.session_state["message_id"],
            "is_good": is_good,
        },
    )
    if resp.status_code != 200:
        logger.error("Failed to submit feedback.")
        st.error("Failed to submit feedback. Check logs.")
        return
    else:
        st.toast("Feedback submitted successfully!", icon=emoji)


def chatbot() -> None:
    """
    Chatbot interface.
    """

    chat_window = st.container(height=500)

    if st.session_state["chat_history"]:
        for message in st.session_state["chat_history"][:-1]:
            with chat_window:
                with st.chat_message(message.role):
                    st.write(message.content)

        # Add sources to last message
        with chat_window:
            with st.chat_message(st.session_state["chat_history"][-1].role):
                st.write(st.session_state["chat_history"][-1].content)
                if st.session_state["context"]:
                    sources = parse_context(st.session_state["context"])
                    st.write("### Sources")
                    for source in sources:
                        st.markdown(source)
                streamlit_feedback(
                    feedback_type="thumbs",
                    review_on_positive=False,
                    on_submit=_submit_feedback,
                )

    query = st.chat_input()

    if query:
        st.session_state["chat_history"].append(ChatMessage(role="user", content=query))
        with chat_window:
            with st.chat_message("user"):
                st.write(query)
            with st.spinner("Retrieving Answers..."):
                response = requests.post(
                    url="http://medchat-backend:5050/chat_response",
                    json={
                        "query": query,
                        "chat_history": "\n\n".join(
                            [
                                f"{message.role}: {message.content}"
                                for message in st.session_state["chat_history"]
                            ]
                        ),
                        "session_id": st.session_state["session_id"],
                    },
                    timeout=120,
                )

                if response.status_code == 200:
                    answer = response.json()["response"]
                    st.session_state["context"] = response.json().get("context", [])
                    st.session_state["message_id"] = response.json().get("message_id")

                else:
                    answer = (
                        "Sorry, I could not find an answer to that question."
                        "Try rephrasing your question or asking something else."
                    )
                st.session_state["chat_history"].append(
                    ChatMessage(role="assistant", content=answer)
                )
                st.rerun()


def title() -> None:
    """
    Title of the Streamlit app.
    """

    st.title("MedChat")
    st.write(
        (
            "Welcome to MedChat!"
            "Ask me questions about medical literature and I'll do my best to help you out!"
        )
    )


def main() -> None:
    """
    Main function to run the Streamlit app.
    """

    init_state()
    title()
    # hello_world()
    chatbot()


if __name__ == "__main__":
    st.set_page_config(
        page_title="MedChat",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="auto",
    )
    main()
