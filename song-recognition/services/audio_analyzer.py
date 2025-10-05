"""
Analisador avançado de características de áudio
Implementa análise musical local sem APIs externas
"""
import numpy as np
import librosa
from typing import Dict, Optional, List
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import json
import os

class AudioAnalyzer:
    def __init__(self):
        self.sample_rate = 22050
        self.hop_length = 512
        self.n_mfcc = 13
        
        # Carregar modelos pré-treinados se existirem
        self.genre_classifier = self._load_genre_classifier()
        self.key_detector = self._load_key_detector()
    
    def analyze_audio(self, audio_path: str) -> Optional[Dict]:
        """Análise completa de características musicais"""
        try:
            # Carregar áudio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            if len(y) == 0:
                return None
            
            # Análises básicas
            tempo = self._extract_tempo(y, sr)
            key, mode = self._extract_key_and_mode(y, sr)
            energy = self._extract_energy(y)
            valence = self._extract_valence(y, sr)
            danceability = self._extract_danceability(y, sr)
            
            # Análise espectral
            spectral_features = self._extract_spectral_features(y, sr)
            
            # Análise rítmica
            rhythmic_features = self._extract_rhythmic_features(y, sr)
            
            # Classificação de gênero
            genre = self._classify_genre(y, sr)
            
            # Análise de instrumentos
            instruments = self._detect_instruments(y, sr)
            
            # Análise de estrutura
            structure = self._analyze_structure(y, sr)
            
            return {
                'tempo': tempo,
                'key': key,
                'mode': mode,
                'energy': energy,
                'valence': valence,
                'danceability': danceability,
                'genre': genre,
                'instruments': instruments,
                'structure': structure,
                'spectral_features': spectral_features,
                'rhythmic_features': rhythmic_features,
                'duration': len(y) / sr
            }
            
        except Exception as e:
            print(f"Erro na análise de áudio: {str(e)}")
            return None
    
    def _extract_tempo(self, y: np.ndarray, sr: int) -> float:
        """Extrai o tempo (BPM) da música"""
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            return float(tempo)
        except:
            return 0.0
    
    def _extract_key_and_mode(self, y: np.ndarray, sr: int) -> tuple:
        """Extrai tonalidade e modo da música"""
        try:
            # Usar chroma para detectar tonalidade
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Calcular perfil de tonalidade
            key_profile = np.mean(chroma, axis=1)
            
            # Nomes das tonalidades (maior)
            major_keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            minor_keys = ['Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm']
            
            # Perfis de tonalidade (simplificados)
            major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])  # C major
            minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])  # A minor
            
            # Calcular correlação com perfis
            major_corr = np.corrcoef(key_profile, major_profile)[0, 1]
            minor_corr = np.corrcoef(key_profile, minor_profile)[0, 1]
            
            if major_corr > minor_corr:
                key_idx = np.argmax(key_profile)
                return major_keys[key_idx], 'Major'
            else:
                key_idx = np.argmax(key_profile)
                return minor_keys[key_idx], 'Minor'
                
        except:
            return 'Desconhecida', 'Desconhecido'
    
    def _extract_energy(self, y: np.ndarray) -> float:
        """Extrai energia da música"""
        try:
            # RMS (Root Mean Square) como medida de energia
            rms = librosa.feature.rms(y=y)[0]
            return float(np.mean(rms))
        except:
            return 0.0
    
    def _extract_valence(self, y: np.ndarray, sr: int) -> float:
        """Extrai valência (positividade) da música"""
        try:
            # Usar características espectrais para estimar valência
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # Valência baseada em características espectrais
            # Músicas mais "brilhantes" tendem a ser mais positivas
            brightness = np.mean(spectral_centroids) / (sr / 2)
            rolloff_ratio = np.mean(spectral_rolloff) / (sr / 2)
            
            valence = (brightness + rolloff_ratio) / 2
            return float(np.clip(valence, 0, 1))
        except:
            return 0.5
    
    def _extract_danceability(self, y: np.ndarray, sr: int) -> float:
        """Extrai dançabilidade da música"""
        try:
            # Fatores que influenciam dançabilidade
            tempo = self._extract_tempo(y, sr)
            energy = self._extract_energy(y)
            
            # Regularidade rítmica
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            if len(onset_frames) > 1:
                onset_intervals = np.diff(onset_frames)
                rhythm_regularity = 1.0 / (1.0 + np.std(onset_intervals))
            else:
                rhythm_regularity = 0.0
            
            # Tempo ideal para dança (100-130 BPM)
            tempo_score = 1.0 - abs(tempo - 115) / 115 if tempo > 0 else 0.0
            tempo_score = max(0, min(1, tempo_score))
            
            # Combinação de fatores
            danceability = (energy * 0.4 + rhythm_regularity * 0.3 + tempo_score * 0.3)
            return float(np.clip(danceability, 0, 1))
        except:
            return 0.5
    
    def _extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extrai características espectrais"""
        try:
            # MFCCs
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
            
            # Centróide espectral
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            
            # Rolloff espectral
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            return {
                'mfcc_mean': np.mean(mfccs, axis=1).tolist(),
                'mfcc_std': np.std(mfccs, axis=1).tolist(),
                'spectral_centroid_mean': float(np.mean(spectral_centroids)),
                'spectral_centroid_std': float(np.std(spectral_centroids)),
                'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
                'spectral_rolloff_std': float(np.std(spectral_rolloff)),
                'zcr_mean': float(np.mean(zcr)),
                'zcr_std': float(np.std(zcr))
            }
        except:
            return {}
    
    def _extract_rhythmic_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extrai características rítmicas"""
        try:
            # Onset strength
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Tempo e beats
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Regularidade rítmica
            if len(beats) > 2:
                beat_intervals = np.diff(beats)
                rhythm_regularity = 1.0 / (1.0 + np.std(beat_intervals))
            else:
                rhythm_regularity = 0.0
            
            return {
                'onset_strength_mean': float(np.mean(onset_strength)),
                'onset_strength_std': float(np.std(onset_strength)),
                'rhythm_regularity': float(rhythm_regularity),
                'beat_count': len(beats),
                'tempo': float(tempo)
            }
        except:
            return {}
    
    def _classify_genre(self, y: np.ndarray, sr: int) -> str:
        """Classifica gênero musical"""
        try:
            if self.genre_classifier:
                # Usar classificador pré-treinado
                features = self._extract_genre_features(y, sr)
                genre = self.genre_classifier.predict([features])[0]
                return genre
            else:
                # Classificação baseada em regras
                return self._rule_based_genre_classification(y, sr)
        except:
            return 'Desconhecido'
    
    def _extract_genre_features(self, y: np.ndarray, sr: int) -> List[float]:
        """Extrai características para classificação de gênero"""
        try:
            # Características espectrais
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            # Características rítmicas
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Combinar características
            features = [
                np.mean(mfccs, axis=1).mean(),
                np.std(mfccs, axis=1).mean(),
                np.mean(spectral_centroids),
                np.std(spectral_centroids),
                np.mean(spectral_rolloff),
                np.std(spectral_rolloff),
                np.mean(zcr),
                np.std(zcr),
                tempo,
                np.mean(onset_strength),
                np.std(onset_strength)
            ]
            
            return features
        except:
            return [0.0] * 11
    
    def _rule_based_genre_classification(self, y: np.ndarray, sr: int) -> str:
        """Classificação de gênero baseada em regras"""
        try:
            tempo = self._extract_tempo(y, sr)
            energy = self._extract_energy(y)
            valence = self._extract_valence(y, sr)
            
            # Regras simples para classificação
            if tempo > 140 and energy > 0.7:
                return 'Electronic/Dance'
            elif tempo > 120 and energy > 0.6:
                return 'Pop/Rock'
            elif tempo < 80 and energy < 0.4:
                return 'Classical/Ambient'
            elif tempo > 100 and valence > 0.6:
                return 'Pop'
            elif tempo > 90 and energy > 0.5:
                return 'Rock'
            else:
                return 'Unknown'
        except:
            return 'Desconhecido'
    
    def _detect_instruments(self, y: np.ndarray, sr: int) -> List[str]:
        """Detecta instrumentos presentes na música"""
        try:
            instruments = []
            
            # Análise de frequências para detectar instrumentos
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            # Detecção de baixo (frequências baixas)
            low_freq_energy = np.mean(spectral_centroids[spectral_centroids < sr * 0.1])
            if low_freq_energy > 0.1:
                instruments.append('Bass')
            
            # Detecção de percussão (alta energia em frequências médias)
            mid_freq_energy = np.mean(spectral_centroids[(spectral_centroids > sr * 0.1) & 
                                                         (spectral_centroids < sr * 0.3)])
            if mid_freq_energy > 0.2:
                instruments.append('Drums')
            
            # Detecção de vocais (frequências médias-alta)
            vocal_freq_energy = np.mean(spectral_centroids[spectral_centroids > sr * 0.3])
            if vocal_freq_energy > 0.15:
                instruments.append('Vocals')
            
            # Detecção de guitarra (características específicas)
            if np.mean(spectral_bandwidth) > 1000:
                instruments.append('Guitar')
            
            return instruments if instruments else ['Unknown']
        except:
            return ['Desconhecido']
    
    def _analyze_structure(self, y: np.ndarray, sr: int) -> Dict:
        """Analisa estrutura da música"""
        try:
            # Segmentação automática
            segments = librosa.segment.agglomerative(y, k=8)
            
            # Análise de repetição
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            similarity_matrix = np.corrcoef(chroma.T)
            
            # Encontrar seções repetidas
            repeated_sections = self._find_repeated_sections(similarity_matrix)
            
            return {
                'segments': len(segments),
                'repeated_sections': repeated_sections,
                'structure_complexity': float(np.std(similarity_matrix))
            }
        except:
            return {'segments': 0, 'repeated_sections': 0, 'structure_complexity': 0.0}
    
    def _find_repeated_sections(self, similarity_matrix: np.ndarray) -> int:
        """Encontra seções repetidas na música"""
        try:
            # Usar threshold para detectar similaridade
            threshold = 0.7
            similar_pairs = np.sum(similarity_matrix > threshold) - len(similarity_matrix)
            return int(similar_pairs / 2)  # Dividir por 2 para evitar contar duas vezes
        except:
            return 0
    
    def _load_genre_classifier(self):
        """Carrega classificador de gênero pré-treinado"""
        try:
            model_path = 'models/genre_classifier.pkl'
            if os.path.exists(model_path):
                import joblib
                return joblib.load(model_path)
        except:
            pass
        return None
    
    def _load_key_detector(self):
        """Carrega detector de tonalidade pré-treinado"""
        try:
            model_path = 'models/key_detector.pkl'
            if os.path.exists(model_path):
                import joblib
                return joblib.load(model_path)
        except:
            pass
        return None
    
    def save_analysis(self, audio_path: str, analysis: Dict, output_path: str = None):
        """Salva análise em arquivo JSON"""
        try:
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(audio_path))[0]
                output_path = f'analysis/{base_name}_analysis.json'
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            print(f"Análise salva em: {output_path}")
        except Exception as e:
            print(f"Erro ao salvar análise: {str(e)}")
