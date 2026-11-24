import urllib.parse
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Personalized SSC AI Tutor", page_icon="🎯", layout="centered")

# --- PERSONALIZED STUDENT PROFILE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Personalize Your Tutor")
    learning_style = st.selectbox("How do you learn best?", [
        "Real-life analogies & simple stories",
        "Step-by-step formulas & logic",
        "Visual descriptions & diagrams",
        "Exam-focused bullet points only"
    ])
    current_level = st.radio("Topic Familiarity:", [
        "Brand New (Teach from zero)",
        "Know basics (Need practice)",
        "Exam Ready (Test me)"
    ])

st.title("🎯 Personalized SSC AI Companion")
st.caption(f"Mode: **{current_level}** • Style: **{learning_style}**")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("⚠️ Add GROQ_API_KEY in Streamlit App Settings -> Secrets.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📖 Personalized Lesson", "✍️ Paste Any Doubt", "🎥 Video Finder"])

# --- TAB 1: ADAPTIVE SSC TUTOR ---
with tab1:
    subject = st.selectbox("Select SSC Subject", [
        "Physical Science (Physics & Chemistry)",
        "Mathematics",
        "Biological Science",
        "Social Studies",
        "English",
        "Second Language (Telugu / Hindi)"
    ])
    topic = st.text_input("Chapter or Topic:", placeholder="e.g., Quadratic Equations, Refraction, Acids & Bases")

    if st.button("Generate Personalized Session", use_container_width=True) and topic:
        prompt = f"""
        You are a personalized AI tutor for a Class 10 Telangana SSC student (TS SCERT syllabus).
        Subject: {subject} | Topic: {topic}
        Student's Current Level: {current_level}
        Preferred Learning Style: {learning_style}

        Tailor your response strictly to their level and learning style:
        - If 'Brand New': Start from absolute zero using {learning_style}, give 1 fully solved basic example, and list the 2 easiest high-scoring SSC board questions.
        - If 'Know basics': Give a quick recap, 2 medium-level SCERT textbook problems with step-by-step solutions, and common exam mistakes to avoid.
        - If 'Exam Ready': Give a rapid 5-question Part-B objective test + one 4-mark and one 8-mark SSC board question with an answer key at the bottom.
        """
        with st.spinner("Customizing your lesson..."):
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown(res.choices[0].message.content)

# --- TAB 2: TEXT / QUESTION DOUBT SOLVER ---
with tab2:
    st.subheader("Type or Paste Any Textbook Question")
    question_text = st.text_area("Paste the question or paragraph you don't understand:", height=120)
    help_type = st.radio("What do you need?", ["Explain the concept simply", "Write full SSC Board answer"], horizontal=True)

    if st.button("Solve Doubt", use_container_width=True) and question_text:
        doubt_prompt = f"""
        Class 10 TS SCERT Doubt: {question_text}
        Task: {help_type}.
        Use the student's preferred style: {learning_style}. Keep it strictly aligned with Class 10 SSC standards.
        """
        with st.spinner("Solving..."):
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": doubt_prompt}]
            )
            st.markdown(res.choices[0].message.content)

# --- TAB 3: VIDEO LESSON FINDER ---
with tab3:
    st.subheader("Watch Concept Videos")
    vid_topic = st.text_input("Topic:", value=topic, placeholder="Enter topic name")
    lang = st.radio("Language:", ["English", "Telugu + English"], horizontal=True)

    if vid_topic:
        query = urllib.parse.quote(f"TS Class 10 SSC {vid_topic} {lang} SCERT")
        yt_link = f"https://youtube.com{query}"
        st.link_button(f"▶️ Watch '{vid_topic}' on YouTube", yt_link, use_container_width=True)
