"""
Sistema de fingerprinting de áudio local
Implementa técnicas de reconhecimento de música sem APIs externas
"""
import numpy as np
import librosa
import hashlib
import sqlite3
import json
from typing import List, Dict, Tuple, Optional
from scipy.signal import find_peaks
from sklearn.metrics.pairwise import cosine_similarity
import os

class AudioFingerprint:
    def __init__(self, db_path='data/audio_fingerprints.db'):
        self.db_path = db_path
        self.sample_rate = 22050  # Taxa de amostragem reduzida para eficiência
        self.window_size = 4096
        self.overlap = 0.5
        self.hop_length = int(self.window_size * (1 - self.overlap))
        
        # Parâmetros para fingerprinting
        self.target_zone_size = 15
        self.fanout = 15
        self.min_amplitude = 0.1
        
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados SQLite para fingerprints"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de músicas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT,
                    file_path TEXT,
                    duration REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de fingerprints
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fingerprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id INTEGER,
                    hash_value TEXT NOT NULL,
                    offset INTEGER NOT NULL,
                    FOREIGN KEY (song_id) REFERENCES songs (id)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON fingerprints (hash_value)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_song_id ON fingerprints (song_id)')
            
            conn.commit()
    
    def generate_fingerprint(self, audio_path: str) -> List[Tuple[str, int]]:
        """Gera fingerprint de um arquivo de áudio"""
        try:
            # Carregar áudio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Aplicar pré-processamento
            y = self._preprocess_audio(y)
            
            # Calcular espectrograma
            stft = librosa.stft(y, n_fft=self.window_size, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            
            # Aplicar filtro de frequência
            magnitude = self._apply_frequency_filter(magnitude)
            
            # Encontrar picos espectrais
            peaks = self._find_spectral_peaks(magnitude)
            
            # Gerar hashes dos picos
            hashes = self._generate_hashes(peaks)
            
            return hashes
            
        except Exception as e:
            print(f"Erro ao gerar fingerprint: {str(e)}")
            return []
    
    def _preprocess_audio(self, y: np.ndarray) -> np.ndarray:
        """Pré-processa o sinal de áudio"""
        # Normalizar
        y = librosa.util.normalize(y)
        
        # Aplicar filtro passa-alta para remover ruído de baixa frequência
        y = librosa.effects.preemphasis(y)
        
        return y
    
    def _apply_frequency_filter(self, magnitude: np.ndarray) -> np.ndarray:
        """Aplica filtro de frequência para focar em frequências relevantes"""
        # Focar em frequências de 30Hz a 3000Hz (voz humana e instrumentos)
        freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=self.window_size)
        
        # Criar máscara de frequência
        freq_mask = (freqs >= 30) & (freqs <= 3000)
        
        # Aplicar máscara
        filtered_magnitude = magnitude.copy()
        filtered_magnitude[~freq_mask] = 0
        
        return filtered_magnitude
    
    def _find_spectral_peaks(self, magnitude: np.ndarray) -> List[Tuple[int, int, float]]:
        """Encontra picos no espectrograma"""
        peaks = []
        
        for time_idx in range(magnitude.shape[1]):
            # Encontrar picos em cada frame de tempo
            frame = magnitude[:, time_idx]
            
            # Encontrar picos locais
            peak_indices, properties = find_peaks(
                frame, 
                height=self.min_amplitude,
                distance=10,  # Distância mínima entre picos
                prominence=0.1
            )
            
            # Armazenar picos encontrados
            for peak_idx in peak_indices:
                if frame[peak_idx] > self.min_amplitude:
                    peaks.append((peak_idx, time_idx, frame[peak_idx]))
        
        return peaks
    
    def _generate_hashes(self, peaks: List[Tuple[int, int, float]]) -> List[Tuple[str, int]]:
        """Gera hashes a partir dos picos espectrais"""
        hashes = []
        
        # Ordenar picos por amplitude
        peaks_sorted = sorted(peaks, key=lambda x: x[2], reverse=True)
        
        # Gerar hashes para cada combinação de picos
        for i, (freq1, time1, amp1) in enumerate(peaks_sorted):
            for j in range(i + 1, min(i + self.fanout, len(peaks_sorted))):
                freq2, time2, amp2 = peaks_sorted[j]
                
                # Calcular diferenças
                freq_diff = freq2 - freq1
                time_diff = time2 - time1
                
                # Criar hash da combinação
                hash_input = f"{freq1}:{freq_diff}:{time_diff}"
                hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:16]
                
                hashes.append((hash_value, time1))
        
        return hashes
    
    def add_song_to_database(self, title: str, artist: str, audio_path: str, 
                           album: str = None) -> int:
        """Adiciona uma música ao banco de dados"""
        try:
            # Gerar fingerprint
            hashes = self.generate_fingerprint(audio_path)
            
            if not hashes:
                raise Exception("Não foi possível gerar fingerprint")
            
            # Calcular duração
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(y) / sr
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Inserir música
                cursor.execute('''
                    INSERT INTO songs (title, artist, album, file_path, duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, artist, album, audio_path, duration))
                
                song_id = cursor.lastrowid
                
                # Inserir fingerprints
                fingerprint_data = [(song_id, hash_val, offset) for hash_val, offset in hashes]
                cursor.executemany('''
                    INSERT INTO fingerprints (song_id, hash_value, offset)
                    VALUES (?, ?, ?)
                ''', fingerprint_data)
                
                conn.commit()
                
                print(f"✅ Música '{title}' por '{artist}' adicionada com {len(hashes)} fingerprints")
                return song_id
                
        except Exception as e:
            print(f"❌ Erro ao adicionar música: {str(e)}")
            return None
    
    def find_matching_song(self, audio_path: str, threshold: float = 0.3) -> Optional[Dict]:
        """Encontra música correspondente no banco de dados"""
        try:
            # Gerar fingerprint da música de entrada
            query_hashes = self.generate_fingerprint(audio_path)
            
            if not query_hashes:
                return None
            
            # Buscar correspondências no banco
            matches = self._find_hash_matches(query_hashes)
            
            if not matches:
                return None
            
            # Calcular scores de correspondência
            song_scores = self._calculate_match_scores(matches)
            
            # Encontrar melhor correspondência
            best_match = max(song_scores.items(), key=lambda x: x[1])
            
            if best_match[1] >= threshold:
                song_id, score = best_match
                song_info = self._get_song_info(song_id)
                song_info['confidence'] = score
                return song_info
            
            return None
            
        except Exception as e:
            print(f"Erro ao encontrar música correspondente: {str(e)}")
            return None
    
    def _find_hash_matches(self, query_hashes: List[Tuple[str, int]]) -> Dict[int, List[Tuple[int, int]]]:
        """Encontra correspondências de hashes no banco de dados"""
        matches = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for hash_val, offset in query_hashes:
                cursor.execute('''
                    SELECT song_id, offset FROM fingerprints 
                    WHERE hash_value = ?
                ''', (hash_val,))
                
                results = cursor.fetchall()
                
                for song_id, db_offset in results:
                    if song_id not in matches:
                        matches[song_id] = []
                    matches[song_id].append((offset, db_offset))
        
        return matches
    
    def _calculate_match_scores(self, matches: Dict[int, List[Tuple[int, int]]]) -> Dict[int, float]:
        """Calcula scores de correspondência baseados em offsets"""
        scores = {}
        
        for song_id, offset_pairs in matches.items():
            if len(offset_pairs) < 3:  # Mínimo de correspondências
                continue
            
            # Calcular diferenças de offset
            offset_diffs = [db_offset - query_offset for query_offset, db_offset in offset_pairs]
            
            # Encontrar offset mais comum (histograma)
            from collections import Counter
            diff_counts = Counter(offset_diffs)
            most_common_diff, count = diff_counts.most_common(1)[0]
            
            # Score baseado na consistência dos offsets
            score = count / len(offset_pairs)
            scores[song_id] = score
        
        return scores
    
    def _get_song_info(self, song_id: int) -> Dict:
        """Obtém informações de uma música pelo ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, artist, album, duration, created_at
                FROM songs WHERE id = ?
            ''', (song_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': song_id,
                    'title': result[0],
                    'artist': result[1],
                    'album': result[2],
                    'duration': result[3],
                    'created_at': result[4]
                }
            return None
    
    def get_database_stats(self) -> Dict:
        """Retorna estatísticas do banco de dados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Contar músicas
            cursor.execute('SELECT COUNT(*) FROM songs')
            song_count = cursor.fetchone()[0]
            
            # Contar fingerprints
            cursor.execute('SELECT COUNT(*) FROM fingerprints')
            fingerprint_count = cursor.fetchone()[0]
            
            # Música com mais fingerprints
            cursor.execute('''
                SELECT s.title, s.artist, COUNT(f.id) as fingerprint_count
                FROM songs s
                LEFT JOIN fingerprints f ON s.id = f.song_id
                GROUP BY s.id
                ORDER BY fingerprint_count DESC
                LIMIT 1
            ''')
            top_song = cursor.fetchone()
            
            return {
                'total_songs': song_count,
                'total_fingerprints': fingerprint_count,
                'avg_fingerprints_per_song': fingerprint_count / song_count if song_count > 0 else 0,
                'top_song': {
                    'title': top_song[0] if top_song else None,
                    'artist': top_song[1] if top_song else None,
                    'fingerprint_count': top_song[2] if top_song else 0
                } if top_song else None
            }
