"""
Controlador para gerenciar reconhecimento de músicas
"""
from services.recognition_service import RecognitionService
from services.audio_service import AudioService
from models.recognition_model import RecognitionModel
import os

class RecognitionController:
    def __init__(self):
        self.recognition_service = RecognitionService()
        self.audio_service = AudioService()
        self.recognition_model = RecognitionModel()
    
    def recognize_song(self, audio_file):
        """Reconhece uma música a partir de um arquivo de áudio"""
        try:
            # Salvar arquivo temporariamente
            temp_path = self.audio_service.save_temp_audio(audio_file)
            
            # Processar áudio para extrair características
            audio_features = self.audio_service.extract_features(temp_path)
            
            # Tentar reconhecimento usando múltiplos serviços
            recognition_result = self.recognition_service.recognize(audio_features, temp_path)
            
            # Salvar resultado no modelo
            if recognition_result.get('success'):
                self.recognition_model.save_recognition(recognition_result)
            
            # Limpar arquivo temporário
            self.audio_service.cleanup_temp_file(temp_path)
            
            return recognition_result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro no reconhecimento: {str(e)}',
                'message': 'Não foi possível reconhecer a música'
            }
    
    def get_recognition_history(self):
        """Retorna histórico de reconhecimentos"""
        try:
            return self.recognition_model.get_history()
        except Exception as e:
            return {'error': f'Erro ao obter histórico: {str(e)}'}
    
    def get_recognition_by_id(self, recognition_id):
        """Retorna um reconhecimento específico por ID"""
        try:
            return self.recognition_model.get_by_id(recognition_id)
        except Exception as e:
            return {'error': f'Erro ao obter reconhecimento: {str(e)}'}
