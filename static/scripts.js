function sendMessage() {
    const inputField = document.getElementById('user-input');
    const userInput = inputField.value.trim();

    if (userInput) {
        appendMessage(userInput, 'user-message');
        inputField.value = '';

        fetch('/chat', {
            method: 'POST',  // This specifies the POST method
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input: userInput,
                session_id: "default_session" // Adjust if needed
            }),
        })
        .then(response => response.json())
        .then(data => {
            appendMessage(data.response, 'bot-message');
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage("Error: Could not get a response.", 'bot-message');
        });
    }
}
