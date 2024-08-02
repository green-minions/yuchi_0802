from typing import List

import nest_asyncio
import streamlit as st
from phi.assistant import Assistant
from phi.document import Document
from phi.document.reader.pdf import PDFReader
from phi.document.reader.website import WebsiteReader
from phi.tools.streamlit.components import get_username_sidebar
from phi.utils.log import logger
from assistant import get_personalized_assistant
nest_asyncio.apply()

st.set_page_config(
    page_title="國泰智多星",
    page_icon=":orange_heart:",
)
st.title("國泰智多星")
st.markdown("### 🌳🌳🌳國泰智多星是由 [國泰世華銀行](https://cathaybk.com.tw/cathaybk/) 建構的客服~")

with st.expander(":rainbow[:point_down: 使用指南]"):
    st.markdown("阿星是個隨時隨地都在你身邊的小幫手.")
    st.markdown("雖然他有不會回答的問題，請溫柔對待他QAQ")
    st.markdown("想不到什麼問題的話就隨便聊聊吧")


def main() -> None:


    # Get username
    user_id = get_username_sidebar()
    if user_id:
        st.sidebar.info(f":technologist: User: {user_id}")
    else:
        st.write(":technologist: Please enter a username")
        return


    # Get LLM Model
    llm_id = "gemini-1.5-flash"
    if "llm_id" not in st.session_state:
        st.session_state["llm_id"] = llm_id
    # Restart the assistant if llm_id changes
    elif st.session_state["llm_id"] != llm_id:
        st.session_state["llm_id"] = llm_id
        restart_assistant()

    # Sidebar checkboxes for selecting tools
    st.sidebar.markdown("### 請選擇相關工具")

    # Enable Calculator
    if "calculator_enabled" not in st.session_state:
        st.session_state["calculator_enabled"] = True
    # Get calculator_enabled from session state if set
    calculator_enabled = st.session_state["calculator_enabled"]
    # Checkbox for enabling calculator
    calculator = st.sidebar.checkbox("Calculator", value=calculator_enabled, help="Enable calculator.")
    if calculator_enabled != calculator:
        st.session_state["calculator_enabled"] = calculator
        calculator_enabled = calculator
        restart_assistant()

    # Enable Web Search via DuckDuckGo
    if "ddg_search_enabled" not in st.session_state:
        st.session_state["ddg_search_enabled"] = True
    # Get ddg_search_enabled from session state if set
    ddg_search_enabled = st.session_state["ddg_search_enabled"]
    # Checkbox for enabling web search
    ddg_search = st.sidebar.checkbox("Web Search", value=ddg_search_enabled, help="Enable web search using DuckDuckGo.")
    if ddg_search_enabled != ddg_search:
        st.session_state["ddg_search_enabled"] = ddg_search
        ddg_search_enabled = ddg_search
        restart_assistant()

    # Enable finance tools
    if "finance_tools_enabled" not in st.session_state:
        st.session_state["finance_tools_enabled"] = True
    # Get finance_tools_enabled from session state if set
    finance_tools_enabled = st.session_state["finance_tools_enabled"]
    # Checkbox for enabling shell tools
    finance_tools = st.sidebar.checkbox("Yahoo Finance", value=finance_tools_enabled, help="Enable finance tools.")
    if finance_tools_enabled != finance_tools:
        st.session_state["finance_tools_enabled"] = finance_tools
        finance_tools_enabled = finance_tools
        restart_assistant()


    st.sidebar.markdown("### 請選擇你小幫手")

    # Enable Python Assistant
    if "python_assistant_enabled" not in st.session_state:
        st.session_state["python_assistant_enabled"] = True
    # Get python_assistant_enabled from session state if set
    python_assistant_enabled = st.session_state["python_assistant_enabled"]
    # Checkbox for enabling web search
    python_assistant = st.sidebar.checkbox(
        "Python Assistant",
        value=python_assistant_enabled,
        help="Enable the Python Assistant for writing and running python code.",
    )
    if python_assistant_enabled != python_assistant:
        st.session_state["python_assistant_enabled"] = python_assistant
        python_assistant_enabled = python_assistant
        restart_assistant()

    # Enable Research Assistant
    if "research_assistant_enabled" not in st.session_state:
        st.session_state["research_assistant_enabled"] = True
    # Get research_assistant_enabled from session state if set
    research_assistant_enabled = st.session_state["research_assistant_enabled"]
    # Checkbox for enabling web search
    research_assistant = st.sidebar.checkbox(
        "Research Assistant",
        value=research_assistant_enabled,
        help="Enable the research assistant (uses Exa).",
    )
    if research_assistant_enabled != research_assistant:
        st.session_state["research_assistant_enabled"] = research_assistant
        research_assistant_enabled = research_assistant
        restart_assistant()

    # Enable Investment Assistant
    if "investment_assistant_enabled" not in st.session_state:
        st.session_state["investment_assistant_enabled"] = True
    # Get investment_assistant_enabled from session state if set
    investment_assistant_enabled = st.session_state["investment_assistant_enabled"]
    # Checkbox for enabling web search
    investment_assistant = st.sidebar.checkbox(
        "Investment Assistant",
        value=investment_assistant_enabled,
        help="Enable the investment assistant. NOTE: This is not financial advice.",
    )
    if investment_assistant_enabled != investment_assistant:
        st.session_state["investment_assistant_enabled"] = investment_assistant
        investment_assistant_enabled = investment_assistant
        restart_assistant()

    if "youtube_assistant_enabled" not in st.session_state:
        st.session_state["youtube_assistant_enabled"] = True
    # Get youtube_assistant_enabled from session state if set
    youtube_assistant_enabled = st.session_state["youtube_assistant_enabled"]
    # Checkbox for enabling web search
    youtube_assistant = st.sidebar.checkbox(
        "youtube Assistant",
        value=youtube_assistant_enabled,
        help="Enable the youtube assistant.",
    )
    if youtube_assistant_enabled != youtube_assistant:
        st.session_state["youtube_assistant_enabled"] = youtube_assistant
        youtube_assistant_enabled = youtube_assistant
        restart_assistant()


    # Get the assistant
    personalized_assistant: Assistant
    if "personalized_assistant" not in st.session_state or st.session_state["personalized_assistant"] is None:
        logger.info(f"---*--- Creating {llm_id} personalized_assistant ---*---")
        personalized_assistant = get_personalized_assistant(
            llm_id=llm_id,
            user_id=user_id,
            ddg_search=ddg_search_enabled,
            finance_tools=finance_tools_enabled,
            python_assistant=python_assistant_enabled,
            research_assistant=research_assistant_enabled,
            investment_assistant=investment_assistant_enabled,
            calculator=calculator_enabled,
            youtube_assistant=youtube_assistant_enabled,
        )
        st.session_state["personalized_assistant"] = personalized_assistant
    else:
        personalized_assistant = st.session_state["personalized_assistant"]

    try:
        st.session_state["assistant_run_id"] = personalized_assistant.create_run()
    except Exception:
        st.warning("Could not create Assistant, is the database running?")
        return

    # Load existing messages
    assistant_chat_history = personalized_assistant.memory.get_chat_history()
    if len(assistant_chat_history) > 0:
        logger.debug("Loading chat history")
        st.session_state["messages"] = assistant_chat_history
    else:
        logger.debug("No chat history found")
        st.session_state["messages"] = [{"role": "assistant", "content": "你想詢問阿星小幫手甚麼呢?"}]

    # Prompt for user input
    if prompt := st.chat_input():
        st.session_state["messages"].append({"role": "user", "content": prompt})

    # Display existing chat messages
    for message in st.session_state["messages"]:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is from a user, generate a new response
    last_message = st.session_state["messages"][-1]
    if last_message.get("role") == "user":
        question = last_message["content"]
        with st.chat_message("assistant"):
            response = ""
            resp_container = st.empty()
            for delta in personalized_assistant.run(question):
                response += delta  # type: ignore
                resp_container.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})

    # Show team member memory
    if personalized_assistant.team and len(personalized_assistant.team) > 0:
        for team_member in personalized_assistant.team:
            if len(team_member.memory.chat_history) > 0:
                with st.status(f"{team_member.name} Memory", expanded=False, state="complete"):
                    with st.container():
                        _team_member_memory_container = st.empty()
                        _team_member_memory_container.json(team_member.memory.get_llm_messages())

    if personalized_assistant.storage:
        assistant_run_ids: List[str] = personalized_assistant.storage.get_all_run_ids()
        new_assistant_run_id = st.sidebar.selectbox("Run ID", options=assistant_run_ids)
        if st.session_state["assistant_run_id"] != new_assistant_run_id:
            logger.info(f"---*--- Loading {llm_id} run: {new_assistant_run_id} ---*---")
            st.session_state["personalized_assistant"] = get_personalized_assistant(
                llm_id=llm_id,
                user_id=user_id,
                run_id=new_assistant_run_id,
                calculator=calculator_enabled,
                ddg_search=ddg_search_enabled,
                finance_tools=finance_tools_enabled,
                python_assistant=python_assistant_enabled,
                research_assistant=research_assistant_enabled,
                investment_assistant=investment_assistant_enabled,
                youtube_assistant=youtube_assistant_enabled,
            )
            st.rerun()
    # Show Assistant memory
    with st.status("Assistant Memory", expanded=False, state="complete"):
        with st.container():
            memory_container = st.empty()
            if personalized_assistant.memory.memories and len(personalized_assistant.memory.memories) > 0:
                memory_container.markdown("\n".join([f"- {m.memory}" for m in personalized_assistant.memory.memories]))
            else:
                memory_container.warning("阿星目前還不記得您的任何資訊喔! 請確定大小寫。")


    if st.sidebar.button("New Run"):
        restart_assistant()


def restart_assistant():
    logger.debug("---*--- Restarting Assistant ---*---")
    st.session_state["personalized_assistant"] = None
    st.session_state["assistant_run_id"] = None
    st.rerun()


main()
