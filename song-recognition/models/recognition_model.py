"""
Modelo para gerenciar dados de reconhecimento de músicas
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class RecognitionModel:
    def __init__(self, data_file='data/recognitions.json'):
        self.data_file = data_file
        self._ensure_data_directory()
        self._ensure_data_file()
    
    def _ensure_data_directory(self):
        """Garante que o diretório de dados existe"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def _ensure_data_file(self):
        """Garante que o arquivo de dados existe"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def save_recognition(self, recognition_data: Dict) -> str:
        """Salva resultado de reconhecimento"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recognitions = json.load(f)
            
            recognition_id = f"recog_{int(datetime.now().timestamp())}"
            recognition_data['id'] = recognition_id
            recognition_data['created_at'] = datetime.now().isoformat()
            
            recognitions.append(recognition_data)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(recognitions, f, ensure_ascii=False, indent=2)
            
            return recognition_id
        except Exception as e:
            raise Exception(f"Erro ao salvar reconhecimento: {str(e)}")
    
    def get_by_id(self, recognition_id: str) -> Optional[Dict]:
        """Obtém um reconhecimento específico"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recognitions = json.load(f)
            
            for recognition in recognitions:
                if recognition.get('id') == recognition_id:
                    return recognition
            
            return None
        except Exception as e:
            raise Exception(f"Erro ao obter reconhecimento: {str(e)}")
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Obtém histórico de reconhecimentos"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recognitions = json.load(f)
            
            # Ordenar por data de criação (mais recentes primeiro)
            sorted_recognitions = sorted(
                recognitions, 
                key=lambda x: x.get('created_at', ''), 
                reverse=True
            )
            
            return sorted_recognitions[:limit]
        except Exception as e:
            raise Exception(f"Erro ao obter histórico: {str(e)}")
    
    def get_successful_recognitions(self, limit: int = 50) -> List[Dict]:
        """Obtém apenas reconhecimentos bem-sucedidos"""
        try:
            history = self.get_history(limit * 2)  # Buscar mais para filtrar
            successful = [r for r in history if r.get('success', False)]
            return successful[:limit]
        except Exception as e:
            raise Exception(f"Erro ao obter reconhecimentos bem-sucedidos: {str(e)}")
    
    def delete_recognition(self, recognition_id: str) -> bool:
        """Deleta um reconhecimento"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recognitions = json.load(f)
            
            recognitions = [r for r in recognitions if r.get('id') != recognition_id]
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(recognitions, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            raise Exception(f"Erro ao deletar reconhecimento: {str(e)}")
