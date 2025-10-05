"""
Controlador para gerenciar gravação e processamento de áudio
"""
import os
import threading
import time
from datetime import datetime
from models.audio_model import AudioModel
from services.audio_service import AudioService

class AudioController:
    def __init__(self):
        self.audio_service = AudioService()
        self.audio_model = AudioModel()
        self.is_recording = False
        self.recording_thread = None
        self.recording_start_time = None
        
    def start_recording(self):
        """Inicia a gravação de áudio"""
        if self.is_recording:
            return {'error': 'Gravação já está em andamento'}
        
        try:
            self.is_recording = True
            self.recording_start_time = datetime.now()
            
            # Iniciar gravação em thread separada
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()
            
            return {
                'status': 'success',
                'message': 'Gravação iniciada',
                'start_time': self.recording_start_time.isoformat()
            }
        except Exception as e:
            self.is_recording = False
            return {'error': f'Erro ao iniciar gravação: {str(e)}'}
    
    def stop_recording(self):
        """Para a gravação de áudio"""
        if not self.is_recording:
            return {'error': 'Nenhuma gravação em andamento'}
        
        try:
            self.is_recording = False
            
            # Aguardar thread de gravação terminar
            if self.recording_thread:
                self.recording_thread.join(timeout=5)
            
            # Processar áudio gravado
            recording_duration = (datetime.now() - self.recording_start_time).total_seconds()
            
            # Salvar informações da gravação
            audio_info = {
                'duration': recording_duration,
                'start_time': self.recording_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'file_path': self.audio_service.get_latest_recording_path()
            }
            
            return {
                'status': 'success',
                'message': 'Gravação finalizada',
                'audio_info': audio_info
            }
        except Exception as e:
            return {'error': f'Erro ao parar gravação: {str(e)}'}
    
    def _record_audio(self):
        """Método interno para gravação de áudio"""
        try:
            self.audio_service.record_audio(self.is_recording)
        except Exception as e:
            print(f"Erro na gravação: {str(e)}")
            self.is_recording = False
    
    def get_recording_status(self):
        """Retorna status atual da gravação"""
        return {
            'is_recording': self.is_recording,
            'start_time': self.recording_start_time.isoformat() if self.recording_start_time else None
        }
