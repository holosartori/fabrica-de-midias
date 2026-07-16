# 🎙️ Fábrica de Mídias — Deploy Automatizado

App Streamlit com deploy automatizado via GitHub Actions. Cada `git push` na `main` reinicia o app no servidor automaticamente.

---

## 📁 Estrutura do projeto

```
video_app/
├── app.py                      # O app Streamlit em si
├── requirements.txt            # Dependências Python
├── .gitignore                  # Arquivos ignorados pelo Git
├── restart.sh                  # Script de reinicialização (chamado pelo GitHub)
├── setup-server.sh             # Setup INICIAL do servidor (roda 1 vez)
├── video-app.service           # Arquivo do systemd
└── .github/
    └── workflows/
        └── deploy.yml          # Pipeline do GitHub Actions
```

---

## 🚀 Setup Inicial (passo a passo, só na primeira vez)

### 1. Suba o código pro GitHub

```bash
cd /caminho/do/seu/projeto
git init
git add .
git commit -m "primeira versão"
git branch -M main
git remote add origin git@github.com:SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

### 2. Copie os arquivos pro servidor

Do seu PC local:
```bash
scp -r app.py requirements.txt restart.sh setup-server.sh video-app.service .gitignore root@SEU_IP:/root/video_app/
```

### 3. Rode o setup no servidor

```bash
ssh root@SEU_IP
cd /root/video_app
chmod +x setup-server.sh restart.sh
sudo bash setup-server.sh
```

Esse script instala ffmpeg, cria o venv, baixa o modelo do Whisper e sobe o serviço systemd.

### 4. Configure os 4 secrets no GitHub

Vá em **Settings → Secrets and variables → Actions → New repository secret**:

| Nome do secret       | Valor                              | Exemplo                          |
|----------------------|------------------------------------|----------------------------------|
| `SSH_HOST`           | IP ou domínio do seu servidor      | `123.456.78.90` ou `srv.exemplo.com` |
| `SSH_USERNAME`       | Usuário SSH                        | `root`                           |
| `SSH_PRIVATE_KEY`    | Chave privada SSH (conteúdo do arquivo) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `APP_PATH`           | Caminho do app no servidor         | `/root/video_app`                |

> 💡 **Como gerar a chave SSH pro deploy:**
> ```bash
> # No seu PC, gere uma chave específica pra deploy
> ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy
> 
> # Copie a chave pública pro servidor
> ssh-copy-id -i ~/.ssh/github_deploy.pub root@SEU_IP
> 
> # Copie a chave PRIVADA (todo o conteúdo) pro secret SSH_PRIVATE_KEY
> cat ~/.ssh/github_deploy
> ```

---

## 🔁 Workflow do dia a dia

Depois de tudo configurado, o ciclo é assim:

```bash
# 1. Edita o código no seu PC
# 2. Testa localmente: streamlit run app.py
# 3. Sobe pro GitHub
git add .
git commit -m "ajustei o cálculo de IMC"
git push
```

Em **~1 minuto** o app tá no ar com a versão nova. Pode ir lá no navegador dar F5. ✨

---

## 🛠️ Comandos úteis no servidor

```bash
# Ver logs em tempo real (Ctrl+C pra sair)
sudo journalctl -u video-app -f

# Ver as últimas 100 linhas do log
sudo journalctl -u video-app -n 100 --no-pager

# Reiniciar manualmente
sudo systemctl restart video-app

# Parar o app
sudo systemctl stop video-app

# Status
sudo systemctl status video-app

# Deploy manual (caso precise sem push)
bash /root/video_app/restart.sh
```

---

## 🔥 Solução de problemas

### App não sobe depois do deploy
```bash
sudo journalctl -u video-app -n 50 --no-pager
```

### Mudou o requirements.txt e quer forçar reinstalação
```bash
cd /root/video_app
source venv/bin/activate
pip install -r requirements.txt --upgrade --force-reinstall
sudo systemctl restart video-app
```

### Esqueceu a senha do LivePIX
Abre o `app.py`, procura por `SENHA_APOIADOR`, troca pelo novo valor, faz `git add . && git commit -m "nova senha" && git push`. Pronto, deploy automático atualiza em 1 min.

### Quer mudar a porta
Edita o `video-app.service` (campo `--server.port=8501`) e o `restart.sh` (variável `PORT=8501`), faz commit + push.

---

## 📊 Custos

- **Servidor VPS**: depende do provider (DigitalOcean $6/mês, Hetzner €4/mês, Contabo €5/mês, etc.)
- **GitHub Actions**: grátis até 2000 minutos/mês em repositórios públicos
- **Domínio** (opcional): R$ 40-60/ano

Esse setup é mais que suficiente pro seu app rodar liso, mesmo com vários usuários simultâneos.

---

Feito com ☕ e ❤️ por Mavis 🚀
