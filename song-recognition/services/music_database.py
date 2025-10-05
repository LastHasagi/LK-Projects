"""
Sistema de gerenciamento de banco de músicas local
Permite adicionar, remover e gerenciar músicas no banco de dados
"""
import os
import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
from services.audio_fingerprint import AudioFingerprint
from services.audio_analyzer import AudioAnalyzer

class MusicDatabase:
    def __init__(self, db_path='data/music_database.db'):
        self.db_path = db_path
        self.fingerprint_system = AudioFingerprint()
        self.audio_analyzer = AudioAnalyzer()
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados"""
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
                    genre TEXT,
                    year INTEGER,
                    duration REAL,
                    file_path TEXT UNIQUE,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de características musicais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id INTEGER,
                    tempo REAL,
                    key TEXT,
                    mode TEXT,
                    energy REAL,
                    valence REAL,
                    danceability REAL,
                    features_json TEXT,
                    FOREIGN KEY (song_id) REFERENCES songs (id)
                )
            ''')
            
            # Tabela de playlists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de relacionamento playlist-música
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlist_songs (
                    playlist_id INTEGER,
                    song_id INTEGER,
                    position INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (playlist_id, song_id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                    FOREIGN KEY (song_id) REFERENCES songs (id)
                )
            ''')
            
            # Índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs (artist)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_songs_genre ON songs (genre)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_songs_year ON songs (year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_tempo ON audio_features (tempo)')
            
            conn.commit()
    
    def add_song(self, file_path: str, title: str, artist: str, 
                 album: str = None, genre: str = None, year: int = None) -> Optional[int]:
        """Adiciona uma música ao banco de dados"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ Arquivo não encontrado: {file_path}")
                return None
            
            # Verificar se música já existe
            existing = self.get_song_by_path(file_path)
            if existing:
                print(f"⚠️  Música já existe no banco: {title} - {artist}")
                return existing['id']
            
            # Analisar arquivo de áudio
            print(f"🔄 Analisando música: {title} - {artist}")
            
            # Extrair características
            analysis = self.audio_analyzer.analyze_audio(file_path)
            if not analysis:
                print(f"❌ Erro ao analisar música: {file_path}")
                return None
            
            # Gerar fingerprint
            print("🔄 Gerando fingerprint...")
            fingerprint_id = self.fingerprint_system.add_song_to_database(
                title, artist, file_path, album
            )
            
            if not fingerprint_id:
                print(f"❌ Erro ao gerar fingerprint para: {title}")
                return None
            
            # Salvar no banco principal
            file_size = os.path.getsize(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Inserir música
                cursor.execute('''
                    INSERT INTO songs (title, artist, album, genre, year, duration, file_path, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, artist, album, genre, year, analysis['duration'], file_path, file_size))
                
                song_id = cursor.lastrowid
                
                # Inserir características
                cursor.execute('''
                    INSERT INTO audio_features (song_id, tempo, key, mode, energy, valence, danceability, features_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    song_id,
                    analysis.get('tempo', 0),
                    analysis.get('key', ''),
                    analysis.get('mode', ''),
                    analysis.get('energy', 0),
                    analysis.get('valence', 0),
                    analysis.get('danceability', 0),
                    json.dumps(analysis, ensure_ascii=False)
                ))
                
                conn.commit()
            
            print(f"✅ Música adicionada com sucesso! ID: {song_id}")
            return song_id
            
        except Exception as e:
            print(f"❌ Erro ao adicionar música: {str(e)}")
            return None
    
    def get_song_by_id(self, song_id: int) -> Optional[Dict]:
        """Obtém música por ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.*, af.tempo, af.key, af.mode, af.energy, af.valence, af.danceability
                    FROM songs s
                    LEFT JOIN audio_features af ON s.id = af.song_id
                    WHERE s.id = ?
                ''', (song_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'id': result[0],
                        'title': result[1],
                        'artist': result[2],
                        'album': result[3],
                        'genre': result[4],
                        'year': result[5],
                        'duration': result[6],
                        'file_path': result[7],
                        'file_size': result[8],
                        'created_at': result[9],
                        'updated_at': result[10],
                        'tempo': result[11],
                        'key': result[12],
                        'mode': result[13],
                        'energy': result[14],
                        'valence': result[15],
                        'danceability': result[16]
                    }
                return None
        except Exception as e:
            print(f"Erro ao obter música: {str(e)}")
            return None
    
    def get_song_by_path(self, file_path: str) -> Optional[Dict]:
        """Obtém música por caminho do arquivo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM songs WHERE file_path = ?', (file_path,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'title': result[1],
                        'artist': result[2],
                        'album': result[3],
                        'genre': result[4],
                        'year': result[5],
                        'duration': result[6],
                        'file_path': result[7],
                        'file_size': result[8],
                        'created_at': result[9],
                        'updated_at': result[10]
                    }
                return None
        except Exception as e:
            print(f"Erro ao obter música por caminho: {str(e)}")
            return None
    
    def search_songs(self, query: str = None, artist: str = None, genre: str = None, 
                    year: int = None, limit: int = 50) -> List[Dict]:
        """Busca músicas no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Construir query dinâmica
                conditions = []
                params = []
                
                if query:
                    conditions.append("(title LIKE ? OR artist LIKE ? OR album LIKE ?)")
                    params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
                
                if artist:
                    conditions.append("artist LIKE ?")
                    params.append(f"%{artist}%")
                
                if genre:
                    conditions.append("genre LIKE ?")
                    params.append(f"%{genre}%")
                
                if year:
                    conditions.append("year = ?")
                    params.append(year)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                cursor.execute(f'''
                    SELECT s.*, af.tempo, af.key, af.mode, af.energy, af.valence, af.danceability
                    FROM songs s
                    LEFT JOIN audio_features af ON s.id = af.song_id
                    WHERE {where_clause}
                    ORDER BY s.created_at DESC
                    LIMIT ?
                ''', params + [limit])
                
                results = cursor.fetchall()
                songs = []
                
                for result in results:
                    songs.append({
                        'id': result[0],
                        'title': result[1],
                        'artist': result[2],
                        'album': result[3],
                        'genre': result[4],
                        'year': result[5],
                        'duration': result[6],
                        'file_path': result[7],
                        'file_size': result[8],
                        'created_at': result[9],
                        'updated_at': result[10],
                        'tempo': result[11],
                        'key': result[12],
                        'mode': result[13],
                        'energy': result[14],
                        'valence': result[15],
                        'danceability': result[16]
                    })
                
                return songs
        except Exception as e:
            print(f"Erro na busca: {str(e)}")
            return []
    
    def get_similar_songs(self, song_id: int, limit: int = 10) -> List[Dict]:
        """Encontra músicas similares baseadas em características"""
        try:
            # Obter características da música de referência
            reference_song = self.get_song_by_id(song_id)
            if not reference_song:
                return []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar músicas com características similares
                cursor.execute('''
                    SELECT s.*, af.tempo, af.key, af.mode, af.energy, af.valence, af.danceability,
                           ABS(af.tempo - ?) as tempo_diff,
                           ABS(af.energy - ?) as energy_diff,
                           ABS(af.valence - ?) as valence_diff
                    FROM songs s
                    LEFT JOIN audio_features af ON s.id = af.song_id
                    WHERE s.id != ?
                    ORDER BY (tempo_diff + energy_diff + valence_diff) ASC
                    LIMIT ?
                ''', (
                    reference_song.get('tempo', 0),
                    reference_song.get('energy', 0),
                    reference_song.get('valence', 0),
                    song_id,
                    limit
                ))
                
                results = cursor.fetchall()
                similar_songs = []
                
                for result in results:
                    similar_songs.append({
                        'id': result[0],
                        'title': result[1],
                        'artist': result[2],
                        'album': result[3],
                        'genre': result[4],
                        'year': result[5],
                        'duration': result[6],
                        'file_path': result[7],
                        'file_size': result[8],
                        'created_at': result[9],
                        'updated_at': result[10],
                        'tempo': result[11],
                        'key': result[12],
                        'mode': result[13],
                        'energy': result[14],
                        'valence': result[15],
                        'danceability': result[16],
                        'similarity_score': 1.0 / (1.0 + result[17] + result[18] + result[19])
                    })
                
                return similar_songs
        except Exception as e:
            print(f"Erro ao buscar músicas similares: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estatísticas gerais
                cursor.execute('SELECT COUNT(*) FROM songs')
                total_songs = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT artist) FROM songs')
                total_artists = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT genre) FROM songs WHERE genre IS NOT NULL')
                total_genres = cursor.fetchone()[0]
                
                cursor.execute('SELECT SUM(duration) FROM songs')
                total_duration = cursor.fetchone()[0] or 0
                
                # Gêneros mais comuns
                cursor.execute('''
                    SELECT genre, COUNT(*) as count
                    FROM songs
                    WHERE genre IS NOT NULL
                    GROUP BY genre
                    ORDER BY count DESC
                    LIMIT 5
                ''')
                top_genres = cursor.fetchall()
                
                # Artistas mais comuns
                cursor.execute('''
                    SELECT artist, COUNT(*) as count
                    FROM songs
                    GROUP BY artist
                    ORDER BY count DESC
                    LIMIT 5
                ''')
                top_artists = cursor.fetchall()
                
                return {
                    'total_songs': total_songs,
                    'total_artists': total_artists,
                    'total_genres': total_genres,
                    'total_duration_hours': total_duration / 3600,
                    'top_genres': [{'genre': g[0], 'count': g[1]} for g in top_genres],
                    'top_artists': [{'artist': a[0], 'count': a[1]} for a in top_artists]
                }
        except Exception as e:
            print(f"Erro ao obter estatísticas: {str(e)}")
            return {}
    
    def remove_song(self, song_id: int) -> bool:
        """Remove música do banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remover características
                cursor.execute('DELETE FROM audio_features WHERE song_id = ?', (song_id,))
                
                # Remover da playlist
                cursor.execute('DELETE FROM playlist_songs WHERE song_id = ?', (song_id,))
                
                # Remover música
                cursor.execute('DELETE FROM songs WHERE id = ?', (song_id,))
                
                conn.commit()
                
                print(f"✅ Música {song_id} removida com sucesso")
                return True
        except Exception as e:
            print(f"❌ Erro ao remover música: {str(e)}")
            return False
    
    def create_playlist(self, name: str, description: str = None) -> Optional[int]:
        """Cria nova playlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO playlists (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                
                playlist_id = cursor.lastrowid
                conn.commit()
                
                print(f"✅ Playlist '{name}' criada com ID: {playlist_id}")
                return playlist_id
        except Exception as e:
            print(f"❌ Erro ao criar playlist: {str(e)}")
            return None
    
    def add_song_to_playlist(self, playlist_id: int, song_id: int) -> bool:
        """Adiciona música à playlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar se já existe
                cursor.execute('''
                    SELECT COUNT(*) FROM playlist_songs 
                    WHERE playlist_id = ? AND song_id = ?
                ''', (playlist_id, song_id))
                
                if cursor.fetchone()[0] > 0:
                    print("⚠️  Música já está na playlist")
                    return False
                
                # Obter próxima posição
                cursor.execute('''
                    SELECT MAX(position) FROM playlist_songs 
                    WHERE playlist_id = ?
                ''', (playlist_id,))
                
                next_position = (cursor.fetchone()[0] or 0) + 1
                
                # Adicionar música
                cursor.execute('''
                    INSERT INTO playlist_songs (playlist_id, song_id, position)
                    VALUES (?, ?, ?)
                ''', (playlist_id, song_id, next_position))
                
                conn.commit()
                print(f"✅ Música adicionada à playlist")
                return True
        except Exception as e:
            print(f"❌ Erro ao adicionar música à playlist: {str(e)}")
            return False
