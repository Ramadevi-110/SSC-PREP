
import streamlit as st
import os
from io import BytesIO
from pypdf import PdfReader
from groq import Groq

# ---------------- PAGE SETUP ----------------
st.set_page_config(
    page_title="SSC PREP AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 SSC PREP AI")
st.caption("Your Personal Telangana SSC Class 10 Study Assistant")

# ---------------- API CONNECTION ----------------
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = os.getenv("GROQ_API_KEY")

def ask_ai(prompt, textbook=""):
    if not api_key:
        st.error("Please add GROQ_API_KEY in Streamlit Secrets.")
        return None

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are SSC PREP AI, a study assistant for Telangana
                    State Class 10 students.

                    Follow the Telangana SSC/SCERT textbook wherever
                    textbook content is provided.

                    Use the exact textbook terminology and topic order.
                    Make notes medium-length, clear and copyable.
                    Include visual elements according to the subject:

- Biological Science: labelled diagrams, biological
  processes and flowcharts.
- Physical Science: equations, formulas, chemical
  reactions and relevant diagrams.
- Social Studies: maps, timelines, tables and
  flowcharts wherever relevant.
- Mathematics: formulas, graphs and worked examples.
- English: grammar tables, writing formats and examples.
- Telugu: grammar tables, meanings and literary details.

Never force diagrams or flowcharts into a topic
where they are not necessary.

Follow the exact textbook order and terminology.
Do not invent textbook content.

                    Do not invent textbook facts. If information is
                    missing from the provided textbook, say so.
                    """
                },
                {
                    "role": "user",
                    "content": (
                        "TEXTBOOK CONTENT:\n"
                        + (textbook[:14000] if textbook else
                           "No textbook content was selected.")
                        + "\n\nREQUEST:\n" + prompt
                    )
                }
            ],
            temperature=0.3,
            max_tokens=2500
        )
        return response.choices[0].message.content

    except Exception as e:
        st.error(f"AI error: {e}")
        return None


# ---------------- TEXTBOOK UPLOAD ----------------
st.sidebar.header("📚 Textbook Library")

uploaded_files = st.sidebar.file_uploader(
    "Upload your SSC textbooks (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.sidebar.success(f"{len(uploaded_files)} textbook(s) uploaded.")

    selected_file_name = st.sidebar.selectbox(
        "Choose the textbook for this session",
        [file.name for file in uploaded_files]
    )

    selected_file = next(
        file for file in uploaded_files
        if file.name == selected_file_name
    )
else:
    selected_file = None
    st.sidebar.info("Upload your textbook PDFs to use textbook-based answers.")


# ---------------- PDF READING ----------------
@st.cache_data(show_spinner=False)
def extract_pdf_text(pdf_bytes):
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""

        # Read only the first 40 pages to avoid long loading times.
        for page in reader.pages[:40]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

            if len(text) >= 20000:
                break

        return text[:20000]

    except Exception as e:
        return f"PDF reading error: {e}"


def get_textbook():
    if selected_file is None:
        return ""

    with st.spinner("Reading the selected textbook..."):
        return extract_pdf_text(selected_file.getvalue())


# ---------------- STUDY DETAILS ----------------
st.sidebar.header("🎯 Study Details")

subject = st.sidebar.selectbox(
    "Select Subject",
    [
        "Mathematics",
        "Physical Science",
        "Biological Science",
        "Social Studies",
        "English",
        "Telugu",
        "Other"
    ]
)

chapter = st.sidebar.text_input("Chapter Name")
topic = st.sidebar.text_input("Topic")
subtopic = st.sidebar.text_input("Subtopic (optional)")

# ---------------- TABS ----------------
notes_tab, concept_tab, video_tab, doubt_tab, maths_tab, flash_tab = st.tabs([
    "📝 Generate Notes",
    "💡 Understand Concepts",
    "🎥 Video Lessons",
    "❓ Ask Doubts",
    "➗ Maths Solver",
    "🧠 Flashcards"
])


# ---------------- GENERATE NOTES ----------------
with notes_tab:
    st.header("📝 Textbook-Based Notes")

    if st.button("Generate Notes", key="notes"):
        if not chapter:
            st.warning("Please enter a chapter name in Study Details.")
        else:
            textbook = get_textbook()
            prompt = f"""
            Prepare Telangana SSC Class 10 {subject} notes.

            Chapter: {chapter}
            Topic: {topic}
            Subtopic: {subtopic}

            Follow the textbook order. Include necessary diagrams,
            flowcharts, tables, formulas and important points.
            Keep the notes medium-length and directly copyable.
            """
            answer = ask_ai(prompt, textbook)
            if answer:
                st.markdown(answer)
                st.download_button(
                    "⬇️ Download Notes",
                    answer,
                    file_name="SSC_Notes.txt"
                )


# ---------------- UNDERSTAND CONCEPTS ----------------
with concept_tab:
    st.header("💡 Understand a Concept")

    concept = st.text_input(
        "Which concept would you like explained?",
        key="concept"
    )

    if st.button("Explain Concept"):
        if concept:
            textbook = get_textbook()
            answer = ask_ai(
                f"Explain {concept} from {subject}, chapter {chapter}. "
                "Start from the basics with simple examples and "
                "step-by-step explanations.",
                textbook
            )
            if answer:
                st.markdown(answer)
        else:
            st.warning("Enter a concept first.")


# ---------------- VIDEO LESSONS ----------------
with video_tab:
    st.header("🎥 Find Video Lessons")

    video_topic = st.text_input(
        "Enter the chapter or concept",
        key="video"
    )

    if st.button("Find Videos"):
        if video_topic:
            import urllib.parse
            search = urllib.parse.quote(
                "Telangana SSC Class 10 " + subject + " " + video_topic
            )
            st.link_button(
                "▶️ Search YouTube Lessons",
                "https://www.youtube.com/results?search_query=" + search
            )
        else:
            st.warning("Enter a topic first.")


# ---------------- ASK DOUBTS ----------------
with doubt_tab:
    st.header("❓ Ask Your Doubt")

    doubt = st.text_area(
        "Type your question here",
        key="doubt"
    )

    if st.button("Solve My Doubt"):
        if doubt:
            textbook = get_textbook()
            answer = ask_ai(
                f"Answer this student's doubt about {subject}: {doubt}. "
                "Explain clearly with examples.",
                textbook
            )
            if answer:
                st.markdown(answer)
        else:
            st.warning("Type your doubt first.")


# ---------------- MATHS SOLVER ----------------
with maths_tab:
    st.header("➗ Step-by-Step Maths Solver")

    problem = st.text_area(
        "Enter your Maths problem",
        key="math_problem"
    )

    if st.button("Solve Step by Step"):
        if problem:
            answer = ask_ai(
                "Solve this Class 10 Maths problem step by step. "
                "Show the formula, substitution, calculations and final answer. "
                "Check the calculations carefully.\n\n" + problem
            )
            if answer:
                st.markdown(answer)
        else:
            st.warning("Enter a Maths problem first.")


# ---------------- FLASHCARDS ----------------
with flash_tab:
    st.header("🧠 Revision Flashcards")

    flash_topic = st.text_input(
        "Enter a chapter or topic",
        key="flash"
    )

    if st.button("Create Flashcards"):
        if flash_topic:
            textbook = get_textbook()
            answer = ask_ai(
                f"Create 10 question-and-answer revision flashcards "
                f"for Telangana SSC Class 10 {subject}, "
                f"chapter/topic: {flash_topic}. "
                "Keep questions short and answers accurate.",
                textbook
            )
            if answer:
                st.markdown(answer)
        else:
            st.warning("Enter a chapter or topic first.")


st.divider()
st.caption("SSC PREP AI | Telangana SSC Class 10")
