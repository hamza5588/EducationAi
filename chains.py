# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_community.vectorstores import FAISS
# from embeddings import chat_model, embeddings
# from langchain.chains import create_history_aware_retriever

# # Define prompt templates
# prompt_template = ChatPromptTemplate.from_template(
#     """Answer questions following these teaching principles and steps:
#     1. Introduce yourself as Mr. Potter
#     2. Ask for and remember student names
#     3. Provide patient, step-by-step guidance
#     4. Break down complex problems into simpler ones
#     5. Check understanding and adjust difficulty accordingly
    
#     <context>
#     {context}
#     </context>
    
#     Question: {input}"""
# )

# system_prompt = (
#     "You are the top high school teacher, Mr. Potter, known for your patience and understanding. "
#     "Your teaching approach follows these specific steps:\n\n"
#     "1. Begin every interaction with 'Hello, my name is Mr. Potter.'\n"
#     "2. Ask 'Can I have your name?' and remember it for future interactions\n"
#     "3. Ask '[student name], how can I help you today?'\n"
#     "4. Break down problems into simpler components to identify gaps in understanding\n"
#     "5. Provide tailored explanations based on student responses\n"
#     "6. Verify understanding by offering practice problems\n"
#     "7. Let students choose to check understanding or tackle more challenges\n"
#     "8. Adjust problem difficulty based on student progress\n\n"
#     "Always maintain patience, provide encouragement, and ensure complete understanding "
#     "before moving to more complex topics. Match questions to appropriate grade levels."
#     "{context}"
# )


# # Create RAG chain function
# def create_conversational_chain(vectorstore):
#     if vectorstore is None:
#         return None
        
#     # Create document chain
#     document_chain = create_stuff_documents_chain(chat_model, prompt_template)
    
#     # Create retriever
#     retriever = vectorstore.as_retriever()

#     # Create history-aware retriever
#     history_aware_retriever = create_history_aware_retriever(
#         chat_model, 
#         retriever,
#         ChatPromptTemplate.from_messages([
#             ("system", "Given a chat history and the latest user question..."),
#             MessagesPlaceholder(variable_name="chat_history"),
#             ("human", "{input}"),
#         ])
#     )

#     # Create final question-answering chain
#     qa_prompt = ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         MessagesPlaceholder("chat_history"),
#         ("human", "{input}"),
#     ])
#     question_answer_chain = create_stuff_documents_chain(chat_model, qa_prompt)

#     # Create and return the RAG chain
#     return create_retrieval_chain(history_aware_retriever, question_answer_chain)

#chains.py

# chains.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from embeddings import embeddings, get_chat_model

# Common system prompt for both scenarios
SYSTEM_PROMPT = """You are the top high school teacher, Mr. Potter, known for your patience and understanding. 
Your teaching approach follows these specific steps:

1. Begin every interaction with 'Hello, my name is Mr. Potter.'
2. Ask 'Can I have your name?' and remember it for future interactions
3. Ask '[student name], how can I help you today?'
4. Break down problems into simpler components to identify gaps in understanding
5. Provide tailored explanations based on student responses
6. Verify understanding by offering practice problems
7. Let students choose to check understanding or tackle more challenges
8. Adjust problem difficulty based on student progress

Always maintain patience, provide encouragement, and ensure complete understanding 
before moving to more complex topics. Match questions to appropriate grade levels."""

def create_conversational_chain(user_id, vectorstore=None):
    """Create a conversation chain with the provided user_id."""
    chat_model = get_chat_model(user_id)  # Get chat model for specific user
    
    if vectorstore is None:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        chain = prompt | chat_model
        
        return RunnablePassthrough.assign(
            answer=chain,
            chat_history=lambda x: x.get("chat_history", [])
        )
    
    # Create RAG chain if vectorstore exists
    rag_prompt = ChatPromptTemplate.from_template(
        """Answer questions following these teaching principles and steps while incorporating the context:
        1. Introduce yourself as Mr. Potter
        2. Ask for and remember student names
        3. Provide patient, step-by-step guidance
        4. Break down complex problems into simpler ones
        5. Check understanding and adjust difficulty accordingly
        
        <context>
        {context}
        </context>
        
        Question: {input}"""
    )
    
    document_chain = create_stuff_documents_chain(chat_model, rag_prompt)
    retriever = vectorstore.as_retriever()

    return create_retrieval_chain(
        retriever, 
        document_chain
    )
def create_regular_chain(chat_model):
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    chain = prompt | chat_model
    
    return RunnablePassthrough.assign(
        answer=chain,
        chat_history=lambda x: x.get("chat_history", [])
    )

def create_rag_chain(chat_model, vectorstore):
    # Create document chain
    rag_prompt = ChatPromptTemplate.from_template(
        """Answer the question from document if not found used your own knowlege to answer the question
        <context>
        {context}
        </context>
        
        Question: {input}"""
    )
    
    document_chain = create_stuff_documents_chain(chat_model, rag_prompt)
    
    # Create retriever
    retriever = vectorstore.as_retriever()

    # Create history-aware retriever
    history_aware_retriever = create_history_aware_retriever(
        chat_model, 
        retriever,
        ChatPromptTemplate.from_messages([
            ("system", "Given a chat history and the latest user question, create a search query."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
    )

    # Create and return the RAG chain
    return create_retrieval_chain(
        history_aware_retriever, 
        document_chain
    )

def format_chat_history(messages):
    formatted_messages = []
    for msg in messages:
        content = msg.get('content', msg.get('message', ''))
        if msg['role'] == 'user':
            formatted_messages.append(HumanMessage(content=content))
        elif msg['role'] in ['bot', 'assistant']:
            formatted_messages.append(AIMessage(content=content))
    return formatted_messages