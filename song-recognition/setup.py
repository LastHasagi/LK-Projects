"""
Script de configuração para Song Recognition
"""
import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Executa um comando e mostra o resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} concluído")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {description}: {e.stderr}")
        return False

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário")
        print(f"   Versão atual: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def create_virtual_environment():
    """Cria ambiente virtual"""
    if os.path.exists('venv'):
        print("✅ Ambiente virtual já existe")
        return True
    
    return run_command('python -m venv venv', 'Criando ambiente virtual')

def install_dependencies():
    """Instala dependências do projeto"""
    pip_cmd = 'venv\\Scripts\\pip' if platform.system() == 'Windows' else 'venv/bin/pip'
    
    # Atualizar pip primeiro
    run_command(f'{pip_cmd} install --upgrade pip', 'Atualizando pip')
    
    # Instalar dependências
    return run_command(f'{pip_cmd} install -r requirements.txt', 'Instalando dependências')

def create_directories():
    """Cria diretórios necessários"""
    directories = ['data', 'temp_audio', 'static/uploads']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Diretório criado: {directory}")
        else:
            print(f"✅ Diretório já existe: {directory}")
    
    return True

def setup_environment_file():
    """Configura arquivo de ambiente"""
    if os.path.exists('.env'):
        print("✅ Arquivo .env já existe")
        return True
    
    if os.path.exists('env.example'):
        import shutil
        shutil.copy('env.example', '.env')
        print("✅ Arquivo .env criado a partir do env.example")
        print("⚠️  Configure suas chaves de API no arquivo .env")
        return True
    else:
        print("⚠️  Arquivo env.example não encontrado")
        return False

def main():
    """Função principal de setup"""
    print("🎵 Song Recognition - Configuração do Projeto")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Criar ambiente virtual
    if not create_virtual_environment():
        print("❌ Falha ao criar ambiente virtual")
        sys.exit(1)
    
    # Instalar dependências
    if not install_dependencies():
        print("❌ Falha ao instalar dependências")
        sys.exit(1)
    
    # Criar diretórios
    create_directories()
    
    # Configurar arquivo de ambiente
    setup_environment_file()
    
    print("\n" + "=" * 50)
    print("🎉 Configuração concluída com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Configure suas chaves de API no arquivo .env")
    print("2. Ative o ambiente virtual:")
    
    if platform.system() == 'Windows':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("3. Execute a aplicação:")
    print("   python run.py")
    print("\n🌐 Acesse: http://localhost:5000")

if __name__ == '__main__':
    main()
