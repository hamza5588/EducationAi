
from dotenv import load_dotenv

load_dotenv()


from langchain_google_genai import GoogleGenerativeAIEmbeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key="AIzaSyDaUzWnAuFZDx1O6J_Xc_AEcZwkiW0aOOE")



from langchain_google_genai import ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash",google_api_key="AIzaSyDaUzWnAuFZDx1O6J_Xc_AEcZwkiW0aOOE")






import bs4
from langchain import hub

from langchain.chains import create_retrieval_chain

from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain_core.prompts import ChatPromptTemplate

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.prompts import MessagesPlaceholder



from langchain.chains.combine_documents import create_stuff_documents_chain

prompt = ChatPromptTemplate.from_template("""You are an AI chatbot simulating a patient for paramedic students practicing clinical assessments.
    Respond accurately using the predefined question:answer pairs for clinical-related inquiries
    If no predefined answer exists, provide a general conversational response while staying in character as a patient.

<context>
{context}
</context>

Question: {input}""")

from langchain_community.vectorstores import FAISS
document_chain = create_stuff_documents_chain(model, prompt)

vector2 = FAISS.load_local("faissindexupdate", embeddings, allow_dangerous_deserialization=True)

system_prompt = (
    "You are an AI chatbot simulating a patient for paramedic students practicing clinical assessments. "
    "Respond accurately using the predefined question:answer pairs for clinical-related inquiries. "
    "If no predefined answer exists, provide a general conversational response while staying in character as a patient. "
    "{context}"
)

from langchain.chains import create_retrieval_chain

retriever = vector2.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, document_chain)

response = retrieval_chain.invoke({"input": "whats going on?"})
a=response["answer"]

print(response["answer"])

from langchain.chains import create_history_aware_retriever

retriever_prompt = (
    "Given a chat history and the latest user question which might reference context in the chat history,"
    "formulate a standalone question which can be understood without the chat history."
    "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt  = ChatPromptTemplate.from_messages(
    [
        ("system", retriever_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),


     ]
)

history_aware_retriever = create_history_aware_retriever(model,retriever,contextualize_q_prompt)

from langchain.chains import create_retrieval_chain

from langchain.chains.combine_documents import create_stuff_documents_chain

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(model, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

from langchain_core.messages import HumanMessage, AIMessage




from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

result=conversational_rag_chain.invoke(
    {"input": "just pain in chest or any other part also?"},
    config={
        "configurable": {"session_id": "abc123"}
    },  # constructs a key "abc123" in `store`.
)["answer"]

print(result)

