import streamlit as st
import requests
import json

BACKEND_URL = "https://webscarping-app.onrender.com"  # Flask

st.set_page_config(page_title="AI Notes Maker", layout="wide")
st.title("📚 AI Notes Maker")

st.write("Paste your topic URL and questions. Maximum 3 questions at a time.")

url = st.text_input("Webpage URL (GfG, TutorialsPoint, etc.)")

questions_input = st.text_area(
    "Questions (one per line)",
    height=200,
    placeholder="What is deadlock?\nExplain Banker's algorithm.\nDefine process and thread.",
)

if "page_text" not in st.session_state:
    st.session_state.page_text = ""
if "qa" not in st.session_state:
    st.session_state.qa = []
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = []

if "selected_questions" not in st.session_state:
    st.session_state.selected_questions = []


col1, col2 = st.columns(2)

with col1:
    if st.button("1️⃣ Scrape Page Text"):
        if not url:
            st.error("Please enter a URL.")
        else:
            with st.spinner("Scraping page..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/scrape", json={"url": url})
                    data = resp.json()
                    if resp.status_code == 200:
                        st.session_state.page_text = data["pageText"]
                        st.success("Page text extracted!")
                        st.text_area(
                            "Extracted text (preview)",
                            st.session_state.page_text[:3000],
                            height=300,
                        )
                    else:
                        st.error(f"Error: {data.get('error')}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

with col2:
    if st.button("2️⃣ Generate Answers with Gemini"):
        if not st.session_state.page_text:
            st.error("Scrape the page first (step 1).")
        else:
            questions = [
                q.strip() for q in questions_input.splitlines() if q.strip()
            ]
            if not questions:
                st.error("Please enter at least one question.")
            else:
                with st.spinner("Calling Gemini to answer questions..."):
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/answer-questions",
                            json={
                                "pageText": st.session_state.page_text,
                                "questions": questions,
                            },
                        )
                        data = resp.json()
                        if resp.status_code == 200:
                            st.session_state.qa = data["qa"]
                            st.success("Answers generated!")
                        else:
                            st.error(f"Error: {data.get('error')}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")

st.markdown("---")
st.subheader("🧠 Generate Questions from This Page. ")

col1, col2, col3 = st.columns(3)

with col1:
    num_questions = st.number_input(
        "Number of questions",
        min_value=1,
        max_value=20,
        value=5
    )

with col2:
    marks = st.selectbox(
        "Marks level",
        [5, 10, 15]
    )

with col3:
    difficulty = st.selectbox(
        "Difficulty",
        ["easy", "exam", "hard"]
    )

if st.button("📝 Generate Questions"):
    if not st.session_state.page_text:
        st.error("Scrape the page first.")
    else:
        with st.spinner("Generating questions......."):
            resp = requests.post(
                f"{BACKEND_URL}/generate-questions",
                json={
                    "pageText": st.session_state.page_text,
                    "num_questions": num_questions,
                    "marks": marks,
                    "difficulty": difficulty
                }
            )

            if resp.status_code == 200:
                st.session_state.generated_questions = resp.json()["questions"]
                st.success("Questions generated! Select the ones you want to use below.")
            else:
                st.error("Failed to generate questions")
                st.code(resp.text)
if st.session_state.generated_questions:
    st.markdown("### 📋 Generated Questions")

    selected = []

    for i, q in enumerate(st.session_state.generated_questions):
        checked = st.text(q)
        if checked:
            selected.append(q)

    st.session_state.selected_questions = selected



st.markdown("---")
st.subheader("📄 Generated Notes")
if st.session_state.qa:
    for i, item in enumerate(st.session_state.qa, start=1):
        st.markdown(f"### Q{i}. {str(item['question'])}")
        if not item.get("found", True):
            st.markdown("**⚠ Not clearly available in the given page.**")
        st.write(item["answer"])
        with st.expander("Source snippet from page"):
            st.write(item.get("source_snippet", ""))

    # Export DOCX
    if st.button("⬇️ Download as DOCX"):
        with st.spinner("Generating DOCX..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/export-docx",
                    json={
                        "qa": st.session_state.qa,
                        "title": "Study Notes",
                    },
                )
                if resp.status_code == 200:
                    st.download_button(
                        "Download File",
                        data=resp.content,
                        file_name="study_notes.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                else:
                    data = resp.json()
                    st.error(f"Error: {data.get('error')}")
            except Exception as e:
                st.error(f"Request failed: {e}")
else:
    st.info("Run steps 1 and 2 to see generated notes here.")
