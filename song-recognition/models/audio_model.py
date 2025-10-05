"""
Modelo para gerenciar dados de áudio
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class AudioModel:
    def __init__(self, data_file='data/audio_recordings.json'):
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
    
    def save_recording(self, recording_data: Dict) -> str:
        """Salva informações de uma gravação"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recordings = json.load(f)
            
            recording_id = f"rec_{int(datetime.now().timestamp())}"
            recording_data['id'] = recording_id
            recording_data['created_at'] = datetime.now().isoformat()
            
            recordings.append(recording_data)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(recordings, f, ensure_ascii=False, indent=2)
            
            return recording_id
        except Exception as e:
            raise Exception(f"Erro ao salvar gravação: {str(e)}")
    
    def get_recording(self, recording_id: str) -> Optional[Dict]:
        """Obtém uma gravação específica"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recordings = json.load(f)
            
            for recording in recordings:
                if recording.get('id') == recording_id:
                    return recording
            
            return None
        except Exception as e:
            raise Exception(f"Erro ao obter gravação: {str(e)}")
    
    def get_all_recordings(self) -> List[Dict]:
        """Obtém todas as gravações"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recordings = json.load(f)
            
            return sorted(recordings, key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            raise Exception(f"Erro ao obter gravações: {str(e)}")
    
    def delete_recording(self, recording_id: str) -> bool:
        """Deleta uma gravação"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                recordings = json.load(f)
            
            recordings = [r for r in recordings if r.get('id') != recording_id]
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(recordings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            raise Exception(f"Erro ao deletar gravação: {str(e)}")
