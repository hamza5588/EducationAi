from flask_socketio import SocketIO, emit
from flask import request
from langchain_openai import ChatOpenAI
import base64
import tempfile
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio = SocketIO()

class VoiceWebSocketHandler:
    def __init__(self):
        try:
            logger.info("Initializing VoiceWebSocketHandler...")
            load_dotenv()
            
            # Initialize LangChain ChatOpenAI with audio capabilities
            self.llm = ChatOpenAI(
                model="gpt-4o-audio-preview",
                temperature=0,
                model_kwargs={
                    "modalities": ["text", "audio"],
                    "audio": {"voice": "alloy", "format": "wav"},
                }
            )
            
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            logger.info("LangChain model initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing handler: {str(e)}")
            raise

    def initialize_socket_events(self):
        @socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            emit('connection_status', {'status': 'connected'})

        @socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Client disconnected: {request.sid}")

        @socketio.on('voice_data')
        def handle_voice_data(data):
            try:
                logger.info("Received voice data")
                
                # Handle potential string or binary data
                if isinstance(data, str):
                    # Decode base64 audio data
                    audio_bytes = base64.b64decode(data.split(',')[1] if ',' in data else data)
                else:
                    audio_bytes = data
                
                logger.info(f"Decoded audio size: {len(audio_bytes)} bytes")
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_bytes)
                    temp_path = temp_file.name
                    logger.info(f"Saved audio to temporary file: {temp_path}")

                try:
                    # Process audio using LangChain
                    logger.info("Processing audio with LangChain...")
                    messages = [("human", "Transcribe this audio and respond appropriately.")]
                    response = self.llm.invoke(messages)
                    
                    # Extract text response
                    text_response = response.content
                    logger.info(f"Generated text response: {text_response}")
                    
                    emit('voice_input_result', {
                        'text': text_response
                    })

                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        logger.info("Cleaned up temporary file")

            except Exception as e:
                logger.error(f"Error processing voice input: {str(e)}", exc_info=True)
                emit('voice_error', {'error': str(e)})

        @socketio.on('generate_voice_output')
        def handle_generate_voice_output(data):
            try:
                text = data.get('text', '')
                logger.info(f"Generating voice output for text: {text}")
                
                if not text:
                    logger.warning("No text provided for voice output")
                    emit('voice_error', {'error': 'No text provided'})
                    return

                # Generate voice response using LangChain
                logger.info("Calling LangChain for voice generation...")
                messages = [("human", text)]
                response = self.llm.invoke(messages)
                
                # Extract audio from response
                if 'audio' in response.additional_kwargs:
                    audio_data = response.additional_kwargs['audio']['data']
                    logger.info("Voice generated successfully")
                    
                    # Send base64 audio data to client
                    emit('voice_output', {
                        'audio': f'data:audio/wav;base64,{audio_data}'
                    })
                else:
                    logger.warning("No audio generated")
                    emit('voice_error', {'error': 'No audio generated'})

            except Exception as e:
                logger.error(f"Error generating voice output: {str(e)}", exc_info=True)
                emit('voice_error', {'error': str(e)})