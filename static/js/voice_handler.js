// Initialize socket connection
const socket = io();
let mediaRecorder = null;
let isProcessingVoice = false;
let isSpeaking = false;

// Socket connection event handlers
socket.on('connect', () => {
    console.log('Connected to WebSocket server');
});

socket.on('connection_status', (data) => {
    console.log('Connection status:', data.status);
});

socket.on('voice_input_result', (data) => {
    console.log('Received voice input result:', data);
    if (data.text) {
        document.getElementById('messageInput').value = data.text;
        // Optionally auto-send the message
        sendMessage();
    }
});

socket.on('voice_output', (data) => {
    console.log('Received voice output');
    if (data.audio) {
        playAudioOutput(data.audio);
    }
});

socket.on('voice_error', (data) => {
    console.error('Voice error:', data.error);
    alert('Voice processing error: ' + data.error);
    stopVoiceInput();
});

// Voice input handling
function startVoiceInput() {
    if (isProcessingVoice) return;

    console.log('Starting voice input...');
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            console.log('Got media stream');
            isProcessingVoice = true;
            document.getElementById('voiceInputBtn').classList.add('active');

            mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            const audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                console.log('Data available from recorder');
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                console.log('MediaRecorder stopped, processing audio...');
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const reader = new FileReader();
                
                reader.onloadend = () => {
                    console.log('Audio converted to base64, sending to server...');
                    socket.emit('voice_data', reader.result);
                };
                
                reader.readAsDataURL(audioBlob);
            };

            console.log('Starting MediaRecorder');
            mediaRecorder.start(100); // Record in 100ms chunks

            // Auto-stop recording after 10 seconds
            setTimeout(() => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    console.log('Auto-stopping after timeout');
                    stopVoiceInput();
                }
            }, 10000);
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            alert('Error accessing microphone. Please check your permissions.');
            stopVoiceInput();
        });
}

function stopVoiceInput() {
    console.log('Stopping voice input...');
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        console.log('MediaRecorder stopped');
    }
    isProcessingVoice = false;
    document.getElementById('voiceInputBtn').classList.remove('active');
}

// Voice output handling
function startVoiceOutput() {
    const lastBotMessage = document.querySelector('.bot-message:last-child');
    if (lastBotMessage) {
        const text = lastBotMessage.innerText;
        console.log('Generating voice output for text:', text);
        socket.emit('generate_voice_output', { text: text });
        document.getElementById('voiceOutputBtn').classList.add('active');
        isSpeaking = true;
    }
}

function playAudioOutput(audioData) {
    const audio = new Audio(audioData);
    audio.onended = () => {
        isSpeaking = false;
        document.getElementById('voiceOutputBtn').classList.remove('active');
    };
    audio.onerror = () => {
        isSpeaking = false;
        document.getElementById('voiceOutputBtn').classList.remove('active');
        alert('Error playing audio');
    };
    audio.play().catch(error => {
        console.error('Error playing audio:', error);
        alert('Error playing audio output');
    });
}

function stopVoiceOutput() {
    isSpeaking = false;
    document.getElementById('voiceOutputBtn').classList.remove('active');
}

// Export functions for use in chat.html
window.toggleVoiceInput = function() {
    if (!isProcessingVoice) {
        startVoiceInput();
    } else {
        stopVoiceInput();
    }
};

window.toggleVoiceOutput = function() {
    if (!isSpeaking) {
        startVoiceOutput();
    } else {
        stopVoiceOutput();
    }
};

// Also export these functions for direct access if needed
window.startVoiceInput = startVoiceInput;
window.stopVoiceInput = stopVoiceInput;
window.startVoiceOutput = startVoiceOutput;
window.stopVoiceOutput = stopVoiceOutput;