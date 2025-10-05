"""
Serviço para processamento de áudio
"""
import os
import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.utils import which
import tempfile
import threading
import time
from datetime import datetime

class AudioService:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.sample_rate = 44100
        self.channels = 1  # Mono
        self.temp_dir = 'temp_audio'
        self.ensure_temp_directory()
    
    def ensure_temp_directory(self):
        """Garante que o diretório temporário existe"""
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def record_audio(self, duration=10):
        """Grava áudio por um período específico"""
        try:
            import pyaudio
            
            # Configuração do PyAudio
            chunk = 1024
            format = pyaudio.paInt16
            
            p = pyaudio.PyAudio()
            
            # Abrir stream
            stream = p.open(
                format=format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            self.recording = True
            frames = []
            
            print(f"Iniciando gravação por {duration} segundos...")
            
            for i in range(0, int(self.sample_rate / chunk * duration)):
                if not self.recording:
                    break
                data = stream.read(chunk)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Salvar áudio gravado
            audio_path = self.save_recorded_audio(frames)
            return audio_path
            
        except ImportError:
            # Fallback para quando PyAudio não estiver disponível
            print("PyAudio não disponível. Usando gravação simulada...")
            return self.create_test_audio()
        except Exception as e:
            print(f"Erro na gravação: {str(e)}")
            return self.create_test_audio()
    
    def save_recorded_audio(self, frames):
        """Salva frames de áudio em arquivo"""
        try:
            import pyaudio
            import wave
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            filepath = os.path.join(self.temp_dir, filename)
            
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return filepath
        except Exception as e:
            print(f"Erro ao salvar áudio: {str(e)}")
            return None
    
    def create_test_audio(self):
        """Cria um arquivo de áudio de teste quando gravação real não está disponível"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_audio_{timestamp}.wav"
            filepath = os.path.join(self.temp_dir, filename)
            
            # Gerar um tom de teste
            duration = 5  # segundos
            frequency = 440  # Hz (nota A)
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            wave = 0.3 * np.sin(2 * np.pi * frequency * t)
            
            sf.write(filepath, wave, self.sample_rate)
            return filepath
        except Exception as e:
            print(f"Erro ao criar áudio de teste: {str(e)}")
            return None
    
    def extract_features(self, audio_path):
        """Extrai características do áudio para reconhecimento"""
        try:
            # Carregar áudio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extrair características
            features = {}
            
            # MFCC (Mel-frequency cepstral coefficients)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc'] = mfccs.tolist()
            
            # Spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            features['spectral_centroid'] = spectral_centroids.tolist()
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            features['spectral_rolloff'] = spectral_rolloff.tolist()
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)
            features['zcr'] = zcr.tolist()
            
            # Chroma
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            features['chroma'] = chroma.tolist()
            
            # Tempo
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = float(tempo)
            
            # Duração
            features['duration'] = len(y) / sr
            
            return features
            
        except Exception as e:
            print(f"Erro na extração de características: {str(e)}")
            return {}
    
    def save_temp_audio(self, audio_file):
        """Salva arquivo de áudio temporário"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temp_audio_{timestamp}.wav"
            filepath = os.path.join(self.temp_dir, filename)
            
            audio_file.save(filepath)
            return filepath
        except Exception as e:
            raise Exception(f"Erro ao salvar arquivo temporário: {str(e)}")
    
    def cleanup_temp_file(self, filepath):
        """Remove arquivo temporário"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Erro ao remover arquivo temporário: {str(e)}")
    
    def get_latest_recording_path(self):
        """Retorna o caminho da gravação mais recente"""
        try:
            if not os.path.exists(self.temp_dir):
                return None
            
            files = [f for f in os.listdir(self.temp_dir) if f.startswith('recording_')]
            if not files:
                return None
            
            latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(self.temp_dir, x)))
            return os.path.join(self.temp_dir, latest_file)
        except Exception as e:
            print(f"Erro ao obter gravação mais recente: {str(e)}")
            return None
    
    def convert_to_wav(self, input_path, output_path=None):
        """Converte arquivo de áudio para WAV"""
        try:
            if output_path is None:
                output_path = input_path.replace('.mp3', '.wav').replace('.m4a', '.wav')
            
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav")
            return output_path
        except Exception as e:
            print(f"Erro na conversão para WAV: {str(e)}")
            return input_path
