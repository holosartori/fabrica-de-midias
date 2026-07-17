#!/bin/bash
# ============================================================================
# 🛠️  setup-server.sh — Configuração inicial do servidor (roda APENAS 1 VEZ)
# ============================================================================
# O que esse script faz:
#   1. Instala ffmpeg, python3, venv, pip, espeak-ng (Piper TTS precisa!)
#   2. Cria o virtualenv em /root/video_app/venv
#   3. Instala todas as dependências do requirements.txt
#   4. Baixa os modelos .onnx do Piper TTS
#   5. Configura o serviço systemd pra deixar o app rodando 24/7
# ============================================================================
set -e

APP_DIR="/root/video_app"
SERVICE_NAME="video-app"
PIPER_VOICES_DIR="$APP_DIR/piper_voices"

echo "═══════════════════════════════════════════════════════════"
echo "  🛠️  Setup do Servidor — Fábrica de Mídias"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ----------------------------------------------------------------------------
# 1. Dependências do sistema
# ----------------------------------------------------------------------------
echo "📦 [1/6] Instalando pacotes do sistema (ffmpeg, espeak-ng, python3-venv)..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y ffmpeg python3 python3-venv python3-pip \
                       espeak-ng espeak-ng-data libespeak-ng1
elif command -v yum &> /dev/null; then
    yum install -y ffmpeg python3 python3-venv python3-pip espeak-ng
else
    echo "❌ Gerenciador de pacotes não suportado. Instale ffmpeg, python3, venv e espeak-ng manualmente."
    exit 1
fi

# ----------------------------------------------------------------------------
# 2. Cria o diretório do app se não existir
# ----------------------------------------------------------------------------
echo "📂 [2/6] Preparando diretório $APP_DIR..."
mkdir -p "$APP_DIR"
mkdir -p "$PIPER_VOICES_DIR"

# ----------------------------------------------------------------------------
# 3. Virtualenv + dependências Python
# ----------------------------------------------------------------------------
echo "🐍 [3/6] Criando virtualenv e instalando dependências..."
cd "$APP_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Pré-baixa o modelo base do Whisper (~140MB) pra primeira execução ser instantânea
echo "🎙️  Pré-baixando modelo Whisper 'base'..."
python3 -c "import whisper; whisper.load_model('base')" 2>/dev/null || echo "   (modelo será baixado na primeira transcrição)"

# ----------------------------------------------------------------------------
# 4. Baixa os modelos do Piper TTS (5 vozes, ~80MB total)
# ----------------------------------------------------------------------------
echo "🎤 [4/6] Baixando modelos do Piper TTS..."
cd "$PIPER_VOICES_DIR"

declare -A VOZES=(
    ["pt_BR-faber-medium"]="pt/pt_BR/faber/medium"
    ["pt_BR-jeff-medium"]="pt/pt_BR/jeff/medium"
    ["pt_BR-cadu-medium"]="pt/pt_BR/cadu/medium"
    ["en_US-amy-medium"]="en/en_US/amy/medium"
    ["es_ES-davefx-medium"]="es/es_ES/davefx/medium"
)

for voz in "${!VOZES[@]}"; do
    if [ ! -f "${voz}.onnx" ]; then
        path="${VOZES[$voz]}"
        echo "   ↓ Baixando $voz..."
        wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/${path}/${voz}.onnx"     || echo "   ⚠️  Falhou: $voz"
        wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/${path}/${voz}.onnx.json" || echo "   ⚠️  Falhou: $voz.json"
    fi
done

VZS=$(ls *.onnx 2>/dev/null | wc -l)
echo "   ✅ $VZS modelo(s) Piper instalado(s)"

# ----------------------------------------------------------------------------
# 5. Permissões dos scripts
# ----------------------------------------------------------------------------
echo "🔑 [5/6] Configurando permissões..."
chmod +x restart.sh setup-server.sh 2>/dev/null || true

# ----------------------------------------------------------------------------
# 6. Systemd service
# ----------------------------------------------------------------------------
echo "⚙️  [6/6] Configurando serviço systemd..."

if [ -f "$APP_DIR/video-app.service" ]; then
    cp "$APP_DIR/video-app.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    sleep 5

    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "   ✅ Serviço ativo!"
    else
        echo "   ⚠️  Serviço não subiu. Tentando reiniciar..."
        systemctl restart "$SERVICE_NAME"
        sleep 3
    fi

    systemctl status "$SERVICE_NAME" --no-pager | head -10
else
    echo "   ⚠️  video-app.service não encontrado em $APP_DIR"
    echo "   → O app vai rodar em modo nohup quando você chamar restart.sh"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Setup concluído!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  📊 Comandos úteis:"
echo "     • Ver logs:       sudo journalctl -u $SERVICE_NAME -f"
echo "     • Reiniciar:      sudo systemctl restart $SERVICE_NAME"
echo "     • Parar:          sudo systemctl stop $SERVICE_NAME"
echo "     • Status:         sudo systemctl status $SERVICE_NAME"
echo ""
echo "  🌐 App disponível em: http://$(hostname -I | awk '{print $1}'):8501"
echo ""

