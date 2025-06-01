import logging
from datetime import datetime
from pydantic.dataclasses import dataclass

import streamlit as st
import requests

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


def parse_context(context: list[dict]) -> str:

    sources = [
        f"['{chunk['title']}'](http://localhost:9090/{chunk['filename']}#page={chunk['start_page'] + 1}) by {chunk['authors']} "
        for chunk in context
        if chunk.get("title") and chunk.get("authors")
    ]

    sources = set(sources)

    return sources


def chatbot() -> None:
    """
    Chatbot interface.
    """

    chat_window = st.container(height=500)

    for message in st.session_state["chat_history"]:
        with chat_window:
            with st.chat_message(message.role):
                st.write(message.content)

    if st.session_state["context"]:
        sources = parse_context(st.session_state["context"])
        with chat_window:
            st.write("### Sources")
            for source in sources:
                st.markdown(source)

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
                    },
                    timeout=300,
                )

                if response.status_code == 200:
                    answer = response.json()["response"]
                    st.session_state["context"] = response.json().get("context", [])

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
