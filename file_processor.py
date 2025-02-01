# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
# import os
# import logging

# logger = logging.getLogger(__name__)

# # Initialize text splitter
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,
#     chunk_overlap=200
# )

# def allowed_file(filename):
#     """Check if file extension is allowed."""
#     ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def process_file(file_path):
#     """Process a single file and return chunks."""
#     try:
#         file_extension = os.path.splitext(file_path)[1].lower()
#         logger.debug(f"Processing file with extension: {file_extension}")
        
#         if file_extension == '.pdf':
#             loader = PyPDFLoader(file_path)
#         elif file_extension == '.docx':
#             loader = Docx2txtLoader(file_path)
#         else:  # .txt files
#             loader = TextLoader(file_path)
            
#         documents = loader.load()
#         chunks = text_splitter.split_documents(documents)
#         logger.debug(f"Successfully processed file into {len(chunks)} chunks")
#         return chunks
#     except Exception as e:
#         logger.error(f"Error processing file {file_path}: {str(e)}")
#         raise


from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.docstore.document import Document
import os
import tempfile
from io import BytesIO
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

def process_file(file_input):
    """
    Process a file and return chunks. Can handle both file paths and file streams.
    
    Args:
        file_input: Either a file path string or a file-like object (BytesIO)
        
    Returns:
        list: List of document chunks
    """
    try:
        # Determine if input is a file path or file stream
        if isinstance(file_input, (str, bytes)):
            file_path = file_input
            file_extension = os.path.splitext(file_path)[1].lower()
            is_file_path = True
        else:
            file_extension = os.path.splitext(file_input.name)[1].lower()
            is_file_path = False
            
        logger.debug(f"Processing file with extension: {file_extension}")
        
        # Handle different file types
        if file_extension == '.pdf':
            if is_file_path:
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            else:
                # For PDFs, we need to save temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    if isinstance(file_input, BytesIO):
                        temp_file.write(file_input.getvalue())
                    else:
                        temp_file.write(file_input.read())
                    temp_path = temp_file.name
                try:
                    loader = PyPDFLoader(temp_path)
                    documents = loader.load()
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
        elif file_extension in ['.doc', '.docx']:
            if is_file_path:
                loader = Docx2txtLoader(file_path)
                documents = loader.load()
            else:
                # For DOCX, we need to save temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                    if isinstance(file_input, BytesIO):
                        temp_file.write(file_input.getvalue())
                    else:
                        temp_file.write(file_input.read())
                    temp_path = temp_file.name
                try:
                    loader = Docx2txtLoader(temp_path)
                    documents = loader.load()
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
        else:  # .txt files
            if is_file_path:
                loader = TextLoader(file_path)
                documents = loader.load()
            else:
                # For text files, we can process directly from memory
                if isinstance(file_input, BytesIO):
                    content = file_input.getvalue().decode('utf-8')
                else:
                    content = file_input.read().decode('utf-8')
                documents = [Document(page_content=content)]
        
        # Split into chunks
        chunks = text_splitter.split_documents(documents)
        logger.debug(f"Successfully processed file into {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise