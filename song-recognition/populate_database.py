#!/usr/bin/env python3
"""
Script para popular o banco de dados com músicas de exemplo
"""
import os
import sys
from services.music_database import MusicDatabase
from services.audio_fingerprint import AudioFingerprint
import json

def create_sample_songs():
    """Cria músicas de exemplo no banco de dados"""
    
    # Músicas de exemplo (você pode adicionar suas próprias)
    sample_songs = [
        {
            'title': 'Bohemian Rhapsody',
            'artist': 'Queen',
            'album': 'A Night at the Opera',
            'genre': 'Rock',
            'year': 1975,
            'file_path': 'sample_music/bohemian_rhapsody.wav'
        },
        {
            'title': 'Imagine',
            'artist': 'John Lennon',
            'album': 'Imagine',
            'genre': 'Pop',
            'year': 1971,
            'file_path': 'sample_music/imagine.wav'
        },
        {
            'title': 'Hotel California',
            'artist': 'Eagles',
            'album': 'Hotel California',
            'genre': 'Rock',
            'year': 1976,
            'file_path': 'sample_music/hotel_california.wav'
        },
        {
            'title': 'Stairway to Heaven',
            'artist': 'Led Zeppelin',
            'album': 'Led Zeppelin IV',
            'genre': 'Rock',
            'year': 1971,
            'file_path': 'sample_music/stairway_to_heaven.wav'
        },
        {
            'title': 'Billie Jean',
            'artist': 'Michael Jackson',
            'album': 'Thriller',
            'genre': 'Pop',
            'year': 1982,
            'file_path': 'sample_music/billie_jean.wav'
        }
    ]
    
    print("🎵 Populando banco de dados com músicas de exemplo...")
    print("=" * 60)
    
    # Inicializar serviços
    music_db = MusicDatabase()
    fingerprint_system = AudioFingerprint()
    
    # Criar diretório de músicas de exemplo
    os.makedirs('sample_music', exist_ok=True)
    
    added_count = 0
    skipped_count = 0
    
    for song_data in sample_songs:
        print(f"\n🔄 Processando: {song_data['title']} - {song_data['artist']}")
        
        # Verificar se arquivo existe
        if not os.path.exists(song_data['file_path']):
            print(f"⚠️  Arquivo não encontrado: {song_data['file_path']}")
            print("   Criando arquivo de exemplo...")
            
            # Criar arquivo de áudio de exemplo
            create_sample_audio_file(song_data['file_path'])
        
        try:
            # Adicionar música ao banco
            song_id = music_db.add_song(
                file_path=song_data['file_path'],
                title=song_data['title'],
                artist=song_data['artist'],
                album=song_data['album'],
                genre=song_data['genre'],
                year=song_data['year']
            )
            
            if song_id:
                print(f"✅ Adicionada com sucesso! ID: {song_id}")
                added_count += 1
            else:
                print(f"❌ Erro ao adicionar música")
                skipped_count += 1
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            skipped_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Resumo:")
    print(f"   ✅ Músicas adicionadas: {added_count}")
    print(f"   ⚠️  Músicas ignoradas: {skipped_count}")
    
    # Mostrar estatísticas do banco
    print(f"\n📈 Estatísticas do banco:")
    stats = music_db.get_statistics()
    for key, value in stats.items():
        if isinstance(value, list):
            print(f"   {key}: {len(value)} itens")
        else:
            print(f"   {key}: {value}")

def create_sample_audio_file(file_path: str):
    """Cria um arquivo de áudio de exemplo"""
    try:
        import numpy as np
        import soundfile as sf
        
        # Parâmetros do áudio
        duration = 30  # 30 segundos
        sample_rate = 22050
        
        # Gerar sinal de exemplo (tom + ruído)
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Tom principal (440 Hz - nota A)
        frequency = 440
        signal = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Adicionar harmônicos
        signal += 0.1 * np.sin(2 * np.pi * frequency * 2 * t)
        signal += 0.05 * np.sin(2 * np.pi * frequency * 3 * t)
        
        # Adicionar ruído
        noise = 0.02 * np.random.randn(len(t))
        signal += noise
        
        # Aplicar envelope (fade in/out)
        envelope = np.ones_like(signal)
        fade_samples = int(0.1 * sample_rate)  # 0.1 segundos de fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        signal *= envelope
        
        # Salvar arquivo
        sf.write(file_path, signal, sample_rate)
        print(f"   📁 Arquivo criado: {file_path}")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar arquivo: {str(e)}")

def show_database_info():
    """Mostra informações sobre o banco de dados"""
    print("\n🔍 Informações do banco de dados:")
    print("=" * 40)
    
    try:
        music_db = MusicDatabase()
        stats = music_db.get_statistics()
        
        print(f"📊 Total de músicas: {stats.get('total_songs', 0)}")
        print(f"🎤 Total de artistas: {stats.get('total_artists', 0)}")
        print(f"🎵 Total de gêneros: {stats.get('total_genres', 0)}")
        print(f"⏱️  Duração total: {stats.get('total_duration_hours', 0):.1f} horas")
        
        print(f"\n🏆 Top gêneros:")
        for genre_info in stats.get('top_genres', []):
            print(f"   {genre_info['genre']}: {genre_info['count']} músicas")
        
        print(f"\n👑 Top artistas:")
        for artist_info in stats.get('top_artists', []):
            print(f"   {artist_info['artist']}: {artist_info['count']} músicas")
            
    except Exception as e:
        print(f"❌ Erro ao obter informações: {str(e)}")

def main():
    """Função principal"""
    print("🎵 Song Recognition - Populador de Banco de Dados")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--info':
        show_database_info()
        return
    
    # Perguntar se quer continuar
    response = input("Deseja popular o banco com músicas de exemplo? (s/N): ").strip().lower()
    
    if response in ['s', 'sim', 'y', 'yes']:
        create_sample_songs()
    else:
        print("Operação cancelada.")
        return
    
    # Mostrar informações finais
    show_database_info()
    
    print(f"\n🎉 Processo concluído!")
    print(f"💡 Dica: Você pode adicionar suas próprias músicas usando a API:")
    print(f"   POST /api/songs")
    print(f"   {{'file_path': 'caminho/para/sua/musica.wav', 'title': 'Título', 'artist': 'Artista'}}")

if __name__ == '__main__':
    main()
