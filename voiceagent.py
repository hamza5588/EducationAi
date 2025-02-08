# from agno.agent import Agent, RunResponse
# from agno.models.openai import OpenAIChat
# from agno.utils.audio import write_audio_to_file

# agent = Agent(
#     model=OpenAIChat(
#         id="gpt-4o-audio-preview",
#         modalities=["text", "audio"],
#         audio={"voice": "alloy", "format": "wav"},
#     ),
#     markdown=True,
# )
# response: RunResponse = agent.run("explain tthe archimedus principle")

# # Save the response audio to a file
# if response.response_audio is not None:
#     write_audio_to_file(
#         audio=agent.run_response.response_audio.content, filename="scary_story.wav"
#     )
import base64
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
load_dotenv()  # Load variables from .env file
api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(
    model="gpt-4o-audio-preview",
    temperature=0,
    model_kwargs={
        "modalities": ["text", "audio"],  # We’re telling the model to handle both text and audio
        "audio": {"voice": "alloy", "format": "wav"},  # Configure voice and output format
    }
)

# Send a request and ask the model to respond with audio
messages = [("human", "hi.")]
output_message = llm.invoke(messages)

# Access the generated audio data
audio_response = output_message.additional_kwargs['audio']['data']
# Decode the base64 audio data
audio_bytes = base64.b64decode(output_message.additional_kwargs['audio']['data'])

# Save the audio file
with open("output.wav", "wb") as f:
    f.write(audio_bytes)
print("Audio saved as output.wav")