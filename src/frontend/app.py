import logging
from datetime import datetime
from pydantic.dataclasses import dataclass

import streamlit as st
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%d-%m-%Y_%H-%M')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)


@dataclass
class ChatMessage:
    """
    Dataclass used to store the author and content of a chat message.
    Author should be either "user" or "ai".
    """

    author: str
    content: str


def init_state() -> None:
    """
    Initialize the Streamlit session state.
    """
    init_dict = {
        "chat_history": [],
        "response": "",
    }

    for key, value in init_dict.items():
        if key not in st.session_state:
            st.session_state[key] = value


def chatbot() -> None:
    """
    Chatbot interface.
    """

    chat_window = st.container(height=500)

    for message in st.session_state["chat_history"]:
        with chat_window:
            with st.chat_message(message.author):
                st.write(message.content)

    query = st.chat_input()

    if query:
        st.session_state["chat_history"].append(
            ChatMessage(author="user", content=query)
        )
        with chat_window:
            with st.chat_message("user"):
                st.write(query)
            with st.spinner("Retrieving Answers..."):
                response = requests.post(
                    url="http://localhost:5050/chat_response",
                    json={
                        "query": query,
                        "chat_history": "\n\n".join(
                            [
                                f"{message.author}: {message.content}"
                                for message in st.session_state["chat_history"]
                            ]
                        ),
                    },
                )

                if response.status_code == 200:
                    answer = response.json()["response"]
                else:
                    answer = "Sorry, I could not find an answer to that question. Try rephrasing your question or asking something else."
                st.session_state["chat_history"].append(
                    ChatMessage(author="ai", content=answer)
                )
                st.rerun()


def title() -> None:

    st.title("MedChat")
    st.write(
        "Welcome to MedChat! Ask me questions about medical literature and I'll do my best to help you out!"
    )


def hello_world() -> None:

    button = st.button("Hello World")

    if button:
        response = requests.get(
            url="http://medchat-backend:5050/hello_world",
        )

        if response.status_code == 200:
            st.write(response.json())
        else:
            st.error(response)


def main() -> None:

    init_state()
    title()
    hello_world()
    # chatbot()


if __name__ == "__main__":
    st.set_page_config(
        page_title="MedChat",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="auto",
    )
    main()
