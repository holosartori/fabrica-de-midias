#!/bin/bash
set -e
APP_DIR="${APP_PATH:-/root/video_app}"
SERVICE_NAME="video-app"
PORT=8501
LOG_FILE="$APP_DIR/streamlit.log"
cd "$APP_DIR"
echo "📂 Trabalhando em: $APP_DIR"
echo "🐍 Atualizando dependências Python..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
fi
echo "🔄 Liberando a porta $PORT..."
if command -v lsof &> /dev/null; then
    PIDS=$(lsof -t -i:$PORT 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "   → Matando PIDs: $PIDS"
        kill -9 $PIDS 2>/dev/null || true
        sleep 2
    fi
elif command -v fuser &> /dev/null; then
    fuser -k -9 $PORT/tcp 2>/dev/null || true
    sleep 2
fi
echo "🔄 Reiniciando o app..."
if systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}.service"; then
    echo "   → Reiniciando via systemd..."
    sudo systemctl restart "$SERVICE_NAME"
    sleep 3
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "   ✅ Serviço rodando!"
    else
        echo "   ❌ Serviço falhou. Logs:"
        sudo journalctl -u "$SERVICE_NAME" -n 30 --no-pager
        exit 1
    fi
else
    echo "   → systemd não detectado, usando nohup..."
    nohup venv/bin/streamlit run app.py \
        --server.port=$PORT \
        --server.address=0.0.0.0 \
        --server.headless=true \
        > "$LOG_FILE" 2>&1 &
    sleep 4
    echo "   ✅ App rodando!"
fi
echo ""
echo "🎉 Deploy finalizado!"
