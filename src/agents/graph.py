import operator
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from src.outputs import TeachingCandidate
from src.prompts.extract_prompts import PARSE_PROMPT

class ResumeScreenerState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add] = Field(
        description="The intermediate steps taken by the agent for processing the resume"
    )    
    id: Optional[str] = Field(description="The id of the candidate")
    candidate: list[TeachingCandidate] = Field(default_factory=list)
    iteration: int = Field(default=0)

    model_config = ConfigDict(use_enum_values=True)


llm = ChatOpenAI(model="gpt-4o-mini")
def read_resume(state:ResumeScreenerState):
    model =  PARSE_PROMPT | llm.with_structured_output(TeachingCandidate)

    try: 
        candidate = model.invoke({"messages": state.messages, "schema": TeachingCandidate.model_json_schema()})
        return {
            "candidate":[candidate.model_dump(mode="json")], 
            "messages":[AIMessage(candidate.model_dump_json())],
            "iteration": state.iteration + 1    
        }
    except Exception as e:
        return {
            "messages":[HumanMessage(
                f"Seems like there was an error validating the data you returned. Check this:\n {str(e)}"
            )],
            "iteration": state.iteration + 1
        }    

def router(state):
    if len(state.candidate)>0:
        return "end"
    else:
        if state.iteration > 3:
            return "end"
        else:
            return "diagnose-error"

workflow = StateGraph(ResumeScreenerState)

workflow.add_node("Reading Resume", read_resume)
# workflow.add_node(diagnose, "Diagnosin2g Error")
workflow.add_edge("__start__","Reading Resume")
workflow.add_conditional_edges("Reading Resume", router, {"end":"__end__", "diagnose-error":"Reading Resume"})

agent = workflow.compile()
agent.name = "sync-resume"