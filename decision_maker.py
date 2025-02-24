import asyncio
from pydantic import BaseModel
from rich import print
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
import logfire
from duckduckgo_search import DDGS
from typing import Optional, List
import os

logfire.configure(send_to_logfire="if-token-present")

def search_internet(query: str) -> list[dict]: 
    """Searches the web for given query and returns top 5 results"""
    results = DDGS().text(query, max_results=5)
    return results

class InfoGatheringOutput(BaseModel):
    questions: List[str]
    answers: Optional[str] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None
    final_result: Optional[str] = None

class ProsOutput(BaseModel):
    pros: List[str]

class ConsOutput(BaseModel):
    cons: List[str]

def create_agents(api_key: str):
    """Create all agents with the provided API key"""
    # Set the API key
    os.environ["OPENAI_API_KEY"] = api_key
    
    model = OpenAIModel('gpt-4')

    # First agent: Gathers information and asks questions
    info_gathering = Agent(
        system_prompt='''You are an expert decision helper. First, ask relevant questions to understand the situation better.
        Keep questions focused and specific. Ask 3-5 questions that will help make a better decision.''',
        model=model,
        result_type=InfoGatheringOutput
    )

    # Second agent: Analyzes pros
    pros_agent = Agent(
        system_prompt="Based on the situation and answers provided, analyze and list the potential benefits and positive outcomes.",
        model=model,
        result_type=ProsOutput
    )

    # Third agent: Analyzes cons
    cons_agent = Agent(
        system_prompt="Based on the situation and answers provided, analyze and list the potential drawbacks and risks.",
        model=model,
        result_type=ConsOutput
    )

    # Fourth agent: Makes final recommendation
    final_agent = Agent(
        system_prompt="Based on the pros and cons analysis, provide a clear recommendation.",
        model=model,
        result_type=str
    )
    
    return info_gathering, pros_agent, cons_agent, final_agent

async def process_decision(query: str, api_key: str, answers: Optional[str] = None) -> InfoGatheringOutput:
    """Process the decision query and return either questions or final result"""
    
    # Create agents with the provided API key
    info_gathering, pros_agent, cons_agent, final_agent = create_agents(api_key)
    
    # If we don't have answers yet, get questions
    if not answers:
        result = await info_gathering.run(f"Help make a decision about: {query}")
        return InfoGatheringOutput(questions=result.data.questions)
    
    # If we have answers, process them and get recommendation
    pros_result = await pros_agent.run(f"Query: {query}\nAnswers: {answers}")
    cons_result = await cons_agent.run(f"Query: {query}\nAnswers: {answers}")
    
    recommendation = await final_agent.run(
        f"Query: {query}\nAnswers: {answers}\nPros: {pros_result.data.pros}\nCons: {cons_result.data.cons}"
    )
    
    return InfoGatheringOutput(
        questions=[],  # No more questions needed
        answers=answers,
        pros=pros_result.data.pros,
        cons=cons_result.data.cons,
        final_result=recommendation.data
    )

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    asyncio.run(process_decision(query="I want to create AI project which people will use?.", api_key=api_key))
