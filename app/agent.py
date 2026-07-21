## the brain with safety net

from langgraph.graph import StateGraph, START, END, add_messages
from typing_extensions import TypedDict, Annotated
from typing import Literal, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_groq import ChatGroq
from langsmith import traceable

import operator
from dotenv import load_dotenv

from app.config import get_settings

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    error: Optional[str]
    retry_count: int
    model_used: str

settings = get_settings()
class ProductionAgent:
    """
    """
    def __init__(self):
        self.primary_llm =ChatGroq(
            model=settings.primary_model,
            temperature=0.0,
            api_key= settings.groq_api_key,
            max_retries=0
        )
        self.fallback_llm = ChatGroq(
            model=settings.primary_model,
            temperature=0.0,
            api_key= settings.groq_api_key,
            max_retries=0
        )
        self.max_retries = settings.max_retries
        self.graph = self._build_graph()
    
    def _build_graph(self):

        def process_message(state:AgentState) -> dict:
            """try to process the message with the primary model"""
            try:
                reponse = self.primary_llm.invoke(state['messages'])
                return {
                    "messages":[reponse],
                    "error": None,
                    "model": "primary"
                }

            except Exception as e:
                return {
                    "error": str(e),
                    "retry_count": state["retry_count"],
                    "model_used": ""
                }


        def try_fallback(state:AgentState) -> dict:
            """try to process the message with the fall_back"""
            try:
                reponse = self.primary_llm.invoke(state['messages'])
                return {
                    "messages":[reponse],
                    "error": None,
                    "model": "fallback"
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "model_used": ""
                }
        
        def error_handler(state:AgentState) -> dict:
            return {
                "messages": [
                    AIMessage(content=("I'm sorry, I'm having trouble processing your message"))
                    ],
                "model_used":"error_handler"

            }


        ## build the graph
        def route_process(state:AgentState):
            if state.get("error") is None:
                return "done"
            elif state["retry_count"] < self.max_retries:
                return "fallback"
            else:
                return "error"
        
            
        def route_fallback(state:AgentState):
            if state.get("error") is None:
                return "done"
            else:
                return "error"
            
        # build the graph
        graph = StateGraph(AgentState)
        ## or just graph = 
        graph.add_node("process", process_message)
        graph.add_node("fallback", try_fallback)
        graph.add_node("error", error_handler)

        graph.add_edge(START,"process")
        graph.add_conditional_edges(
            "process",
            route_process,
            {"done":END,
            "fallback":"fallback",
            "error":"error"}
        )
        graph.add_conditional_edges(
            "fallback",
            route_fallback,
            {"done":END,
            "error":"error"}
        )
        graph.add_edge("error",END)
        return graph.compile()

    @traceable(name="production_agent_invoke")
    def invoke(self, message:str)->dict:

        result = self.graph.invoke({
            "messages":[HumanMessage(content=message)],
            "model_used":"",
            "retry_count":0,
            "error":None
        })

        return {
            "response":result["messages"][-1].content,
            "model_used":result.get("model_used","Uknown"),
            "error":result.get("error")
        }
    