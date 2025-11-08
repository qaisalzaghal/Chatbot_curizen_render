from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import create_retriever_tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.agent_toolkits import GmailToolkit
from langchain_google_community import CalendarToolkit
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
#from vectorstore import retriever
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from fastapi import FastAPI, Request
import cassio
from langchain_community.vectorstores import Cassandra
import os
import pickle

from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "curizen_chatbot_code"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_ID = os.getenv("ASTRA_DB_ID")


cassio.init(token=ASTRA_DB_APPLICATION_TOKEN, database_id=ASTRA_DB_ID)

embeddings = OpenAIEmbeddings()

# Connect to your vector collection
Cassandra_data = Cassandra(
    embedding=embeddings,
    table_name="qa_mini_demo"   # your existing data
)

# Create retriever
retriever_astra = Cassandra_data.as_retriever(search_kwargs={"k": 3})

# Define scopes for both Gmail and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.calendars',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.acls',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.app.created',
    'https://www.googleapis.com/auth/calendar.calendarlist',
    'https://www.googleapis.com/auth/calendar.calendarlist.readonly',
    'https://www.googleapis.com/auth/calendar.calendars.readonly',
    'https://www.googleapis.com/auth/calendar.events.owned',
    'https://www.googleapis.com/auth/calendar.events.readonly',
    'https://www.googleapis.com/auth/calendar.freebusy',
    'openid'
]

def get_google_credentials():
    """Get Google credentials with both Gmail and Calendar scopes"""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

# Get credentials with both Gmail and Calendar scopes
credentials = get_google_credentials()

# Initialize LLM
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

retriever_tool_astra = create_retriever_tool(
    retriever_astra,
    "curizen_knowledge_base_astra",
    "Search and return information about Curizen company. Use this tool when you need to answer questions about Curizen's services, products, or company information.",
)

# Initialize Gmail toolkit
gmail_toolkit = GmailToolkit()
gmail_tools = gmail_toolkit.get_tools()

# Build Calendar API resource manually with proper scopes
calendar_api_resource = build('calendar', 'v3', credentials=credentials)

# Initialize Google Calendar toolkit with the API resource
calendar_toolkit = CalendarToolkit(api_resource=calendar_api_resource)
calendar_tools = calendar_toolkit.get_tools()

# Combine all tools
tools = [retriever_tool_astra] + gmail_tools + calendar_tools

# Create the agent with LangGraph
agent = create_react_agent(
    llm, 
    tools,
    prompt="""You are a helpful assistant working with Curizen company. 
You have access to tools that can help you answer questions about the company, manage Gmail, and manage Google Calendar.

Available capabilities:
- Answer questions about Curizen using the knowledge base
- Search, read, send emails, and create drafts in Gmail
- Create, view, update, and delete calendar events
- Check availability and schedule meetings

Always use the available tools to retrieve accurate information before answering questions about Curizen.
For Gmail-related requests, use the appropriate Gmail tools.
For calendar-related requests, use the Google Calendar tools to manage events and schedules.

If you don't find relevant information in the knowledge base, say so honestly."""
)

# Session management
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def run_agent(user_input: str, session_id: str):
    """Run the agent with chat history"""
    
    # Get chat history
    chat_history = get_session_history(session_id)
    
    # Prepare messages with history
    messages = [
        *[msg for msg in chat_history.messages],  # Add history
        HumanMessage(content=user_input)  # Add new user message
    ]
    
    # Invoke the agent
    result = agent.invoke({"messages": messages})
    
    # Extract the final response
    final_message = result["messages"][-1]
    response_content = final_message.content
    
    # Save to chat history
    chat_history.add_user_message(user_input)
    chat_history.add_ai_message(response_content)
    
    return response_content

# Main conversation loop
print("Curizen Chatbot with Gmail & Calendar Integration (type 'exit' or 'quit' to stop)")
print("-" * 70)
print("\nAvailable capabilities:")
print("- Ask questions about Curizen company")
print("- Search and read Gmail messages")
print("- Send emails and create email drafts")
print("- Create, view, update, and delete calendar events")
print("- Schedule meetings and check availability")
print("-" * 70)


app = FastAPI()

@app.post("/curizen_chatbot")
async def chat(request: Request):
    data = await request.json()
    user_input_query = data.get("message", "")
    user_input_session = data.get("session_id", "")

    if user_input_query.lower() in ["exit", "quit"]:
        print("Goodbye!")
        return {"response": "Goodbye!"}
    else:
        try:
            response = run_agent(user_input_query, user_input_session)
            return {"response": response}
        except Exception as e:
            print(f"Error occurred: {e}")
            return {"error": str(e)}



"""
while True:
    user_input_query = input("\nUser: ")
    
    if user_input_query.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break
    
    user_input_session = input("Session ID: ")
    
    try:
        response = run_agent(user_input_query, user_input_session)
        print(f"\nAssistant: {response}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
"""