"""
Serviço para reconhecimento de músicas usando sistema local
"""
import os
import json
from typing import Dict, Optional
from services.audio_fingerprint import AudioFingerprint
from services.audio_analyzer import AudioAnalyzer

class RecognitionService:
    def __init__(self):
        self.fingerprint_system = AudioFingerprint()
        self.audio_analyzer = AudioAnalyzer()
    
    def recognize(self, audio_features: Dict, audio_path: str) -> Dict:
        """Reconhece música usando sistema local de fingerprinting"""
        result = {
            'success': False,
            'service_used': 'Sistema Local',
            'song_info': None,
            'confidence': 0,
            'message': 'Não foi possível reconhecer a música'
        }
        
        try:
            # Tentar reconhecimento por fingerprinting
            fingerprint_result = self._recognize_by_fingerprint(audio_path)
            if fingerprint_result.get('success'):
                return fingerprint_result
            
            # Fallback: análise de características
            analysis_result = self._analyze_characteristics(audio_features, audio_path)
            if analysis_result.get('success'):
                return analysis_result
            
            # Último recurso: análise básica
            basic_result = self._basic_analysis(audio_features)
            return basic_result
            
        except Exception as e:
            result['message'] = f'Erro no reconhecimento: {str(e)}'
            return result
    
    def _recognize_by_fingerprint(self, audio_path: str) -> Dict:
        """Reconhece música usando sistema de fingerprinting local"""
        try:
            match = self.fingerprint_system.find_matching_song(audio_path)
            
            if match:
                return {
                    'success': True,
                    'service_used': 'Fingerprinting Local',
                    'song_info': {
                        'title': match['title'],
                        'artist': match['artist'],
                        'album': match.get('album', ''),
                        'duration': match.get('duration', 0),
                        'created_at': match.get('created_at', '')
                    },
                    'confidence': match['confidence'],
                    'message': 'Música reconhecida pelo banco local!'
                }
            
            return {'success': False, 'message': 'Música não encontrada no banco local'}
            
        except Exception as e:
            print(f"Erro no fingerprinting: {str(e)}")
            return {'success': False, 'message': f'Erro no fingerprinting: {str(e)}'}
    
    def _analyze_characteristics(self, audio_features: Dict, audio_path: str) -> Dict:
        """Analisa características do áudio para reconhecimento"""
        try:
            # Análise avançada de características
            analysis = self.audio_analyzer.analyze_audio(audio_path)
            
            if analysis:
                return {
                    'success': True,
                    'service_used': 'Análise de Características',
                    'song_info': {
                        'title': 'Música Analisada',
                        'artist': 'Artista Desconhecido',
                        'tempo': analysis.get('tempo', 0),
                        'key': analysis.get('key', 'Desconhecida'),
                        'mode': analysis.get('mode', 'Desconhecido'),
                        'energy': analysis.get('energy', 0),
                        'valence': analysis.get('valence', 0),
                        'danceability': analysis.get('danceability', 0),
                        'estimated_genre': analysis.get('genre', 'Desconhecido')
                    },
                    'confidence': 0.6,
                    'message': 'Análise de características concluída'
                }
            
            return {'success': False, 'message': 'Não foi possível analisar características'}
            
        except Exception as e:
            print(f"Erro na análise de características: {str(e)}")
            return {'success': False, 'message': f'Erro na análise: {str(e)}'}
    
    def _basic_analysis(self, audio_features: Dict) -> Dict:
        """Análise básica baseada em características do áudio"""
        try:
            if not audio_features:
                return {'success': False, 'message': 'Características de áudio não disponíveis'}
            
            # Análise básica baseada em tempo e características
            tempo = audio_features.get('tempo', 0)
            duration = audio_features.get('duration', 0)
            
            # Classificação básica por tempo
            tempo_category = self._classify_tempo(tempo)
            
            # Análise de energia espectral
            mfcc = audio_features.get('mfcc', [])
            spectral_centroid = audio_features.get('spectral_centroid', [])
            
            genre_guess = self._guess_genre_by_features(tempo, mfcc, spectral_centroid)
            
            return {
                'success': True,
                'service_used': 'Análise Local',
                'song_info': {
                    'title': 'Música não identificada',
                    'artist': 'Artista desconhecido',
                    'album': '',
                    'tempo': tempo,
                    'tempo_category': tempo_category,
                    'duration': duration,
                    'estimated_genre': genre_guess,
                    'analysis': 'Análise baseada em características locais do áudio'
                },
                'confidence': 0.3,  # Baixa confiança para análise local
                'message': 'Não foi possível identificar a música, mas foram extraídas algumas características'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Erro na análise básica: {str(e)}'}
    
    def _classify_tempo(self, tempo: float) -> str:
        """Classifica o tempo da música"""
        if tempo < 60:
            return "Muito lento"
        elif tempo < 90:
            return "Lento"
        elif tempo < 120:
            return "Moderado"
        elif tempo < 140:
            return "Allegro"
        elif tempo < 180:
            return "Presto"
        else:
            return "Muito rápido"
    
    def _guess_genre_by_features(self, tempo: float, mfcc: list, spectral_centroid: list) -> str:
        """Tenta adivinhar o gênero baseado nas características"""
        try:
            # Análise muito básica
            if tempo > 140:
                return "Dance/Electronic"
            elif tempo > 120:
                return "Pop/Rock"
            elif tempo > 90:
                return "Ballad/Slow"
            else:
                return "Classical/Ambient"
        except:
            return "Desconhecido"
