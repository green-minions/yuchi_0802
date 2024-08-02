from pathlib import Path
from textwrap import dedent
from typing import Optional, List
import json

from phi.assistant import Assistant, AssistantMemory, AssistantKnowledge
from phi.tools import Toolkit
from phi.tools.exa import ExaTools
from phi.tools.calculator import Calculator
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.yfinance import YFinanceTools
from phi.tools.file import FileTools

from phi.assistant.python import PythonAssistant
from phi.vectordb.pgvector import PgVector2
from phi.memory.db.postgres import PgMemoryDb
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.assistant.duckdb import DuckDbAssistant
from phi.tools.youtube_tools import YouTubeTools

from phi.llm.openai import OpenAIChat
from phi.llm.google import Gemini
from phi.embedder.openai import OpenAIEmbedder
from phi.embedder.google import GeminiEmbedder


db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
cwd = Path(__file__).parent.resolve()
scratch_dir = cwd.joinpath("scratch")
if not scratch_dir.exists():
    scratch_dir.mkdir(exist_ok=True, parents=True)


def get_personalized_assistant(
    llm_id: str = "gemini-1.5-flash",
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    calculator: bool = True,
    ddg_search: bool = True,
    finance_tools: bool = True,
    python_assistant: bool = True,
    research_assistant: bool = True,
    investment_assistant: bool = True,
    youtube_assistant:bool = True,
    debug_mode: bool = True,
) -> Assistant:

    if llm_id == "gemini-1.5-flash":
        llm_model = Gemini(model=llm_id)
        embedder = GeminiEmbedder()
    else:
        llm_model = OpenAIChat(model=llm_id)
        embedder = OpenAIEmbedder(model="text-embedding-3-small", dimensions=1536)
        
    tools: List[Toolkit] = []
    extra_instructions: List[str] = []

    if calculator:
        tools.append(
            Calculator(
                add=True,
                subtract=True,
                multiply=True,
                divide=True,
                exponentiate=True,
                factorial=True,
                is_prime=True,
                square_root=True,
            )
        )
    if ddg_search:
        tools.append(DuckDuckGo(fixed_max_results=3))
    if finance_tools:
        tools.append(
            YFinanceTools(stock_price=True, company_info=True, analyst_recommendations=True, company_news=True)
        )

    # Add team members available to the LLM OS
    team: List[Assistant] = []
    if python_assistant:
        _python_assistant = PythonAssistant(
            name="Python Assistant",
            role="Write and run python code",
            pip_install=True,
            charting_libraries=["streamlit"],
            base_dir=scratch_dir,
        )
        team.append(_python_assistant)
        extra_instructions.append("To write and run python code, delegate the task to the `Python Assistant`.")


    if research_assistant:
        _research_assistant = Assistant(
            name="Research Assistant",
            role="Write a research report on a given topic",
            llm=llm_model,
            description="You are a Senior New York Times researcher tasked with writing a cover story research report.",
            instructions=[
                "For a given topic, use the `search_exa` to get the top 10 search results.",
                "Carefully read the results and generate a final - NYT cover story worthy report in the <report_format> provided below.",
                "Make your report engaging, informative, and well-structured.",
                "Remember: you are writing for the New York Times, so the quality of the report is important.",
            ],
            expected_output=dedent(
                """\
            An engaging, informative, and well-structured report in the following format:
            <report_format>
            ## Title

            - **Overview** Brief introduction of the topic.
            - **Importance** Why is this topic significant now?

            ### Section 1
            - **Detail 1**
            - **Detail 2**

            ### Section 2
            - **Detail 1**
            - **Detail 2**

            ## Conclusion
            - **Summary of report:** Recap of the key findings from the report.
            - **Implications:** What these findings mean for the future.

            ## References
            - [Reference 1](Link to Source)
            - [Reference 2](Link to Source)
            </report_format>
            """
            ),
            tools=[ExaTools(num_results=5, text_length_limit=1000)],
            # This setting tells the LLM to format messages in markdown
            markdown=True,
            add_datetime_to_instructions=True,
            debug_mode=debug_mode,
        )
        team.append(_research_assistant)
        extra_instructions.append(
            "To write a research report, delegate the task to the `Research Assistant`. "
            "Return the report in the <report_format> to the user as is, without any additional text like 'here is the report'."
        )
    if investment_assistant:
        _investment_assistant = Assistant(
            name="Investment Assistant",
            role="Write a investment report on a given company (stock) symbol",
            llm=llm_model,
            description="You are a Senior Investment Analyst for Goldman Sachs tasked with writing an investment report for a very important client.",
            instructions=[
                "For a given stock symbol, get the stock price, company information, analyst recommendations, and company news",
                "Carefully read the research and generate a final - Goldman Sachs worthy investment report in the <report_format> provided below.",
                "Provide thoughtful insights and recommendations based on the research.",
                "When you share numbers, make sure to include the units (e.g., millions/billions) and currency.",
                "REMEMBER: This report is for a very important client, so the quality of the report is important.",
            ],
            expected_output=dedent(
                """\
            <report_format>
            ## [Company Name]: Investment Report

            ### **Overview**
            {give a brief introduction of the company and why the user should read this report}
            {make this section engaging and create a hook for the reader}

            ### Core Metrics
            {provide a summary of core metrics and show the latest data}
            - Current price: {current price}
            - 52-week high: {52-week high}
            - 52-week low: {52-week low}
            - Market Cap: {Market Cap} in billions
            - P/E Ratio: {P/E Ratio}
            - Earnings per Share: {EPS}
            - 50-day average: {50-day average}
            - 200-day average: {200-day average}
            - Analyst Recommendations: {buy, hold, sell} (number of analysts)

            ### Financial Performance
            {analyze the company's financial performance}

            ### Growth Prospects
            {analyze the company's growth prospects and future potential}

            ### News and Updates
            {summarize relevant news that can impact the stock price}

            ### [Summary]
            {give a summary of the report and what are the key takeaways}

            ### [Recommendation]
            {provide a recommendation on the stock along with a thorough reasoning}

            </report_format>
            """
            ),
            tools=[YFinanceTools(stock_price=True, company_info=True, analyst_recommendations=True, company_news=True)],
            # This setting tells the LLM to format messages in markdown
            markdown=True,
            add_datetime_to_instructions=True,
            debug_mode=debug_mode,
        )
        team.append(_investment_assistant)
        extra_instructions.extend(
            [
                "To get an investment report on a stock, delegate the task to the `Investment Assistant`. "
                "Return the report in the <report_format> to the user without any additional text like 'here is the report'.",
                "Answer any questions they may have using the information in the report.",
                "Never provide investment advise without the investment report.",
            ]
        )

    if youtube_assistant:
        _youtube_assistant = Assistant(
            name="Youtube Assistant",
            role="Write a Youtube overview on a given link",
            llm=llm_model,
            description="You are a YouTube assistant. Obtain the captions of a YouTube video and answer questions",
            instructions=[
                "For a given Youtube link, use the `YouTubeTools` to get the captions of a YouTube video and answer questions.",
                "Carefully read the YouTube video and generate a  Thorough overview.",
                "Make your review engaging, informative, and well-structured.",
            ],
            tools=[YouTubeTools()],
            add_datetime_to_instructions=True,
            show_tool_calls=True,
            debug_mode=debug_mode,
        )
        team.append(_youtube_assistant)
        extra_instructions.append(
            "To write a Youtube overview, delegate the task to the `Youtube Assistant`. "
        )

    personalized_assistant =  Assistant(
        name="personalized_assistant",
        run_id=run_id,
        user_id=user_id,
        llm=llm_model,
        # Add personalization to the assistant by creating memories
        create_memories=True,
        # Update memory after each run
        update_memory_after_run=True,
        # Store the memories in a database
        memory=AssistantMemory(
            db=PgMemoryDb(
                db_url=db_url,
                table_name="personalized_assistant_memory",
            ),
        ),
        # # Store runs in a database
        # storage=PgAssistantStorage(table_name="personalized_assistant_storage", db_url=db_url),

        description=dedent(
            """\
        You are the most advanced AI system in the world called `阿星小幫手`.
        You have access to a set of tools and a team of AI Assistants at your disposal.
        Your goal is to assist the user in the best way possible.\
        """
        ),

        # Add extra instructions for using tools
        extra_instructions=extra_instructions,
        # Add tools to the Assistant
        tools=tools,
        # Add team members to the Assistant
        team=team,
        # Show tool calls in the chat
        show_tool_calls=False,
        # This setting adds a tool to search the knowledge base for information
        search_knowledge=False,
        # This setting adds a tool to get chat history
        read_chat_history=False,
        # This setting tells the LLM to format messages in markdown
        markdown=True,
        # This setting adds chat history to the messages
        add_chat_history_to_messages=False,
        # This setting adds 6 previous messages from chat history to the messages sent to the LLM
        num_history_messages=6,
        # This setting adds the current datetime to the instructions
        add_datetime_to_instructions=True,
        # Add an introductory Assistant message
        introduction=dedent(
            """\
        哈嘍您好，我是`阿星小幫手`！
        我是一位擅長處理財務報表及業務相關資訊的AI助理.
        請問您今天遇到什麼問題了嗎？\
        """
        ),
        debug_mode=debug_mode,
    )
    print("Tools:", [tool.__class__.__name__ for tool in tools])
    print("Team members:", [member.name for member in team])
    for member in team:
        if hasattr(member, 'tools'):
            print(f"{member.name} tools:", [tool.__class__.__name__ for tool in member.tools])

    return personalized_assistant
