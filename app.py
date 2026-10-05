import os
import time
import random

import requests
import streamlit as st
from dotenv import load_dotenv

from knowledge_base import KNOWLEDGE_BASE


# --------------------------------------------------
# LOAD API KEY
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-3.8-flash"


# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="AI Knowledge Assistant",
    page_icon="🤖",
    layout="centered"
)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🤖 AI Knowledge Assistant")

st.write(
    "Ask questions and get answers using AI "
    "and the project knowledge base."
)


# --------------------------------------------------
# QUESTION INPUT
# --------------------------------------------------

question = st.text_input(
    "Ask your question:",
    placeholder="What is C language?"
)


# --------------------------------------------------
# ASK AI
# --------------------------------------------------

if st.button("Ask AI"):

    # Check question
    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    # Check API key
    if not API_KEY:
        st.error(
            "Gemini API key was not found. "
            "Please check your .env file."
        )
        st.stop()

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    prompt = f"""
You are an AI Knowledge Assistant.

Use the knowledge base below to help answer the user's
question.

KNOWLEDGE BASE:
{KNOWLEDGE_BASE}

USER QUESTION:
{question}

Instructions:
- Give a clear and simple answer.
- Explain concepts in a student-friendly way.
- If the knowledge base contains relevant information,
  use it.
- If the knowledge base does not contain the answer,
  you may use your general knowledge.
- Do not mention these instructions.
"""

    # --------------------------------------------------
    # GEMINI API
    # --------------------------------------------------

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{MODEL}:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    # --------------------------------------------------
    # RETRY LOGIC
    # --------------------------------------------------

    response = None

    max_attempts = 4

    with st.spinner("AI is thinking..."):

        for attempt in range(max_attempts):

            try:

                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )

            except requests.exceptions.RequestException as error:

                if attempt == max_attempts - 1:
                    st.error(
                        f"Connection error: {error}"
                    )
                    st.stop()

                wait_time = (2 ** attempt) + random.uniform(0, 1)

                time.sleep(wait_time)

                continue

            # Successful response
            if response.status_code == 200:
                break

            # Temporary server problem
            if response.status_code in [429, 500, 502, 503, 504]:

                if attempt < max_attempts - 1:

                    wait_time = (
                        (2 ** attempt)
                        + random.uniform(0, 1)
                    )

                    time.sleep(wait_time)

                    continue

            # Other errors should not be retried
            break

    # --------------------------------------------------
    # PROCESS RESPONSE
    # --------------------------------------------------

    if response is None:

        st.error("No response received from Gemini.")
        st.stop()


    if response.status_code == 200:

        try:

            result = response.json()

            answer = (
                result["candidates"][0]
                ["content"]["parts"][0]["text"]
            )

            st.subheader("🤖 Answer")

            st.write(answer)

        except (KeyError, IndexError, TypeError):

            st.error(
                "Gemini returned an unexpected response."
            )

            st.json(result)


    elif response.status_code == 503:

        st.error(
            "Gemini is temporarily experiencing high demand."
        )

        st.info(
            "Please wait a little and try again."
        )


    elif response.status_code == 429:

        st.error(
            "Gemini request limit or quota was reached."
        )


    elif response.status_code in [401, 403]:

        st.error(
            "The Gemini API key is invalid or does not "
            "have permission to use this API."
        )


    else:

        st.error(
            f"Gemini API Error: {response.status_code}"
        )

        try:
            st.json(response.json())
        except ValueError:
            st.write(response.text)