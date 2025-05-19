import os
import json
import asyncio
import websockets
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import openai
from dotenv import load_dotenv
import numpy as np
import tempfile
import wave
import threading
import queue
import time

class SpeechSystem:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.recognizer = sr.Recognizer()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False
        self.current_npc_voice = "alloy"  # Default voice
        self.voice_settings = {
            "alloy": {"speed": 1.0, "pitch": 1.0, "description": "Balanced, neutral voice"},
            "echo": {"speed": 1.0, "pitch": 1.0, "description": "Clear, articulate voice"},
            "fable": {"speed": 1.0, "pitch": 1.0, "description": "Storytelling, expressive voice"},
            "onyx": {"speed": 0.9, "pitch": 0.9, "description": "Deep, authoritative voice"},
            "nova": {"speed": 1.0, "pitch": 1.1, "description": "Warm, friendly voice"},
            "shimmer": {"speed": 1.1, "pitch": 1.1, "description": "Bright, energetic voice"}
        }
        
        # Emotion-based voice configurations
        self.emotion_voice_mapping = {
            "happy": {"voice": "shimmer", "speed": 1.1, "pitch": 1.1},
            "sad": {"voice": "echo", "speed": 0.9, "pitch": 0.9},
            "angry": {"voice": "onyx", "speed": 1.1, "pitch": 0.9},
            "excited": {"voice": "nova", "speed": 1.2, "pitch": 1.2},
            "calm": {"voice": "alloy", "speed": 1.0, "pitch": 1.0},
            "friendly": {"voice": "nova", "speed": 1.0, "pitch": 1.1},
            "authoritative": {"voice": "onyx", "speed": 0.9, "pitch": 0.9}
        }
        
    def set_npc_voice(self, voice_name, speed=1.0, pitch=1.0):
        """Configure voice settings for an NPC"""
        if voice_name in self.voice_settings:
            self.current_npc_voice = voice_name
            self.voice_settings[voice_name].update({
                "speed": speed,
                "pitch": pitch
            })
            print(f"Set voice to {voice_name} with speed={speed} and pitch={pitch}")
        else:
            print(f"Voice {voice_name} not found, using default voice")
            self.current_npc_voice = "alloy"
            
    def adjust_voice_for_emotion(self, emotion):
        """Adjust voice settings based on detected emotion"""
        if emotion in self.emotion_voice_mapping:
            config = self.emotion_voice_mapping[emotion]
            self.set_npc_voice(config["voice"], config["speed"], config["pitch"])
            print(f"Adjusted voice for emotion: {emotion}")
        else:
            print(f"Unknown emotion: {emotion}, using default voice settings")
            
    def start_listening(self):
        """Start listening for speech input"""
        self.is_listening = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._process_audio_queue, daemon=True).start()
        
    def stop_listening(self):
        """Stop listening for speech input"""
        self.is_listening = False
        
    def _listen_loop(self):
        """Background thread for continuous speech recognition"""
        print("Starting speech recognition loop...")
        with sr.Microphone() as source:
            print("Microphone initialized")
            self.recognizer.adjust_for_ambient_noise(source)
            print("Ambient noise adjusted")
            while self.is_listening:
                try:
                    print("Listening for speech...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    print("Audio captured, adding to queue")
                    self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"Error in speech recognition: {e}")
                    
    async def process_speech(self, audio_data):
        """Process speech input and get response from OpenAI"""
        try:
            # Convert audio to text
            print("Converting speech to text...")
            text = self.recognizer.recognize_google(audio_data)
            if not text:
                print("No speech detected")
                return None, None
            print(f"Recognized text: {text}")
            
            # Get response from OpenAI
            print("Getting OpenAI response...")
            response = await self._get_openai_response(text)
            if not response:
                print("No response from OpenAI")
                return None, None
            print(f"OpenAI response: {response}")
            
            # Convert response to speech
            print("Converting response to speech...")
            await self._text_to_speech(response)
            print("Speech conversion complete")
            
            return text, response
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio")
            return None, None
        except sr.RequestError as e:
            print(f"Could not request results from speech recognition service: {e}")
            return None, None
        except Exception as e:
            print(f"Error processing speech: {e}")
            return None, None
            
    async def _get_openai_response(self, text):
        """Get response from OpenAI API with emotion detection"""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an NPC in a game. Respond naturally and include an emotion tag at the start of your response in the format [EMOTION:emotion_name]. Available emotions: happy, sad, angry, excited, calm, friendly, authoritative."},
                    {"role": "user", "content": text}
                ],
                stream=True
            )
            
            full_response = ""
            emotion = None
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Check for emotion tag at the start
                    if not emotion and full_response.startswith("[EMOTION:"):
                        end_tag = full_response.find("]")
                        if end_tag != -1:
                            emotion = full_response[9:end_tag].lower()
                            full_response = full_response[end_tag + 1:].strip()
                            
            if emotion:
                self.adjust_voice_for_emotion(emotion)
                
            return full_response
        except Exception as e:
            print(f"Error getting OpenAI response: {e}")
            return None
            
    async def _text_to_speech(self, text):
        """Convert text to speech using OpenAI's TTS API"""
        if not text:
            return
            
        try:
            self.is_speaking = True
            
            # Get voice settings
            voice_settings = self.voice_settings[self.current_npc_voice]
            
            # Generate speech
            client = openai.OpenAI()
            response = client.audio.speech.create(
                model="tts-1",
                voice=self.current_npc_voice,
                input=text,
                speed=voice_settings["speed"]
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
                
            # Play the audio
            data, samplerate = sf.read(temp_file_path)
            sd.play(data, samplerate)
            sd.wait()
            
            # Clean up
            os.unlink(temp_file_path)
            self.is_speaking = False
            
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            self.is_speaking = False
            
    def interrupt_speech(self):
        """Interrupt current speech output and clear any pending audio"""
        if self.is_speaking:
            try:
                sd.stop()
                self.is_speaking = False
                # Clear any pending audio in the queue
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        break
                print("Speech interrupted and queue cleared")
            except Exception as e:
                print(f"Error during speech interruption: {e}")
                self.is_speaking = False

    def is_currently_speaking(self):
        """Check if the system is currently speaking"""
        return self.is_speaking

    def _process_audio_queue(self):
        """Process audio from the queue"""
        print("Starting audio queue processing...")
        while self.is_listening:
            try:
                if not self.audio_queue.empty() and not self.is_speaking:
                    print("Processing audio from queue...")
                    audio = self.audio_queue.get()
                    # Clear any remaining audio in queue to prevent buildup
                    while not self.audio_queue.empty():
                        try:
                            self.audio_queue.get_nowait()
                        except queue.Empty:
                            break
                    asyncio.run(self.process_speech(audio))
            except Exception as e:
                print(f"Error processing audio queue: {e}")
                # Ensure we don't get stuck in an error state
                self.is_speaking = False
            time.sleep(0.1)  # Small delay to prevent CPU overuse 