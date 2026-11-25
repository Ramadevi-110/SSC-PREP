
import os
import urllib.parse
from pathlib import Path

import streamlit as st
from groq import Groq
from pypdf import PdfReader

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="SSC PREP AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 SSC PREP AI")
st.caption("Your Personal Telangana SSC Class 10 Study Assistant")

# ---------------- SETTINGS ----------------

TEXTBOOK_DIR = Path("textbooks")
TEXTBOOK_DIR.mkdir(exist_ok=True)

SUBJECTS = [
    "Mathematics",
    "Physical Science",
    "Biological Science",
    "Social Studies",
    "English",
    "Telugu",
    "Hindi"
]

MODEL = "llama-3.3-70b-versatile"

# ---------------- AI CONNECTION ----------------

api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))

if not api_key:
    st.error("Please add GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)


def ask_ai(prompt, textbook_text=""):
    context = textbook_text[:18000]

    system_prompt = """
You are SSC PREP AI, a careful tutor for Telangana SSC Class 10.

Follow these rules:
1. Use Telangana SCERT Class 10 terminology.
2. Never invent textbook facts or headings.
3. Preserve the textbook's order and terminology.
4. Separate textbook-supported information from extra explanations.
5. Explain difficult concepts in simple English.
6. Use readable headings, bullet points and tables.
7. Include simple labelled diagram instructions when useful.
8. If the supplied textbook does not contain the requested
   information, clearly say so.
9. Do not claim that supplementary information is from
   the textbook.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"""
TEXTBOOK MATERIAL:
{context if context else "No textbook PDF supplied."}

STUDENT REQUEST:
{prompt}
"""
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3
    )

    return response.choices[0].message.content


# ---------------- PDF READER ----------------

def extract_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


def get_stored_text():
    documents = []

    for pdf in TEXTBOOK_DIR.glob("*.pdf"):
        try:
            reader = PdfReader(str(pdf))
            for page in reader.pages:
                documents.append(page.extract_text() or "")
        except Exception:
            continue

    return "\n".join(documents)


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("⚙️ My Study Profile")

    subject = st.selectbox("Select Subject", SUBJECTS)

    learning_style = st.selectbox(
        "Preferred Learning Style",
        [
            "Simple explanations with examples",
            "Step-by-step explanations",
            "Visual descriptions and diagrams",
            "Exam-focused bullet points"
        ]
    )

    level = st.selectbox(
        "My Current Level",
        [
            "Teach me from zero",
            "I know the basics",
            "I am ready for revision"
        ]
    )

    st.divider()

    st.subheader("📚 Textbook Library")

    uploaded_pdfs = st.file_uploader(
        "Upload SSC textbook PDFs",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_pdfs:
        for pdf in uploaded_pdfs:
            safe_name = Path(pdf.name).name
            save_path = TEXTBOOK_DIR / safe_name

            if not save_path.exists():
                with open(save_path, "wb") as file:
                    file.write(pdf.getvalue())

        st.success("PDFs saved for this app session.")

    stored_text = get_stored_text()

    if stored_text:
        st.caption("Stored textbook material is available.")

    st.info(
        "For permanent textbook storage on GitHub, "
        "add official PDF files to the textbooks folder."
    )


# ---------------- TEXTBOOK CONTEXT ----------------

uploaded_text = ""

if uploaded_pdfs:
    selected_pdf = st.selectbox(
        "Choose a PDF for this session",
        ["No additional PDF"] + [p.name for p in uploaded_pdfs]
    )

    if selected_pdf != "No additional PDF":
        selected_file = next(
            p for p in uploaded_pdfs if p.name == selected_pdf
        )

        try:
            uploaded_text = extract_pdf(selected_file)
        except Exception:
            st.warning("Could not read this PDF.")

textbook_context = (
    (stored_text + "\n" + uploaded_text).strip()
)


# ---------------- MAIN LEARNING TABS ----------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Generate Notes",
    "🧠 Understand Concepts",
    "🎥 Video Lessons",
    "✍️ Ask Doubts",
    "🧮 Maths Solver",
    "🗂️ Flashcards"
])


# ---------------- TAB 1: NOTES ----------------

with tab1:
    st.header("📝 SSC Notes Generator")

    chapter = st.text_input(
        "Chapter name",
        key="notes_chapter"
    )

    topic = st.text_input(
        "Topic or subtopic (optional)",
        key="notes_topic"
    )

    if st.button("Generate Textbook Notes", key="notes_btn"):
        if not chapter:
            st.warning("Enter a chapter name.")
        else:
            prompt = f"""
Generate medium-length, directly copyable Telangana SSC
Class 10 {subject} notes.

Chapter: {chapter}
Topic: {topic if topic else "Entire chapter"}

Follow the exact textbook headings and subheading order
where the supplied material supports them.

Include:
- Important textbook facts
- Definitions
- Necessary labelled diagrams
- Useful flowcharts
- Important formulas and tables
- Short revision cards

Do not add unrelated information.

Learning preference: {learning_style}

Clearly separate the textbook notes from any supplementary
explanation. Do not invent textbook section numbers.
"""
            with st.spinner("Preparing your notes..."):
                try:
                    result = ask_ai(prompt, textbook_context)
                    st.markdown(result)
                    st.download_button(
                        "Download Notes",
                        result,
                        file_name="SSC_Notes.txt"
                    )
                except Exception as e:
                    st.error(f"AI error: {e}")


# ---------------- TAB 2: CONCEPT EXPLAINER ----------------

with tab2:
    st.header("🧠 Understand Any Concept")

    concept = st.text_input(
        "Which concept is difficult?",
        key="concept_input"
    )

    if st.button("Explain This Concept"):
        if concept:
            prompt = f"""
Teach the Class 10 Telangana SSC concept: {concept}
Subject: {subject}

Student level: {level}
Preferred style: {learning_style}

First explain the textbook-supported concept.
Then provide a separate section titled
'Understand Better - Additional Explanation'.

Use simple examples, analogies, step-by-step reasoning
and visual descriptions wherever useful.
"""
            with st.spinner("Explaining the concept..."):
                try:
                    st.markdown(ask_ai(prompt, textbook_context))
                except Exception as e:
                    st.error(f"AI error: {e}")


# ---------------- TAB 3: VIDEO FINDER ----------------

with tab3:
    st.header("🎥 Video Learning Centre")

    video_topic = st.text_input(
        "Enter chapter or concept",
        key="video_topic"
    )

    language = st.selectbox(
        "Video language",
        ["English", "Telugu", "Telugu + English"]
    )

    if st.button("Find Video Lessons"):
        if video_topic:
            search = urllib.parse.quote(
                f"Telangana SSC Class 10 {video_topic} "
                f"{language} animated explanation"
            )

            url = (
                "https://www.youtube.com/results?search_query="
                + search
            )

            st.link_button(
                "▶️ Search Educational Videos",
                url
            )

            st.caption(
                "Check that the selected video matches "
                "your SSC syllabus."
            )


# ---------------- TAB 4: DOUBT SOLVER ----------------

with tab4:
    st.header("✍️ Ask Your Doubts")

    question = st.text_area(
        "Paste your question here",
        height=150
    )

    doubt_mode = st.radio(
        "How should I help?",
        [
            "Explain from scratch",
            "Step-by-step solution",
            "SSC exam-style answer"
        ]
    )

    if st.button("Solve My Doubt"):
        if question.strip():
            prompt = f"""
Subject: {subject}
Question: {question}

Task: {doubt_mode}
Learning level: {level}
Learning style: {learning_style}

Explain accurately and clearly.
Use textbook context where available.
"""
            with st.spinner("Solving your doubt..."):
                try:
                    st.markdown(ask_ai(prompt, textbook_context))
                except Exception as e:
                    st.error(f"AI error: {e}")


# ---------------- TAB 5: MATHS SOLVER ----------------

with tab5:
    st.header("🧮 Mathematics Step-by-Step Solver")

    maths_question = st.text_area(
        "Enter your Maths problem",
        height=120
    )

    if st.button("Solve Maths Problem"):
        if maths_question.strip():
            prompt = f"""
Solve this Class 10 Telangana SSC Maths problem:

{maths_question}

Requirements:
1. Write the given information.
2. Identify the formula or method.
3. Solve step by step.
4. Explain why each step is performed.
5. Show the final answer clearly.
6. Mention common calculation mistakes.
"""
            with st.spinner("Working through the problem..."):
                try:
                    st.markdown(ask_ai(prompt, textbook_context))
                except Exception as e:
                    st.error(f"AI error: {e}")


# ---------------- TAB 6: FLASHCARDS ----------------

with tab6:
    st.header("🗂️ Quick Revision Cards")

    flash_chapter = st.text_input(
        "Enter chapter name",
        key="flash_chapter"
    )

    card_count = st.slider(
        "Number of revision questions",
        5, 20, 10
    )

    if st.button("Create Revision Cards"):
        if flash_chapter:
            prompt = f"""
Create {card_count} Class 10 Telangana SSC revision
flashcards for {subject}, chapter: {flash_chapter}.

Use textbook-supported information wherever available.

Format:
Question 1:
Answer:

Keep answers clear, concise and useful for revision.
Add supplementary questions only in a separately
marked section.
"""
            with st.spinner("Creating revision cards..."):
                try:
                    st.markdown(ask_ai(prompt, textbook_context))
                except Exception as e:
                    st.error(f"AI error: {e}")


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "SSC PREP AI | Telangana SSC Class 10 | "
    "Learn • Understand • Revise • Improve"
)
