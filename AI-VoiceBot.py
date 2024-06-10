# -*- coding: utf-8 -*-
"""SS.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1RkCrj0CjOjT6ty_Gf4lxyYyzvFo3j40Z
"""

!python --version

!pip install spacy

!pip install SpeechRecognition

!pip install Flask pyngrok

!ngrok config add-authtoken 2heCcq4TPQiHHdzzd0c6iPQSPpz_3pDbga4tsLSQGDnsSKJ6V

!pip install transformers
!pip install torch

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "microsoft/DialoGPT-medium"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

def generate_response(user_input):
    global chat_history_ids

    new_user_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')

    bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if chat_history_ids is not None else new_user_input_ids

    chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

    response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

    return response

chat_history_ids = None

while True:
    user_input = input("User: ")
    if user_input.lower() == 'exit':
        break

    response = generate_response(user_input)
    print(f"Bot: {response}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot with Voice Recording</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        #chat-container {
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
        }
        #messages {
            border: 1px solid #ccc;
            padding: 10px;
            height: 300px;
            overflow-y: scroll;
            margin-bottom: 10px;
        }
        #input-container {
            display: flex;
            align-items: center;
        }
        #textInput {
            flex: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-right: 10px;
        }
        #recordButton, #stopButton, #sendButton {
            padding: 10px 15px;
            margin-right: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        #recordButton {
            background-color: #28a745;
            color: white;
        }
        #stopButton {
            background-color: #dc3545;
            color: white;
            display: none;
        }
        #sendButton {
            background-color: #007bff;
            color: white;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <h1>Chatbot</h1>
        <div id="messages"></div>
        <div id="input-container">
            <input type="text" id="textInput" placeholder="Type your message...">
            <button id="recordButton">Record</button>
            <button id="stopButton">Stop</button>
            <button id="sendButton">Send</button>
        </div>
        <audio id="audioPlayback" controls style="display: none;"></audio>
    </div>

    <script>
        let recordButton = document.getElementById('recordButton');
        let stopButton = document.getElementById('stopButton');
        let sendButton = document.getElementById('sendButton');
        let textInput = document.getElementById('textInput');
        let messagesDiv = document.getElementById('messages');
        let audioPlayback = document.getElementById('audioPlayback');

        let chunks = [];
        let recorder;
        let stream;

        recordButton.addEventListener('click', async () => {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            recorder = new MediaRecorder(stream);

            recorder.ondataavailable = event => {
                chunks.push(event.data);
            };

            recorder.onstop = () => {
                let blob = new Blob(chunks, { type: 'audio/wav' });
                chunks = [];
                let audioURL = URL.createObjectURL(blob);
                audioPlayback.src = audioURL;
                audioPlayback.style.display = 'block';

                // Append audio element to messages
                let audioElement = document.createElement('audio');
                audioElement.controls = true;
                audioElement.src = audioURL;
                messagesDiv.appendChild(audioElement);
                messagesDiv.appendChild(document.createElement('br'));
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                // Send audio to backend
                sendAudioMessage(blob);

                // Reset buttons
                recordButton.style.display = 'inline';
                stopButton.style.display = 'none';
            };

            recorder.start();
            recordButton.style.display = 'none';
            stopButton.style.display = 'inline';
        });

        stopButton.addEventListener('click', () => {
            recorder.stop();
            stream.getTracks().forEach(track => track.stop());
        });

        sendButton.addEventListener('click', () => {
            let text = textInput.value.trim();
            if (text) {
                appendMessage(text, 'user');
                textInput.value = '';
                // Placeholder: Replace with actual call to chatbot backend
                setTimeout(() => appendMessage('Hello!', 'bot'), 1000);
            }
        });

        function sendAudioMessage(blob) {
            appendMessage("Sending audio to backend...", 'user');

            let formData = new FormData();
            formData.append('file', blob, 'audio.wav');

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                appendMessage(data.transcript, 'bot');
            })
            .catch(error => {
                console.error('Error:', error);
                appendMessage("Audio is processsing...", 'bot');
            });
        }

        function appendMessage(message, sender) {
            let messageElement = document.createElement('div');
            messageElement.textContent = message;
            messageElement.style.padding = '10px';
            messageElement.style.marginBottom = '5px';
            messageElement.style.borderRadius = '4px';
            if (sender === 'user') {
                messageElement.style.backgroundColor = '#dcf8c6';
                messageElement.style.textAlign = 'right';
            } else {
                messageElement.style.backgroundColor = '#f1f1f1';
            }
            messagesDiv.appendChild(messageElement);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
"""

from google.colab import drive
drive.mount('/content/drive')
folder_path = "/content/drive/MyDrive/DataScienceProjects/template"

from flask import Flask, render_template_string, request, jsonify
from pyngrok import ngrok
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        text = "Google Speech Recognition could not understand audio"
    except sr.RequestError as e:
        text = f"Could not request results from Google Speech Recognition service; {e}"

    os.remove(file_path)
    return jsonify({"transcript": text})

app.config['UPLOAD_FOLDER'] = folder_path
TOKEN_NGROK = '2heCcq4TPQiHHdzzd0c6iPQSPpz_3pDbga4tsLSQGDnsSKJ6V'
ngrok.set_auth_token(TOKEN_NGROK)
public_url = ngrok.connect(5000)

print(f" * ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:5000\"")

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run()