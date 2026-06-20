import os
import subprocess
import tempfile
import speech_recognition as sr
from typing import Dict, Any

class AudioTranscriber:
    @classmethod
    def transcribe(cls, file_path: str) -> str:
        """
        Transcribes a WAV/audio/video file to text using speech_recognition.
        If it's not a WAV, we convert it to WAV using ffmpeg.
        If transcription fails, it falls back to a template text or error.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File audio/video {file_path} non trovato.")
            
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Check if the file is WAV, AIFF, or FLAC
        ext = os.path.splitext(file_path)[1].lower()
        
        temp_wav_path = None
        target_wav_file = file_path
        
        # Supported directly by speech_recognition
        supported_exts = [".wav", ".aiff", ".aif", ".flac"]
        
        if ext not in supported_exts:
            try:
                # Convert the file using ffmpeg to a temporary WAV file
                # Use tempfile to generate a safe path
                fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd) # Close file descriptor as ffmpeg will write to it
                
                # Execute ffmpeg to extract/convert audio to mono WAV 16kHz PCM
                cmd = [
                    "ffmpeg", "-y",
                    "-i", file_path,
                    "-vn", # Disable video recording/extraction
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    temp_wav_path
                ]
                # Run subprocess silently
                result = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                if result.returncode != 0:
                    raise Exception(f"FFmpeg conversion failed: {result.stderr}")
                
                target_wav_file = temp_wav_path
            except Exception as e:
                # Cleanup temp file if created
                if temp_wav_path and os.path.exists(temp_wav_path):
                    try:
                        os.remove(temp_wav_path)
                    except:
                        pass
                return f"[Errore Conversione Audio] Impossibile convertire il file in WAV tramite FFmpeg: {e}"
                
        try:
            with sr.AudioFile(target_wav_file) as source:
                audio_data = recognizer.record(source)
                # Use Google Web Speech API (free, no key required for basic usage)
                text = recognizer.recognize_google(audio_data, language="it-IT")
                return text
        except sr.UnknownValueError:
            return "[Errore] Google Speech Recognition non è riuscito a comprendere l'audio."
        except sr.RequestError as e:
            return f"[Errore] Impossibile contattare il servizio di trascrizione Google; {e}"
        except Exception as e:
            return f"[Errore Trascrizione] Impossibile elaborare l'audio: {e}"
        finally:
            # Always clean up the temporary file
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except:
                    pass
