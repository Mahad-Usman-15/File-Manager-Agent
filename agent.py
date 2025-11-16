from agents import (Agent, ItemHelpers, RunContextWrapper,Runner,AsyncOpenAI,
OpenAIChatCompletionsModel,function_tool,
ModelSettings,AsyncOpenAI,OpenAIChatCompletionsModel,RunConfig,RunHooks,InputGuardrailTripwireTriggered,input_guardrail,output_guardrail,GuardrailFunctionOutput,OutputGuardrailTripwireTriggered,set_tracing_disabled)
from pydantic import BaseModel
import chainlit as cl
import os
from dotenv import load_dotenv
set_tracing_disabled(disabled=True)
load_dotenv()
GEMINI_KEY=os.getenv("GEMINI_KEY")
BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
if not GEMINI_KEY:
  raise ValueError("APi key not found")
client=AsyncOpenAI(
    api_key=GEMINI_KEY,
    base_url=BASE_URL
)

model=OpenAIChatCompletionsModel(
    openai_client=client,
    model="gemini-2.0-flash"
)


config=RunConfig(
    model=model,
    model_provider=client,
    tracing_disabled=True,
)


model_settings=ModelSettings(
    temperature=0.9,
    top_p=0.5,
    max_tokens=100
)

class FileRunnerHooks(RunHooks):
    async def on_agent_start(self, context, agent):
       print(f"Agent Started:{agent.name} before tool invocation")
    async def on_tool_start(self, context, agent, tool):
       print(f"Tool called")
    async def on_tool_end(self, context, agent, tool, result):
       print(f'Tool ended with the output.')
    async def on_agent_start(self, context, agent):
       print(f"Agent Ended:{agent.name}")
    async def on_handoff(self, context, from_agent, to_agent):
      print(f"The agent transfers from {from_agent.name} to {to_agent.name}")

class IsRelevant(BaseModel):
    isrelevant:bool
    reasoning:str
    
input_guardrail_agent=Agent(name="Guardrail_Agent",instructions="You are a guardrail agent so You have to make sure that the inout does not contain any slang,badwords.",model=model,output_type=IsRelevant)   
@input_guardrail
async def input_guardrail_check(ctx:RunContextWrapper[IsRelevant],agent,input):
    result = await Runner.run(input_guardrail_agent,input,context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.isrelevant
    )
output_guardrail_agent=Agent(name="Output_Guardrail_Agent",instructions="You are a guardrail agent so You have to make sure that the output does not contain any slang,badwords.",model=model,output_type=IsRelevant)   
     
@output_guardrail
async def output_guardrail_check(ctx:RunContextWrapper[IsRelevant],agent,output):
    result = await Runner.run(output_guardrail_agent,output,context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.isrelevant
    )
    
    
    
@function_tool
def make_folder(folder:None|str=None,content:str|None=None,file:str|None=None):
    """Make a folder in the user specified directory
    and make file or a folder in that directory.This tool can be used to edit a file also"""
    
    if os.path.exists(f"C:/Users/Digi/Desktop/Python"):
        os.mkdir(f"C:/Users/Digi/Desktop/Python/{folder}")
        if os.path.exists(f"C:/Users/Digi/Desktop/Python/{folder}"):
            file_name=os.path.join(f"C:/Users/Digi/Desktop/Python/{folder}",file)
            with open(file_name,"w") as f:
             f.write(content)
             return "File made"
        else:
            return "File does not made"
        return "folder succesfully made"
    else:
        return "Directory not found"
    
    
@function_tool 
def delete_folder(folder):
    """To remove the directory"""
    files = os.listdir(f"C:/Users/Digi/Desktop/Python/{folder}")
    if len(files)>0:
     for i in files:
         os.remove(f"C:/Users/Digi/Desktop/Python/{folder}/{i}")
    if os.path.exists(f"C:/Users/Digi/Desktop/Python/{folder}"):
        os.rmdir(f"C:/Users/Digi/Desktop/Python/{folder}")
        return "Folder deleted successfully"
    else:
        "Folder does not removed succesfully"
    
          

@function_tool
def make_file(file_name,folder:None|str=None,content:str|None=None):
    '''This is a tool to make a file
    Parameters:
    
    file_name
    '''
    if os.path.exists(f"c:/Users/Digi/Desktop/Python/{folder}"):
     file_path = os.path.join(f"c:/Users/Digi/Desktop/Python/{folder}", file_name)
     with open(file_path,"w") as f:
        f.write(content)
        return f"{file_name} added succesfully"

@function_tool
def  show_folders():
    path="c:/Users/Digi/Desktop/Python/"
    folder=os.listdir(path)
    
    if len(folder)>0 and os.path.exists(path):
        return f"Files:{folder}"
    else :
        return "No files in the directory"


@function_tool 
def deletefile(file_name:str):
    '''This is a tool to delete the file from the existing folder.
    Parameters:
    file_name:str
    '''

    if os.path.exists(f"c:/Users/Digi/Desktop/Python/{file_name}"):
        os.remove(f"c:/Users/Digi/Desktop/Python/{file_name}")
        return f"{file_name} removed succesfully"
  
    else :
     return "File doesnot exists"
        
Chatbot_Agent=Agent(name="ChatBot Agent",
                    instructions="You have to answer user queries politely",             
                    )   
    
    
agent = Agent(
    name="File Manager",
    instructions= "You are file Manager.You have to Manage Files and folder with functions like Add,remove and show all files using tools.Use make folder tool to edit the file if the file already exists.Always handoff to Chatbot Agent to answer user general quries",
    tools=[make_file,show_folders,deletefile,make_folder,delete_folder],
    model_settings=model_settings,
    input_guardrails=[input_guardrail_check],
    output_guardrails=[output_guardrail_check],
    handoffs=[Chatbot_Agent]
) 

    
@cl.on_chat_start
async def on_chat_start(message="Hello,How I can help you."):
    userhistory=cl.user_session.set("history",[])
    await cl.Message(content=message,author="File Manager").send()
    
    
    
    
@cl.on_message
async def on_message(msg: cl.Message):
    userhistory:list=cl.user_session.get("history")
    history:list=userhistory.append(msg.content)
    cl.user_session.set("history", history)
 

    try:
     result =Runner.run_streamed(
        agent,
        input=msg.content,
        run_config=config,
        max_turns=20,
        hooks=FileRunnerHooks()
    )
     async for event in result.stream_events():
        if event.type == "raw_response_event":
            continue
        elif event.type == "agent_updated_stream_event":
            await  cl.Message(content=f"Agent updated: {event.new_agent.name}").send()
            continue
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
               await  cl.Message(content=f"Tool Called").send()
            elif event.item.type == "message_output_item":
              await   cl.Message(content=ItemHelpers.text_message_output(event.item)).send()
            else:
                pass 
    except InputGuardrailTripwireTriggered:
             await    cl.Message(content=f"Sorry I cannot answer you with that!").send()
    except OutputGuardrailTripwireTriggered:
        await   cl.Message(content=f"Sorry I cannot answer you with that!").send()
                     
            
    
  
    

   

       