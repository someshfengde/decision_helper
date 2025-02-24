import streamlit as st
import asyncio
from decision_maker import process_decision, InfoGatheringOutput

# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = 'initial'
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'result' not in st.session_state:
    st.session_state.result = None

st.set_page_config(
    page_title="Decision Helper Agent",
    page_icon="🤔",
    layout="wide"
)

st.title("🤔 Decision Helper Agent")
st.markdown("""
This AI-powered tool helps you make better decisions by:
1. Asking relevant follow-up questions
2. Analyzing pros and cons
3. Providing a well-reasoned conclusion
""")

def reset_state():
    """Reset all state variables"""
    st.session_state.state = 'initial'
    st.session_state.query = ""
    st.session_state.questions = []
    st.session_state.result = None

# Initial query input
if st.session_state.state == 'initial':
    query = st.text_area(
        "What decision are you trying to make?",
        placeholder="Example: Should I switch my career to AI?",
        height=100
    )
    
    if st.button("Help me decide", type="primary"):
        if query:
            st.session_state.query = query
            with st.spinner("Analyzing your query..."):
                result = asyncio.run(process_decision(query))
                if result.questions:
                    st.session_state.questions = result.questions
                    st.session_state.state = 'questions'
                st.rerun()
        else:
            st.warning("Please enter your decision query first.")

# Handle follow-up questions
elif st.session_state.state == 'questions':
    st.info(f"Analyzing your query: {st.session_state.query}")
    
    if st.session_state.questions:
        st.write("### Please answer these follow-up questions:")
        
        # Create a form for questions
        with st.form(key='questions_form'):
            answers = []
            for i, q in enumerate(st.session_state.questions, 1):
                answer = st.text_area(f"{i}. {q}", key=f"q_{i}")
                answers.append(f"Q: {q}\nA: {answer}")
            
            submit = st.form_submit_button("Submit Answers", type="primary")
            
            if submit:
                if all(a.split("A: ")[1].strip() for a in answers):  # Check if all questions are answered
                    with st.spinner("Processing your answers..."):
                        result = asyncio.run(process_decision(
                            st.session_state.query,
                            "\n".join(answers)
                        ))
                        st.session_state.result = result
                        st.session_state.state = 'complete'
                        st.rerun()
                else:
                    st.warning("Please answer all questions.")
        
        if st.button("Start Over", type="secondary"):
            reset_state()
            st.rerun()

# Show final result
elif st.session_state.state == 'complete' and st.session_state.result:
    result = st.session_state.result
    
    st.success("Analysis complete!")
    
    # Show pros if available
    if result.pros:
        st.write("### 👍 Pros:")
        for pro in result.pros:
            st.write(f"- {pro}")
    
    # Show cons if available
    if result.cons:
        st.write("### 👎 Cons:")
        for con in result.cons:
            st.write(f"- {con}")
    
    # Show final recommendation
    if result.final_result:
        st.markdown("### 🎯 Final Recommendation")
        st.markdown(result.final_result)
    
    if st.button("Make Another Decision", type="primary"):
        reset_state()
        st.rerun()

st.divider()
st.markdown("""
### How it works
1. **Information Gathering**: The AI asks clarifying questions to better understand your situation
2. **Pros Analysis**: Identifies potential benefits and positive outcomes
3. **Cons Analysis**: Evaluates potential drawbacks and risks
4. **Final Decision**: Provides a well-reasoned recommendation based on the analysis
""")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using PydanticAI")