from openai import OpenAI
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import pydub
import time
import io
client = OpenAI()
from playsound import playsound


# Initialize recognizer
r = sr.Recognizer()
mic = sr.Microphone()
assist_phrase = ["How may I help you?", "Would you like to go to the next step?", "Have a great day Mr Shade"]
valid_wake = False
AudioSegment.converter = "C:\\Users\\zacha\\Downloads\\ffmpeg-7.0-full_build\\ffmpeg-7.0-full_build\\bin\\ffmpeg.exe"

def record_until_silence_keyword():
    # Start listening to the microphone
    with mic as source:
        print("Listening for keyword...")
        r.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        audio = r.listen(source)  # Listen until silence\
        # Convert SpeechRecognition audio data to audio bytes
        audio_bytes = audio.get_wav_data()

        # Use AudioSegment to process the raw byte data
        audio_segment = AudioSegment.from_wav(io.BytesIO(audio_bytes))

        # Detect chunks of audio based on silence
        chunks = split_on_silence(
            audio_segment,
            min_silence_len=3000,
            silence_thresh=audio_segment.dBFS-14,
            keep_silence=500
        )

        return chunks[0] if chunks else None
    

def record_until_silence_prompt():
    # Start listening to the microphone
    with mic as source:
        r.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        audio = r.listen(source)  # Listen until silence
        # Convert SpeechRecognition audio data to audio bytes
        audio_bytes = audio.get_wav_data()

        # Use AudioSegment to process the raw byte data
        audio_segment = AudioSegment.from_wav(io.BytesIO(audio_bytes))

        # Detect chunks of audio based on silence
        chunks = split_on_silence(
            audio_segment,
            min_silence_len=3000,
            silence_thresh=audio_segment.dBFS-14,
            keep_silence=500
        )

        return chunks[0] if chunks else None

def save_audio(audio, filename):
    if audio:
        audio.export(filename, format="mp3")
        print(f"Audio saved as {filename}")
    else:
        print("No audio to save")


def assist_response(inp):
    speech_file_path = "assist_response.mp3"
    with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="alloy",
    input=inp
    ) as response:
        response.stream_to_file(speech_file_path)


assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a master teacher in all things engineering, having full knowledge of electrical, mechanical, and computer science and engineering. You will help me bring my projects to life.",
    model="gpt-4-1106-preview",
)

thread = client.beta.threads.create()

def create_message(mess):
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=mess
    )
    return message


def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

def check_for_keyword(keyword):
    global valid_wake
    audio_file = open("PromptMessage.mp3", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    if keyword in transcription.text:
        return True
    else:
        return False

def get_prompt():
    audio_file = open("PromptMessage.mp3", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text

def get_message():
    run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
    )
    run = wait_on_run(run, thread)

while True:

    try:
        while not valid_wake:
            audio = record_until_silence_keyword()
            save_audio(audio, "PromptMessage.mp3")
            valid_wake = check_for_keyword("Hey GPT")
            print(str(valid_wake))
        if valid_wake:
            assist_response(assist_phrase[0])
            playsound("assist_response.mp3")
            audio = record_until_silence_prompt()
            
            save_audio(audio, "PromptMessage.mp3")
            mess = get_prompt()
            message = create_message(mess)
            get_message() 
            messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc", after=message.id)
            assist_response(messages.data[0].content[0].text.value)
            playsound("assist_response.mp3")
            assist_response(assist_phrase[1])
            playsound("assist_response.mp3")
    except KeyboardInterrupt:
        break

    