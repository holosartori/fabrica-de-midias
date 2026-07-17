#!/bin/bash
# ============================================================================
# 🔄 restart.sh — Reinicia o app Streamlit e atualiza dependências
# Chamado automaticamente pelo GitHub Actions a cada push na main
# ============================================================================
set -e

APP_DIR="${APP_PATH:-/root/video_app}"
SERVICE_NAME="video-app"
PORT=8501
LOG_FILE="$APP_DIR/streamlit.log"
APP_URL="https://fabricadeaudiobooks.app.br"

cd "$APP_DIR"

echo "📂 Trabalhando em: $APP_DIR"
echo "🐍 Atualizando dependências Python..."

# Ativa o venv se existir, senão usa o python do sistema
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
else
    echo "⚠️  venv não encontrado, usando pip do sistema"
    pip3 install -r requirements.txt --quiet || true
fi

echo "🔄 Reiniciando o app..."

# ----------------------------------------------------------------------------
# Estratégia 1: Systemd (recomendado — app sempre vivo mesmo após reboot)
# ----------------------------------------------------------------------------
if systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}.service"; then
    echo "   → Reiniciando via systemd..."

    sudo systemctl restart "$SERVICE_NAME"

    # Espera generosa pra evitar race condition na porta 8501
    sleep 6

    # Tenta confirmar até 3 vezes com 3 segundos entre tentativas
    ATIVO=""
    for i in 1 2 3; do
        if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
            ATIVO="sim"
            break
        fi
        echo "   ⏳ Tentativa $i/3 — aguardando serviço inicializar..."
        sleep 3
    done

    if [ "$ATIVO" = "sim" ]; then
        echo "   ✅ Serviço rodando!"
        sudo systemctl status "$SERVICE_NAME" --no-pager | head -8
    else
        echo "   ❌ Serviço falhou ao iniciar. Veja os logs:"
        sudo journalctl -u "$SERVICE_NAME" -n 30 --no-pager
        exit 1
    fi
else
    # ------------------------------------------------------------------------
    # Estratégia 2: Fallback (mata o processo na porta e sobe de novo)
    # ------------------------------------------------------------------------
    echo "   → systemd não detectado, usando modo fallback (nohup)..."

    # Tenta descobrir o PID do Streamlit na porta
    PID=""
    if command -v lsof &> /dev/null; then
        PID=$(lsof -t -i:$PORT 2>/dev/null || true)
    elif command -v fuser &> /dev/null; then
        PID=$(fuser $PORT/tcp 2>/dev/null || true)
    fi

    if [ -n "$PID" ]; then
        echo "   → Matando PID antigo: $PID"
        kill "$PID" 2>/dev/null || true
        sleep 3
    fi

    # Sobe o app de novo em background
    echo "   → Subindo novo processo..."
    nohup venv/bin/streamlit run app.py \
        --server.port=$PORT \
        --server.address=0.0.0.0 \
        --server.headless=true \
        > "$LOG_FILE" 2>&1 &

    sleep 6

    # Confirma que subiu
    if command -v lsof &> /dev/null && lsof -i:$PORT &> /dev/null; then
        echo "   ✅ App rodando na porta $PORT!"
        echo "   📝 Logs em: $LOG_FILE"
    else
        echo "   ⚠️  Não consegui confirmar se o app subiu. Veja: tail -f $LOG_FILE"
    fi
fi

echo ""
echo "🎉 Deploy finalizado com sucesso!"
echo "🌐 App disponível em: $APP_URL"
