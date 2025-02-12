import streamlit as st
import openai
import tempfile
import os

# API Key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Streamlit UI
st.set_page_config(page_title="Voice to Image AI", layout="wide")

st.title("🎙️ Voice to Image AI Generator")
st.markdown("### Convert your voice into AI-generated images!")

# Layout: Split screen into two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("## 🎤 Record Your Voice")

    recorder_html = """
        <style>
            .record-btn { background-color: #ff4757; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 5px; }
            .stop-btn { background-color: #1e90ff; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 5px; }
            .download-btn { background-color: #2ed573; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-size: 14px; text-decoration: none; display: inline-block; margin-top: 10px; }
        </style>
        <script>
        let mediaRecorder;
        let audioChunks = [];
        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                document.getElementById('recording-status').innerText = "🔴 Recording...";
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };
                mediaRecorder.onstop = () => {
                    let audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    let audioUrl = URL.createObjectURL(audioBlob);
                    let downloadLink = document.getElementById('audio-download');
                    downloadLink.href = audioUrl;
                    downloadLink.download = "recorded_audio.wav";
                    downloadLink.style.display = "block";
                    document.getElementById('recording-status').innerText = "✅ Recording Stopped.";
                };
            });
        }
        function stopRecording() {
            mediaRecorder.stop();
        }
        </script>
        <button class="record-btn" onclick="startRecording()">🎤 Start Recording</button>
        <button class="stop-btn" onclick="stopRecording()">⏹ Stop Recording</button>
        <p id="recording-status">⚪ Not Recording</p>
        <a id="audio-download" class="download-btn" style="display:none;">⬇ Download Audio</a>
    """
    st.components.v1.html(recorder_html, height=200)

    st.markdown("## ⬆ Upload Recorded Audio")
    uploaded_file = st.file_uploader("Upload your recorded .wav file", type=["wav"])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(uploaded_file.read())
            audio_file_path = temp_audio.name
        st.success("✅ File uploaded successfully!")

        # Transcription Step
        st.markdown("## 📝 Transcribing Speech...")
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        os.remove(audio_file_path)  # Clean up the temp file
        transcript = transcription.text
        st.success(f"📝 Transcription: {transcript}")

        # Prompt Refinement
        st.markdown("## 💡 Refining Prompt with ChatGPT")
        chatgpt_prompt = f"Convert this into a detailed image description for AI art: '{transcript}'"
        
        chatgpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that generates creative and detailed image prompts."},
                {"role": "user", "content": chatgpt_prompt}
            ]
        )
        
        refined_prompt = chatgpt_response.choices[0].message.content
        st.success(f"🎨 Refined Prompt: {refined_prompt}")

        # Generate Image
        st.markdown("## 🎨 Generating Image...")
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=refined_prompt,
            n=1,
            size="1024x1024"
        )
        image_url = dalle_response.data[0].url

with col2:
    if "image_url" in locals():
        st.image(image_url, caption="✨ AI-Generated Image ✨", use_column_width=True)
