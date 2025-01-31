from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
import os
import logging

logger = logging.getLogger(__name__)

# Initialize text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file(file_path):
    """Process a single file and return chunks."""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        logger.debug(f"Processing file with extension: {file_extension}")
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.docx':
            loader = Docx2txtLoader(file_path)
        else:  # .txt files
            loader = TextLoader(file_path)
            
        documents = loader.load()
        chunks = text_splitter.split_documents(documents)
        logger.debug(f"Successfully processed file into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise