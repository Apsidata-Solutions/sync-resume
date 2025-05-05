import operator
from typing import Annotated, List, Literal
from pydantic import BaseModel, Field, ConfigDict

from langchain_core.messages import AnyMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from prompts.classify_prompts import CLASSIFY_PROMPT

class EmailType(BaseModel):
    """
    EmailType to categorise emails
    """
    type: Literal["candidate", "non candidate"] = Field(description="This field classifies the email as being a candidate and their resume or not")

llm = ChatOpenAI(model="gpt-4o-mini")

model = CLASSIFY_PROMPT | llm.with_structured_output(EmailType)

class EmailClassifierState(BaseModel):
    id: str 
    messages: Annotated[List[AnyMessage], operator.add] = Field(
        description="The intermediate steps taken by the agent for processing the resume"
    )
    type: EmailType 
    

def classify(state:EmailClassifierState):
    #Define the model here, i.e. a single llm call. With prompts/ outputs, examples. 
    model = CLASSIFY_PROMPT | llm.with_structured_output(EmailType)

    try: 
        output = model.invoke({"messages":state.messages})
        # Invoke the model here return the response as a message, otherwise
        return {
            "type":output.model_dump(mode="json"), 
            "messages":[AIMessage(output.model_dump_json())]
        }

    except Exception as e:
        return {
            "messages":[AIMessage(
                f"Error: Seems like there was an error validating the data you returned. Check this:\n {str(e)}"
            )]
        }    

def router(state):
    if isinstance(state.messages[-1], AIMessage):
        return "error"
    else:
        return "end"

workflow = StateGraph(EmailClassifierState)

workflow.add_node("Classifying Email", classify)
workflow.add_edge("__start__","Classifying Email")
workflow.add_conditional_edges("Classifying Email", router, {"end":"__end__", "error":"Classifying Email"})

agent = workflow.compile()
agent.name = "sync-email"