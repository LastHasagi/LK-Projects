"""
Aplicação principal do Song Recognition
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from controllers.audio_controller import AudioController
from controllers.recognition_controller import RecognitionController
from services.music_database import MusicDatabase
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurações
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar controladores e serviços
audio_controller = AudioController()
recognition_controller = RecognitionController()
music_database = MusicDatabase()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/record', methods=['POST'])
def record_audio():
    """Endpoint para iniciar gravação de áudio"""
    try:
        result = audio_controller.start_recording()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop_record', methods=['POST'])
def stop_record():
    """Endpoint para parar gravação e processar áudio"""
    try:
        result = audio_controller.stop_recording()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recognize', methods=['POST'])
def recognize_song():
    """Endpoint para reconhecer música"""
    try:
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({'error': 'Nenhum arquivo de áudio fornecido'}), 400
        
        result = recognition_controller.recognize_song(audio_file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Song Recognition API funcionando'})

# Endpoints para gerenciamento do banco de músicas
@app.route('/api/songs', methods=['GET'])
def get_songs():
    """Lista músicas no banco"""
    try:
        query = request.args.get('q', '')
        artist = request.args.get('artist', '')
        genre = request.args.get('genre', '')
        year = request.args.get('year', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        songs = music_database.search_songs(
            query=query, artist=artist, genre=genre, year=year, limit=limit
        )
        return jsonify({'songs': songs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/<int:song_id>', methods=['GET'])
def get_song(song_id):
    """Obtém música específica"""
    try:
        song = music_database.get_song_by_id(song_id)
        if song:
            return jsonify(song)
        else:
            return jsonify({'error': 'Música não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/<int:song_id>/similar', methods=['GET'])
def get_similar_songs(song_id):
    """Obtém músicas similares"""
    try:
        limit = request.args.get('limit', 10, type=int)
        similar = music_database.get_similar_songs(song_id, limit)
        return jsonify({'similar_songs': similar})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs', methods=['POST'])
def add_song():
    """Adiciona nova música ao banco"""
    try:
        data = request.get_json()
        
        required_fields = ['file_path', 'title', 'artist']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        song_id = music_database.add_song(
            file_path=data['file_path'],
            title=data['title'],
            artist=data['artist'],
            album=data.get('album'),
            genre=data.get('genre'),
            year=data.get('year')
        )
        
        if song_id:
            return jsonify({'song_id': song_id, 'message': 'Música adicionada com sucesso'})
        else:
            return jsonify({'error': 'Erro ao adicionar música'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    """Remove música do banco"""
    try:
        success = music_database.remove_song(song_id)
        if success:
            return jsonify({'message': 'Música removida com sucesso'})
        else:
            return jsonify({'error': 'Erro ao remover música'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Obtém estatísticas do banco"""
    try:
        stats = music_database.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    """Cria nova playlist"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        
        if not name:
            return jsonify({'error': 'Nome da playlist é obrigatório'}), 400
        
        playlist_id = music_database.create_playlist(name, description)
        if playlist_id:
            return jsonify({'playlist_id': playlist_id, 'message': 'Playlist criada com sucesso'})
        else:
            return jsonify({'error': 'Erro ao criar playlist'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
