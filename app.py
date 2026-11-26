
import streamlit as st
import os
import re
import json
from io import BytesIO
from urllib.parse import quote_plus
from pypdf import PdfReader
from groq import Groq


# =====================================================
# 1. PAGE SETUP
# =====================================================

st.set_page_config(
    page_title="SSC PREP AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 SSC PREP AI")
st.caption("Your Personal Telangana SSC Class 10 Study Assistant")

MAX_TEXTBOOK_CHARS = 16000
MAX_PDF_PAGES = 8

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False


# =====================================================
# 2. API CONNECTION
# =====================================================

try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = os.getenv("GROQ_API_KEY")


# =====================================================
# 3. AI CONNECTION
# =====================================================

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

IMPORTANT RULES:

1. Follow the exact textbook terminology and topic order.
2. Never invent textbook facts.
3. If information is missing from the supplied textbook,
   clearly say so.
4. Keep notes medium-length, clear and directly copyable.
5. Do not add unnecessary explanations or padding.

SUBJECT REQUIREMENTS:

Biological Science:
- Necessary labelled diagrams.
- Biological processes.
- Important flowcharts and tables.

Physical Science:
- Formulas and equations.
- Chemical reactions.
- Necessary diagrams and tables.

Social Studies:
- Maps, timelines, tables and flowcharts wherever relevant.

Mathematics:
- Formulas, graphs and step-by-step worked examples.

English:
- Grammar tables, writing formats and examples.

Telugu:
- Grammar tables, meanings and literary details.

Never force diagrams or flowcharts into topics
where they are not necessary.

Use simple language when explaining difficult concepts.
"""
                },
                {
                    "role": "user",
                    "content": (
                        "RELEVANT TEXTBOOK CONTENT:\n"
                        + (
                            textbook[:MAX_TEXTBOOK_CHARS]
                            if textbook
                            else "No textbook content was selected."
                        )
                        + "\n\nREQUEST:\n"
                        + prompt
                    )
                }
            ],
            temperature=0.3,
            max_tokens=3000
        )

        return response.choices[0].message.content

    except Exception as e:
        st.error(f"AI error: {e}")
        return None


# =====================================================
# 4. TEXTBOOK UPLOAD
# =====================================================

st.sidebar.header("📚 Textbook Library")

uploaded_files = st.sidebar.file_uploader(
    "Upload your SSC textbooks (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

selected_file = None

if uploaded_files:

    st.sidebar.success(
        f"{len(uploaded_files)} textbook(s) uploaded."
    )

    selected_file_name = st.sidebar.selectbox(
        "Choose the textbook for this session",
        [file.name for file in uploaded_files]
    )

    selected_file = next(
        file for file in uploaded_files
        if file.name == selected_file_name
    )

else:
    st.sidebar.info(
        "Upload your SSC textbook PDFs to use textbook-based answers."
    )


# =====================================================
# 5. PDF TEXT EXTRACTION
# =====================================================

@st.cache_data(show_spinner=False)
def extract_pdf_pages(pdf_bytes):

    reader = PdfReader(BytesIO(pdf_bytes))

    pages = []

    for page_number, page in enumerate(reader.pages):

        page_text = page.extract_text()

        if page_text:
            pages.append({
                "page": page_number + 1,
                "text": page_text
            })
        else:
            pages.append({
                "page": page_number + 1,
                "text": ""
            })

    return pages


# =====================================================
# 6. CHAPTER-WISE TEXTBOOK SEARCH
# =====================================================

def get_relevant_text(query):

    if selected_file is None:
        return ""

    try:

        with st.spinner("Finding the relevant textbook chapter..."):

            pages = extract_pdf_pages(
                selected_file.getvalue()
            )

            if not pages:
                return ""

            # Remove unnecessary spaces from the search query.
            query = re.sub(r"\s+", " ", query).strip()

            chapter_name = chapter.strip()

            if not chapter_name:
                return ""

            def normalize(text):
                return re.sub(
                    r"\s+",
                    " ",
                    text.lower()
                ).strip()

            normalized_chapter = normalize(chapter_name)

            # First, search for the exact chapter heading.
            exact_matches = []

            for index, page in enumerate(pages):

                page_text = normalize(page["text"])

                position = page_text.find(normalized_chapter)

                if position >= 0:
                    exact_matches.append(
                        (position, index)
                    )

            if exact_matches:

                # Prefer a heading appearing near the beginning
                # of a page rather than in a contents list.
                exact_matches.sort(
                    key=lambda item: item[0]
                )

                start_index = exact_matches[0][1]

                st.sidebar.success(
                    "Chapter heading found in the PDF."
                )

            else:

                # If the exact heading is not found,
                # search for pages containing its keywords.
                keywords = re.findall(
                    r"\w+",
                    chapter_name.lower(),
                    flags=re.UNICODE
                )

                scored_pages = []

                for index, page in enumerate(pages):

                    page_text = page["text"].lower()

                    score = sum(
                        page_text.count(word)
                        for word in keywords
                        if len(word) > 1
                    )

                    if score > 0:
                        scored_pages.append(
                            (score, index)
                        )

                if scored_pages:

                    scored_pages.sort(
                        reverse=True
                    )

                    start_index = scored_pages[0][1]

                    st.sidebar.info(
                        "Using keyword matching to find the chapter."
                    )

                else:

                    st.warning(
                        "The chapter heading was not found. "
                        "Please check the chapter name and PDF."
                    )

                    return ""

            # Extract only a limited number of pages
            # beginning from the matching chapter page.
            selected_pages = pages[
                start_index:start_index + MAX_PDF_PAGES
            ]

            relevant_text = ""

            for page in selected_pages:

                page_content = (
                    f"\n--- PDF Page {page['page']} ---\n"
                    + page["text"]
                    + "\n"
                )

                if (
                    len(relevant_text)
                    + len(page_content)
                    > MAX_TEXTBOOK_CHARS
                ):
                    remaining = (
                        MAX_TEXTBOOK_CHARS
                        - len(relevant_text)
                    )

                    if remaining > 0:
                        relevant_text += page_content[:remaining]

                    break

                relevant_text += page_content

            if not relevant_text.strip():
                st.warning(
                    "No readable text was extracted from these PDF pages."
                )
                return ""

            return relevant_text

    except Exception as e:

        st.error(f"PDF reading error: {e}")
        return ""


# =====================================================
# 7. STUDY DETAILS
# =====================================================

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

chapter = st.sidebar.text_input(
    "Chapter Name"
)

topic = st.sidebar.text_input(
    "Topic"
)

subtopic = st.sidebar.text_input(
    "Subtopic (optional)"
)


# =====================================================
# 8. SEVEN STUDY TABS
# =====================================================

(
    notes_tab,
    concept_tab,
    video_tab,
    doubt_tab,
    maths_tab,
    flash_tab,
    quiz_tab
) = st.tabs([
    "📝 Generate Notes",
    "💡 Understand Concepts",
    "🎥 Video Lessons",
    "❓ Ask Doubts",
    "➗ Maths Solver",
    "🧠 Flashcards",
    "🧠 MCQ Practice"
])


# =====================================================
# 9. GENERATE NOTES
# =====================================================

with notes_tab:

    st.header("📝 Textbook-Based Notes")

    st.write(
        "Generate medium-length notes following "
        "your Telangana SSC textbook."
    )

    if st.button("Generate Notes", key="notes"):

        if not chapter:
            st.warning(
                "Please enter a chapter name in Study Details."
            )

        else:

            textbook = get_relevant_text(
                f"{chapter} {topic} {subtopic}"
            )

            prompt = f"""
Prepare Telangana SSC Class 10 {subject} notes.

Chapter: {chapter}
Topic: {topic}
Subtopic: {subtopic}

Follow the exact textbook order and terminology.

Include:
- Important definitions.
- Necessary labelled diagrams.
- Useful flowcharts.
- Important formulas and equations.
- Tables wherever relevant.
- Important textbook points.

Keep the notes medium-length and directly copyable.

Do not force diagrams or flowcharts where they
are not necessary.
"""

            answer = ask_ai(prompt, textbook)

            if answer:

                st.markdown(answer)

                st.download_button(
                    "⬇️ Download Notes",
                    answer,
                    file_name="SSC_Notes.txt",
                    mime="text/plain"
                )


# =====================================================
# 10. UNDERSTAND CONCEPTS
# =====================================================

with concept_tab:

    st.header("💡 Understand a Concept")

    concept = st.text_input(
        "Which concept would you like explained?",
        key="concept"
    )

    if st.button("Explain Concept"):

        if concept:

            textbook = get_relevant_text(
                f"{chapter} {concept}"
            )

            answer = ask_ai(
                f"""
Explain the concept '{concept}' from Telangana
SSC Class 10 {subject}.

Chapter: {chapter}

Start from the basics.

Use:
- Simple explanations.
- Step-by-step teaching.
- Easy examples.
- Important terminology.
- Small text-based diagrams where useful.

Make sure the student understands the concept.
""",
                textbook
            )

            if answer:
                st.markdown(answer)

        else:

            st.warning("Enter a concept first.")


# =====================================================
# 11. VIDEO LESSONS
# =====================================================

with video_tab:

    st.header("🎥 Video Lessons")

    st.write(
        "Find video lessons related to your SSC chapter."
    )

    video_topic = st.text_input(
        "Enter the chapter or concept",
        key="video"
    )

    if st.button("Find Videos"):

        if video_topic:

            search = quote_plus(
                "Telangana SSC Class 10 "
                + subject
                + " "
                + video_topic
            )

            youtube_url = (
                "https://www.youtube.com/results?search_query="
                + search
            )

            st.link_button(
                "▶️ Search YouTube Lessons",
                youtube_url
            )

        else:

            st.warning("Enter a topic first.")


# =====================================================
# 12. ASK DOUBTS
# =====================================================

with doubt_tab:

    st.header("❓ Ask Your Doubt")

    doubt = st.text_area(
        "Type your question here",
        key="doubt"
    )

    if st.button("Solve My Doubt"):

        if doubt:

            textbook = get_relevant_text(
                f"{chapter} {topic} {doubt}"
            )

            answer = ask_ai(
                f"""
Answer this Telangana SSC Class 10 student's doubt.

Subject: {subject}
Chapter: {chapter}

Question:
{doubt}

Explain clearly in simple language.
Use examples wherever necessary.
""",
                textbook
            )

            if answer:
                st.markdown(answer)

        else:

            st.warning("Type your doubt first.")


# =====================================================
# 13. MATHEMATICS SOLVER
# =====================================================

with maths_tab:

    st.header("➗ Step-by-Step Maths Solver")

    st.write(
        "Enter a Maths problem to receive a detailed solution."
    )

    problem = st.text_area(
        "Enter your Maths problem",
        key="math_problem"
    )

    if st.button("Solve Step by Step"):

        if problem:

            answer = ask_ai(
                f"""
Solve this Telangana SSC Class 10 Mathematics problem.

Show:
1. Given information.
2. Formula used.
3. Substitution.
4. Step-by-step calculations.
5. Final answer.

Check the calculations carefully.

Problem:
{problem}
"""
            )

            if answer:
                st.markdown(answer)

        else:

            st.warning("Enter a Maths problem first.")


# =====================================================
# 14. FLASHCARDS
# =====================================================

with flash_tab:

    st.header("🧠 Revision Flashcards")

    st.write(
        "Generate question-and-answer flashcards for revision."
    )

    flash_topic = st.text_input(
        "Enter a chapter or topic",
        key="flash"
    )

    if st.button("Create Flashcards"):

        if flash_topic:

            textbook = get_relevant_text(
                f"{chapter} {flash_topic}"
            )

            answer = ask_ai(
                f"""
Create 10 question-and-answer revision flashcards
for Telangana SSC Class 10 {subject}.

Chapter/topic: {flash_topic}

Format:

### Card 1
**Question:** ...

**Answer:** ...

Continue up to Card 10.

Keep questions short and answers accurate.
Follow the textbook terminology.
Do not invent facts.
""",
                textbook
            )

            if answer:
                st.markdown(answer)

        else:

            st.warning("Enter a chapter or topic first.")


# =====================================================
# 15. MCQ PRACTICE
# =====================================================

with quiz_tab:

    st.header("🧠 MCQ Practice")

    st.write(
        "Test your understanding with textbook-based multiple-choice questions."
    )

    quiz_count = st.selectbox(
        "Number of Questions",
        [5, 10, 15, 20],
        key="quiz_count"
    )

    quiz_difficulty = st.selectbox(
        "Difficulty Level",
        ["Easy", "Medium", "Hard"],
        key="quiz_difficulty"
    )

    if st.button("Generate MCQ Quiz"):

        if not chapter:

            st.warning(
                "Please enter a chapter name in Study Details."
            )

        else:

            textbook = get_relevant_text(
                f"{chapter} {topic}"
            )

            if textbook:

                quiz_prompt = f"""
Create exactly {quiz_count} multiple-choice questions
for Telangana SSC Class 10 {subject}.

Chapter: {chapter}
Topic: {topic}
Difficulty: {quiz_difficulty}

Use the supplied textbook content.

IMPORTANT:
- Each question must have exactly four options.
- Options must be labelled A, B, C and D.
- There must be only one correct answer.
- Do not include hints.
- Do not show answers separately before submission.
- Include a short explanation for every correct answer.

Return ONLY valid JSON in this exact structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "options": {{
                "A": "Option one",
                "B": "Option two",
                "C": "Option three",
                "D": "Option four"
            }},
            "correct_answer": "A",
            "explanation": "Explanation of the answer"
        }}
    ]
}}

Create exactly {quiz_count} questions.
Do not include Markdown code fences.
"""

                with st.spinner("Preparing your MCQ quiz..."):

                    result = ask_ai(
                        quiz_prompt,
                        textbook
                    )

                if result:

                    try:

                        # Extract the JSON object if the AI
                        # includes any extra surrounding text.
                        start = result.find("{")
                        end = result.rfind("}") + 1

                        if start == -1 or end == 0:
                            raise ValueError(
                                "No valid JSON object found."
                            )

                        quiz_json = json.loads(
                            result[start:end]
                        )

                        questions = quiz_json.get(
                            "questions",
                            []
                        )

                        if not questions:
                            raise ValueError(
                                "No questions were generated."
                            )

                        st.session_state.quiz_data = questions

                        st.session_state.quiz_submitted = False

                    except Exception as e:

                        st.error(
                            f"Could not prepare the quiz correctly: {e}"
                        )

                        st.caption(
                            "Try generating the quiz again."
                        )

            else:

                st.warning(
                    "Relevant textbook content was not found. "
                    "Check the chapter name and uploaded PDF."
                )


    # -------------------------------------------------
    # DISPLAY QUIZ
    # -------------------------------------------------

    if st.session_state.quiz_data:

        questions = st.session_state.quiz_data

        st.divider()

        st.subheader("Your Quiz")

        with st.form("mcq_quiz_form"):

            for index, question in enumerate(questions):

                st.markdown(
                    f"**Q{index + 1}. {question.get('question', '')}**"
                )

                options = question.get("options", {})

                if isinstance(options, list):

                    options = {
                        "ABCD"[i]: value
                        for i, value in enumerate(options[:4])
                    }

                option_labels = ["A", "B", "C", "D"]

                choice = st.radio(
                    "Choose your answer:",
                    options=option_labels,
                    format_func=lambda x, opts=options: (
                        f"{x}. {opts.get(x, '')}"
                    ),
                    key=f"quiz_answer_{index}",
                    index=None
                )

            submitted = st.form_submit_button(
                "Submit Quiz"
            )

            if submitted:

                st.session_state.quiz_submitted = True


        # -------------------------------------------------
        # RESULTS AFTER SUBMISSION ONLY
        # -------------------------------------------------

        if st.session_state.quiz_submitted:

            score = 0

            for index, question in enumerate(questions):

                selected = st.session_state.get(
                    f"quiz_answer_{index}"
                )

                correct = str(
                    question.get("correct_answer", "")
                ).strip().upper()

                correct = correct[:1]

                if selected == correct:
                    score += 1

            total = len(questions)

            percentage = round(
                (score / total) * 100,
                2
            ) if total else 0

            st.divider()

            st.subheader("📊 Your Results")

            st.metric(
                "Your Score",
                f"{score} / {total}"
            )

            st.metric(
                "Percentage",
                f"{percentage}%"
            )

            st.progress(
                score / total if total else 0
            )

            if score == total:

                st.success(
                    "Excellent! You answered every question correctly."
                )

            elif score >= total / 2:

                st.info(
                    "Good effort! Review the explanations to improve."
                )

            else:

                st.warning(
                    "Keep practising. Review the explanations and try again."
                )

            st.divider()

            st.subheader("Answer Review")

            for index, question in enumerate(questions):

                selected = st.session_state.get(
                    f"quiz_answer_{index}"
                )

                correct = str(
                    question.get("correct_answer", "")
                ).strip().upper()[:1]

                options = question.get("options", {})

                if isinstance(options, list):

                    options = {
                        "ABCD"[i]: value
                        for i, value in enumerate(options[:4])
                    }

                st.markdown(
                    f"**Q{index + 1}. {question.get('question', '')}**"
                )

                if selected:

                    st.write(
                        f"Your answer: {selected}. "
                        f"{options.get(selected, '')}"
                    )

                else:

                    st.write("Your answer: Not attempted")

                st.write(
                    f"Correct answer: {correct}. "
                    f"{options.get(correct, '')}"
                )

                if selected == correct:

                    st.success("Correct!")

                else:

                    st.error("Incorrect.")

                st.write(
                    "**Explanation:** "
                    + question.get(
                        "explanation",
                        "No explanation was provided."
                    )
                )

                st.divider()

            if st.button("Try Another Quiz"):

                st.session_state.quiz_data = None
                st.session_state.quiz_submitted = False

                st.rerun()


# =====================================================
# 16. FOOTER
# =====================================================

st.divider()

st.caption(
    "📚 SSC PREP AI | Telangana SSC Class 10"
)

st.caption(
    "Study • Understand • Practise • Revise"
)
