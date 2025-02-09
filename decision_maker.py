# %% [markdown]
# ## What do we have to make 
# 
# user will give you a situation. 
# first agent will ask the additional questions if necessary 
# 
# second and third agent will provide pros and cons of the situation. If it requires any tool calls have a web search and simple calculator tool powered by python make both tools availalbe to this agent. 
# 
# forth agent: 
# will provide the final conclusion if user should take that decision or not. 

# %% [markdown]
# ## Imports

# %%
from dotenv import load_dotenv
load_dotenv()

from openai import BaseModel
from rich import print
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
import asyncio
import logfire
from dataclasses import dataclass


logfire.configure()
# import nest_asyncio
# nest_asyncio.apply()
from duckduckgo_search import DDGS
from rich.prompt import Prompt




# %% [markdown]
# ### Tools for internet search 

# %%
from pydantic_ai.tools import Tool

def search_internet(query: str) -> list[dict]: 
    """Searches the web for given query and returns top 5 results

    Args:
        query (str): Query to search

    Returns:
        list: List of top 5 results
    """
    results = DDGS().text(query, max_results=5)
    return results

async def get_more_info_from_user(questions: list[str]) -> str:
    """
    In case of more infromation needed, this function asks user relavent info and gets you that info. 

    Args:
        questions (list[str]): list of questions to ask 

    Returns:
        str: answers for above questions from user
    """
    answers = Prompt.ask(f"""
    -----
    Please answer the following questions
    -----
    {questions}
    -----
    """)
    return answers

search_tool  = Tool(search_internet)
get_more_info_from_user = Tool(get_more_info_from_user)


# %%
class InfoGatheringOutput(BaseModel): 
    """The model returned by info gathering agent.

    Args:
        BaseModel (_type_): _description_

    Returns:
        _type_: _description_
    """
    query: str 
    questions: list[str]
    answers_from_user: str 
    pros: list[str]
    cons: list[str]

class ProsOutput(BaseModel): 
    """
    The model returned by pros agent.
    Args:
        BaseModel (_type_): _description_

    Returns:
        _type_: _description_
    """
    pros: list[str]

class ConsOutput(BaseModel): 
    """
    The model returned by cons agent.

    Args:
        BaseModel (_type_): _description_

    Returns:
        _type_: _description_
    """
    cons: list[str]

@dataclass
class Deps:
    pros_identifier_agent: Agent
    cons_identifier_agent: Agent
    conclusion_agent: Agent


model = OpenAIModel('gpt-4o-mini')
entry_and_info_gathering = Agent(  
    system_prompt='You are a expert in making decisions you make right decisions always. You will be given a situation and you have to ask questions to user to so that you can make a right decision which user asks. You have access to the tool call for the getting more info from user please use that, after gathering you can use pros and cons gathering agent to get pros and cons. ',  
    model = model, 
    tools = [search_tool, get_more_info_from_user],
    result_type=InfoGatheringOutput
)


pros_identifier_agent  = Agent(
    system_prompt = "you have given a situation and some questions answered by user. You have to respond all the pros of that situation. ",
    result_type=ProsOutput, 
    model = model, 
    tools = [search_tool]
)

cons_identifier_agent = Agent(
    system_prompt = "You are the best critic which evaluates situation and gives critical responses which are importatnt to make decision. you have given a situation and some questions answered by user. You have to respond all the cons of that situation. ",
    result_type=ConsOutput, 
    model = model,
    tools = [search_tool]
)

conclusion_agent = Agent(
    system_prompt = "you have given a situation and some questions answered by user. Also the pros and cons about the situation you have provide conclusion for making the better decision. The highest pros and a decision which is ethical is usually the best decision, think and answer based on the knowledge and scenarios you've observed from past.",
    result_type=str,
    model = model,
    tools = [search_tool]
)

@entry_and_info_gathering.tool
async def transfer_to_pros_agent(ctx: RunContext, query: str, questions: list[str], answer: str ) -> str:
    print(f"Getting pros for: {query}")
    result = await ctx.deps.pros_identifier_agent.run(f"Please evaluate the topic and provide pros for this {query} previous agent asked this question to the user {questions} and user provided following answer {answer}.")
    return result

@entry_and_info_gathering.tool
async def transfer_to_cons_agent(ctx: RunContext, query: str, questions: list[str], answer: str ) -> str:
    print(f"Getting cons for: {query}")
    result = await ctx.deps.cons_identifier_agent.run(f"Please evaluate the topic and provide cons for this {query} previous agent asked this question to the user {questions} and user provided following answer {answer}.")
    return result

deps = Deps(pros_identifier_agent = pros_identifier_agent, cons_identifier_agent = cons_identifier_agent, conclusion_agent = conclusion_agent)

# %%
async def main(query: str):
    res =await entry_and_info_gathering.run(query, deps = deps)
    if res != None: 
        print(res.data)
        questions = res.data.questions
        answers_from_user = res.data.answers_from_user
        query = res.data.query
        pros = res.data.pros
        cons = res.data.cons
        result = await deps.conclusion_agent.run(f"Evalute the query {query} and questions {questions} and answers from user were {answers_from_user} and the pros are {pros} and cons are {cons}")
        print(result.data)


    return result.data

if __name__ == "__main__":
    asyncio.run(main(query = "I want to create AI project which people will use?."))

# %%



