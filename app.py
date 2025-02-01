from io import BytesIO
from venv import logger
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import logging
import sqlite3
from chains import create_conversational_chain, format_chat_history

from history import get_session_history
from langchain_core.runnables.history import RunnableWithMessageHistory
from embeddings import embeddings
from file_processor import process_file, allowed_file
from langchain_community.vectorstores import FAISS

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
from datetime import datetime
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import logging
from db import get_db_connection
from chains import create_conversational_chain
from models import embeddings, get_chat_model

from io import BytesIO
import tempfile
from langchain.docstore.document import Document

# Set up Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Database connection
def get_db_connection():
    conn = sqlite3.connect('chat.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ensure the database and tables exist
# In app.py, update the initialize_database function
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            useremail TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            class_standard TEXT NOT NULL,
            medium TEXT NOT NULL,
            groq_api_key TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    ''')
    
    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Create chat_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'bot')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
# Initialize the database
initialize_database()


# In app.py, add this at the top
vectorstore = None
# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        useremail = request.form['useremail']
        password = request.form['password']
        class_standard = request.form['class_standard']
        medium = request.form['medium']
        groq_api_key = request.form['groq_api_key']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (username, useremail, password, class_standard, medium, groq_api_key) VALUES (?, ?, ?, ?, ?, ?)',
                (username, useremail, password, class_standard, medium, groq_api_key)
            )
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username or email already exists!"
        finally:
            conn.close()
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        useremail = request.form['useremail']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE useremail = ? AND password = ?', (useremail, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['groq_api_key'] = user['groq_api_key'] 
            return redirect(url_for('index'))
        else:
            return "Invalid email or password!"
    return render_template('login.html')


@app.route('/')
def index():
    print("Session in index route:", session)  # Debugging line
    if 'user_id' not in session:
        print("User not logged in, redirecting to login page")  # Debugging line
        return redirect(url_for('login'))
    return render_template('chat.html')

# Create a new conversation
@app.route('/create_conversation', methods=['POST'])
def create_conversation():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.json
    title = data.get('title', 'New Conversation')  # Default title

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO conversations (user_id, title) VALUES (?, ?)',
        (session['user_id'], title)
    )
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'conversation_id': conversation_id, 'title': title})

# Get all conversations for the user
@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    conn = get_db_connection()
    conversations = conn.execute('''
        SELECT c.id, COALESCE(c.title, ch.message) AS title
        FROM conversations c
        LEFT JOIN chat_history ch ON c.id = ch.conversation_id AND ch.role = 'user'
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in conversations])

    return jsonify([dict(row) for row in conversations])

# Get messages for a specific conversation
@app.route('/get_messages/<int:conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    conn = get_db_connection()
    messages = conn.execute('''
        SELECT message, role, created_at
        FROM chat_history
        WHERE conversation_id = ?
        ORDER BY created_at
    ''', (conversation_id,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in messages])

# Save a message to a conversation
@app.route('/save_message', methods=['POST'])
def save_message():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.json
    conversation_id = data.get('conversation_id')
    message = data.get('message')
    role = data.get('role')  # 'user' or 'bot'

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO chat_history (conversation_id, message, role) VALUES (?, ?, ?)',
        (conversation_id, message, role)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    global vectorstore
    
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
            
        files = request.files.getlist('files')
        all_chunks = []
        
        for file in files:
            if file and allowed_file(file.filename):
                logger.info(f"Processing file: {file.filename}")
                try:
                    # Convert file to BytesIO for in-memory processing
                    file_content = file.read()
                    file_stream = BytesIO(file_content)
                    file_stream.name = file.filename  # Important: set name for extension checking
                    
                    # Process the file
                    chunks = process_file(file_stream)
                    all_chunks.extend(chunks)
                    logger.info(f"Successfully processed {file.filename}")
                    
                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
                    continue
        
        if not all_chunks:
            return jsonify({'error': 'No valid content was found in the uploaded files'}), 400
        
        try:
            if vectorstore is None:
                vectorstore = FAISS.from_documents(all_chunks, embeddings)
                logger.info("Created new vectorstore")
            else:
                vectorstore.add_documents(all_chunks)
                logger.info("Added documents to existing vectorstore")
                
            return jsonify({'message': 'Files processed successfully'})
            
        except Exception as e:
            logger.error(f"Error with vectorstore: {str(e)}")
            return jsonify({'error': 'Error processing document for chat context'}), 500
            
    except Exception as e:
        logger.error(f"Error in upload: {str(e)}")
        return jsonify({'error': str(e)}), 500
# @app.route('/upload', methods=['POST'])
# def upload_file():
#     global vectorstore
    
#     try:
#         if 'files' not in request.files:
#             return jsonify({'error': 'No files provided'}), 400
            
#         files = request.files.getlist('files')
#         all_chunks = []
        
#         for file in files:
#             if file and allowed_file(file.filename):
#                 filename = secure_filename(file.filename)
#                 temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#                 file.save(temp_path)
                
#                 try:
#                     chunks = process_file(temp_path)
#                     all_chunks.extend(chunks)
#                 finally:
#                     if os.path.exists(temp_path):
#                         os.remove(temp_path)
        
#         if not all_chunks:
#             return jsonify({'error': 'No valid content was found in the uploaded files'}), 400
        
#         if vectorstore is None:
#             vectorstore = FAISS.from_documents(all_chunks, embeddings)
#         else:
#             vectorstore.add_documents(all_chunks)
            
#         return jsonify({'message': 'Files processed successfully'})
        
#     except Exception as e:
#         logger.error(f"Error in upload: {str(e)}")
#         return jsonify({'error': str(e)}), 500


# Add this route to your Flask application
@app.route('/update_api_key', methods=['POST'])
def update_api_key():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
        
    try:
        data = request.json
        new_api_key = data.get('api_key')
        
        if not new_api_key:
            return jsonify({'error': 'API key is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update the API key for the current user
        cursor.execute(
            'UPDATE users SET groq_api_key = ? WHERE id = ?',
            (new_api_key, session['user_id'])
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'API key updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


from langchain_core.messages import HumanMessage
from langchain.schema import SystemMessage

def get_db_connection():
    conn = sqlite3.connect('chat.db')
    conn.row_factory = sqlite3.Row
    return conn
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import MessagesPlaceholder

# Global memory store
conversation_histories = {}

def get_or_create_memory(conversation_id):
    if conversation_id not in conversation_histories:
        conversation_histories[conversation_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return conversation_histories[conversation_id]
# 1. Update the chat route to use 'bot' instead of 'assistant'
# Add these imports at the top of the file
from langchain_core.messages import HumanMessage, AIMessage
from langchain.schema import SystemMessage
@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    try:
        data = request.json
        user_id = session['user_id']
        user_input = data.get('input', '')
        conversation_id = data.get('conversation_id')

        if not user_input.strip():
            return jsonify({'error': 'Empty message'}), 400

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create new conversation if none exists
        if not conversation_id:
            cursor.execute(
                'INSERT INTO conversations (user_id, title) VALUES (?, ?)',
                (user_id, user_input[:50])
            )
            conversation_id = cursor.lastrowid
            conn.commit()

        # Save user message
        cursor.execute(
            'INSERT INTO chat_history (conversation_id, message, role) VALUES (?, ?, ?)',
            (conversation_id, user_input, 'user')
        )
        conn.commit()

        try:
            # Get chat model and create chain
            chat_model = get_chat_model(user_id)
            chain = create_conversational_chain(user_id, vectorstore)

            # Get chat history
            cursor.execute('''
                SELECT message, role
                FROM chat_history
                WHERE conversation_id = ?
                ORDER BY created_at
            ''', (conversation_id,))
            
            # Format history for chain
            chain_history = []
            for row in cursor.fetchall():
                message = row['message']
                if row['role'] == 'user':
                    chain_history.append(HumanMessage(content=message))
                elif row['role'] == 'bot':
                    chain_history.append(AIMessage(content=message))

            # Get response from chain
            response = chain.invoke({
                "input": user_input,
                "chat_history": chain_history
            })
            
            # Extract the response content
            if isinstance(response.get('answer'), str):
                bot_response = response['answer']
            else:
                bot_response = response['answer'].content

            if not bot_response or not isinstance(bot_response, str):
                raise ValueError("Invalid response from chat model")

            # Save bot response
            cursor.execute(
                'INSERT INTO chat_history (conversation_id, message, role) VALUES (?, ?, ?)',
                (conversation_id, bot_response, 'bot')
            )
            
            cursor.execute(
                'UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (conversation_id,)
            )
            conn.commit()

            return jsonify({
                'response': bot_response,
                'conversation_id': conversation_id
            })

        except Exception as e:
            error_message = str(e)
            
            # Check for specific error types
            if "gsk_" in error_message or "API key" in error_message:
                return jsonify({
                    'error': 'Invalid API key. Please update your API key in settings.'
                }), 400
            
            # Handle other invalid API key scenarios
            if "unauthorized" in error_message.lower() or "invalid" in error_message.lower():
                return jsonify({
                    'error': 'Your API key appears to be invalid. Please check and update it in settings.'
                }), 400
                
            # For all other errors
            logger.error(f"Error in chat model processing: {error_message}")
            return jsonify({
                'error': 'There was an error processing your message. Please make sure your API key is valid.'
            }), 500

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({
            'error': 'Please check your API key in settings and try again.'
        }), 500
        
    finally:
        if 'conn' in locals():
            conn.close()

def format_chat_history(messages):
    """
    Format chat history for the chain.
    
    Args:
        messages (list): List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        list: Formatted messages for the chain
    """
    formatted_messages = []
    for msg in messages:
        content = msg.get('content', msg.get('message', ''))
        if msg['role'] == 'user':
            formatted_messages.append(HumanMessage(content=content))
        elif msg['role'] in ['bot', 'assistant']:
            formatted_messages.append(AIMessage(content=content))
    return formatted_messages
    

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    conn = get_db_connection()
    chat_history = conn.execute('''
        SELECT ch.message, ch.role, ch.created_at
        FROM chat_history ch
        JOIN conversations c ON ch.conversation_id = c.id
        WHERE c.user_id = ?
        ORDER BY ch.created_at
    ''', (session['user_id'],)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in chat_history])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # Change the port to match Render's expected port
