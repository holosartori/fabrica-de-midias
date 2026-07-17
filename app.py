"""
Fábrica de Mídias | Premium
- TTS: Edge TTS (online) + Piper TTS (local) — motor híbrido
- STT: Whisper local
"""

import streamlit as st
import asyncio
import os
import uuid
import urllib.parse
import datetime
import wave
import subprocess
import whisper
from PIL import Image
from pypdf import PdfReader
from pydub import AudioSegment

# =====================================================================
# ⚙️ CONFIGURAÇÕES
# =====================================================================
SENHA_APOIADOR = "VALEU10"
SENHA_MASTER_DONO = "MINHASENHADEACESSOTOTAL"

LIMITE_MINUTOS_TTS = 5.0
LIMITE_MINUTOS_STT = 5.0

LINK_LIVEPIX_OFICIAL = "https://widget.livepix.gg/embed/0073569a-c57a-4d8d-b4cd-92e611844bfb"

PIPER_VOICES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piper_voices")
# =====================================================================

st.set_page_config(
    page_title="Fábrica de Mídias | Premium",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title { font-size: clamp(1.6rem, 4vw, 2.8rem); font-weight: 800; text-align: center; color: #1E293B; margin-bottom: 0.2rem; word-wrap: break-word; }
    .sub-title { font-size: clamp(0.9rem, 2vw, 1.1rem); text-align: center; color: #64748B; margin-bottom: 1.5rem; word-wrap: break-word; }
    video, audio { width: 100% !important; max-width: 100% !important; border-radius: 8px; }
    .stTextArea textarea { font-size: 16px !important; }
    .badge-hybrid { display: inline-block; background: linear-gradient(90deg, #0EA5E9 50%, #047857 50%); color: white; font-size: 0.75rem; font-weight: 600; padding: 3px 10px; border-radius: 12px; margin-bottom: 0.8rem; }
</style>
""", unsafe_allow_html=True)

if "vip_liberado" not in st.session_state:
    st.session_state.vip_liberado = False
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:8]

SID = st.session_state.session_id


# =====================================================================
# ☕ SIDEBAR
# =====================================================================
with st.sidebar:
    st.markdown("### 🔑 Desbloquear Recursos (Estourou o Limite?)")
    st.write("Se você precisa processar arquivos de áudio/vídeo maiores que 5 minutos, obtenha sua chave de acesso apoiando nosso projeto!")
    st.info(
        "💡 **Como seu apoio é utilizado:**\n\n"
        "• **50%** é destinado a cobrir os custos do servidor e manutenção desta ferramenta.\n\n"
        "• **50%** é doado diretamente para o **Projeto Cãomer**, ajudando a alimentar e cuidar de cães de rua."
    )
    st.markdown(f"""
        <a href="{LINK_LIVEPIX_OFICIAL}" target="_blank" style="text-decoration: none;">
            <div style="background-color: #00D1B2; color: white; font-weight: bold; padding: 12px 10px; border-radius: 8px; text-align: center; box-shadow: 0px 4px 10px rgba(0, 209, 178, 0.2); font-size: 14px; margin-bottom: 15px;">
                🔓 Apoiar e Obter Código de Acesso
            </div>
        </a>
    """, unsafe_allow_html=True)
    st.markdown("⚠️ *Para receber sua senha, após realizar o PIX de qualquer valor mande uma mensagem na própria plataforma do LivePIX solicitando a chave, ou insira a senha padrão caso já a tenha recebido.*")
    senha_digitada = st.text_input("Insira sua senha de liberação aqui:", type="password", key="app_senha_vip")
    if senha_digitada == SENHA_MASTER_DONO:
        st.session_state.vip_liberado = True
        st.success("👑 Modo Dono Ativo! (Acesso Ilimitado)")
    elif senha_digitada == SENHA_APOIADOR:
        st.session_state.vip_liberado = True
        st.success("🔓 Modo Apoiador Ativo! (Acesso Premium)")
    elif senha_digitada:
        st.error("Senha inválida.")

    st.markdown("---")
    st.markdown("### 🔧 Status dos Motores TTS")
    # Piper
    if os.path.isdir(PIPER_VOICES_DIR):
        vozes_piper = [f for f in os.listdir(PIPER_VOICES_DIR) if f.endswith(".onnx")]
        if vozes_piper:
            st.success(f"💻 Piper: {len(vozes_piper)} voz(es) local(is)")
        else:
            st.warning("💻 Piper: pasta vazia (sem modelos)")
    else:
        st.warning(f"💻 Piper: pasta {PIPER_VOICES_DIR} não existe")
    # Edge
    st.info("☁️ Edge TTS: online (depende da Microsoft)")


# =====================================================================
# 🔊 MOTOR TTS — HÍBRIDO (Edge + Piper)
# =====================================================================

# Cada entrada tem "engine" e "id" — o app roteia pro motor certo.
VOZES_DISPONIVEIS = {
    # ===== EDGE TTS (online, scraping da Microsoft) =====
    "☁️ Edge - Francisca (F) 🇧🇷":          {"engine": "edge",  "id": "pt-BR-FranciscaNeural"},
    "☁️ Edge - Thalita Multi (F) 🇧🇷":     {"engine": "edge",  "id": "pt-BR-ThalitaMultilingualNeural"},
    "☁️ Edge - Antonio (M) 🇧🇷":            {"engine": "edge",  "id": "pt-BR-AntonioNeural"},
    "☁️ Edge - Jenny (F) 🇺🇸":              {"engine": "edge",  "id": "en-US-JennyNeural"},
    "☁️ Edge - Christopher (M) 🇺🇸":        {"engine": "edge",  "id": "en-US-ChristopherNeural"},
    "☁️ Edge - Elvira (F) 🇪🇸":             {"engine": "edge",  "id": "es-ES-ElviraNeural"},
    "☁️ Edge - Alvaro (M) 🇪🇸":             {"engine": "edge",  "id": "es-ES-AlvaroNeural"},
    # ===== PIPER TTS (local, sem billing, MIT) =====
    "💻 Piper - Faber (M) 🇧🇷":             {"engine": "piper", "id": "pt_BR-faber-medium"},
    "💻 Piper - Jeff (M) 🇧🇷":              {"engine": "piper", "id": "pt_BR-jeff-medium"},
    "💻 Piper - Cadu (M) 🇧🇷":              {"engine": "piper", "id": "pt_BR-cadu-medium"},
    "💻 Piper - Amy (F) 🇺🇸":               {"engine": "piper", "id": "en_US-amy-medium"},
    "💻 Piper - Davefx (M) 🇪🇸":            {"engine": "piper", "id": "es_ES-davefx-medium"},
}


# ---------- Edge TTS ----------
def gerar_audio_edge(texto: str, voz_id: str, velocidade: str, output_path: str):
    """Usa edge-tts (online, scraping da Microsoft). Síncrono via asyncio."""
    import edge_tts

    async def _run():
        communicate = edge_tts.Communicate(texto, voz_id, rate=velocidade)
        await communicate.save(output_path)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run())
        loop.close()
    except Exception:
        # fallback pra casos onde já tem loop rodando
        asyncio.run(_run())


# ---------- Piper TTS ----------
def _parse_length_scale(velocidade: str) -> float:
    """-12% → 0.88, +0% → 1.0"""
    sinal = -1 if velocidade.startswith("-") else 1
    pct = abs(int(velocidade.replace("%", "").replace("+", "")))
    if sinal == -1:
        return max(0.5, 1.0 - pct / 100)
    return min(2.0, 1.0 + pct / 100)


@st.cache_resource
def carregar_voz_piper(voz_id: str):
    """Cacheia o modelo Piper em RAM (uma vez por voz)."""
    from piper import PiperVoice, SynthesisConfig
    onnx_path = os.path.join(PIPER_VOICES_DIR, f"{voz_id}.onnx")
    json_path = os.path.join(PIPER_VOICES_DIR, f"{voz_id}.onnx.json")
    if not (os.path.exists(onnx_path) and os.path.exists(json_path)):
        raise FileNotFoundError(
            f"Modelo Piper não encontrado para '{voz_id}'. Esperado em {onnx_path}"
        )
    return PiperVoice.load(onnx_path, json_path)


def gerar_audio_piper(texto: str, voz_id: str, velocidade: str, output_path: str):
    """Piper local. Sintetiza em WAV temp e converte pra MP3 com ffmpeg."""
    voice = carregar_voz_piper(voz_id)
    length_scale = _parse_length_scale(velocidade)
    wav_temp = output_path.replace(".mp3", ".wav")
    with wave.open(wav_temp, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(voice.config.sample_rate)
        syn_config = SynthesisConfig(length_scale=length_scale)
        voice.synthesize(texto, wav_file, syn_config=syn_config)
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_temp, "-codec:a", "libmp3lame", "-b:a", "192k", output_path],
        check=True, capture_output=True,
    )
    os.remove(wav_temp)


# ---------- Roteador ----------
def gerar_audio(texto: str, voz_info: dict, velocidade: str, output_path: str):
    """Despacha pro motor certo baseado em voz_info['engine']."""
    engine = voz_info["engine"]
    voz_id = voz_info["id"]
    if engine == "edge":
        gerar_audio_edge(texto, voz_id, velocidade, output_path)
    elif engine == "piper":
        gerar_audio_piper(texto, voz_id, velocidade, output_path)
    else:
        raise ValueError(f"Motor TTS desconhecido: {engine}")


# =====================================================================
# OUTROS (Whisper + helpers)
# =====================================================================
@st.cache_resource
def carregar_modelo_whisper():
    return whisper.load_model("base")


def nome_arquivo_seguro(nome_original: str) -> str:
    return os.path.basename(nome_original)


# =====================================================================
# ABAS
# =====================================================================
aba1, aba2, aba3, aba4 = st.tabs([
    "📢 Texto ➔ Áudio / Vídeo (TTS)",
    "🎙️ Áudio ➔ Texto / Transcrição (STT)",
    "📺 Baixar do YouTube",
    "🩺 Calculadoras de Saúde",
])


# ==============================================================================
# ABA 1: TTS
# ==============================================================================
with aba1:
    st.markdown('<h1 class="main-title">📚 Fábrica de Audiobooks & Videobooks</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Converta textos ou arquivos em conteúdos em áudio e vídeo.</p>', unsafe_allow_html=True)
    st.markdown('<span class="badge-hybrid">☁️ Edge TTS + 💻 Piper TTS — 12 vozes disponíveis</span>', unsafe_allow_html=True)

    metodo_texto = st.radio("Como deseja enviar o conteúdo?", ["Digitar/Colar Texto", "Subir Arquivo (PDF ou TXT)"], horizontal=True, key="radio_metodo_texto")
    texto_final = ""
    if metodo_texto == "Digitar/Colar Texto":
        texto_final = st.text_area("Digite ou cole o texto do livro:", height=180, placeholder="Cole aqui o conteúdo...")
    else:
        arquivo_texto = st.file_uploader("Upload do arquivo do livro:", type=["pdf", "txt"])
        if arquivo_texto is not None:
            if arquivo_texto.name.endswith(".txt"):
                texto_final = arquivo_texto.read().decode("utf-8", errors="ignore")
            elif arquivo_texto.name.endswith(".pdf"):
                reader = PdfReader(arquivo_texto)
                texto_final = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

    col_fmt, col_voz, col_vel = st.columns([1, 1, 1])
    with col_fmt:
        formato_saida = st.radio("Escolha o tipo de mídia:", ["Audiobook (.mp3)", "Videobook (.mp4)"])
    with col_voz:
        voz_label = st.selectbox("Escolha a Voz Neural:", list(VOZES_DISPONIVEIS.keys()))
        voz_info = VOZES_DISPONIVEIS[voz_label]
    with col_vel:
        velocidade = st.select_slider("Velocidade da Fala:", options=["-20%", "-15%", "-12%", "-10%", "-5%", "+0%"], value="-12%")

    palavras = len(texto_final.split())
    duracao_estimada_minutos = palavras / 140.0

    formato_video = "YouTube / Padrão (16:9) - Horizontal"
    capa_file = None
    if formato_saida == "Videobook (.mp4)":
        st.markdown("### 🎬 Configurações do Vídeo")
        col_aspecto, col_capa = st.columns([1, 1])
        with col_aspecto:
            formato_video = st.selectbox("Selecione o Formato do Vídeo:", ["TikTok / Shorts (9:16) - Vertical", "YouTube (16:9) - Horizontal"])
        with col_capa:
            capa_file = st.file_uploader("Upload da Capa/Imagem de Fundo (Opcional):", type=["jpg", "jpeg", "png"])

    def preparar_imagem_capa(imagem_file, formato_str, caminho_saida):
        largura, altura = (1080, 1920) if "9:16" in formato_str else (1920, 1080)
        fundo = Image.new("RGB", (largura, altura), color=(15, 23, 42))
        if imagem_file is not None:
            img = Image.open(imagem_file).convert("RGB")
            img.thumbnail((largura, altura), Image.Resampling.LANCZOS)
            fundo.paste(img, ((largura - img.width) // 2, (altura - img.height) // 2))
        fundo.save(caminho_saida)

    excedeu_limite_tts = duracao_estimada_minutos > LIMITE_MINUTOS_TTS
    engine_label = "☁️ Edge" if voz_info["engine"] == "edge" else "💻 Piper"

    if excedeu_limite_tts and not st.session_state.vip_liberado:
        st.warning(f"⚠️ **Este texto vai gerar um arquivo muito longo!** Duração estimada: {duracao_estimada_minutos:.1f} minutos. O limite gratuito é de **{LIMITE_MINUTOS_TTS:.0f} minutos**.")
        st.info("💡 Ajude o **Projeto Cãomer** / manutenção e obtenha a senha de desbloqueio na barra lateral!")
        st.button("🚀 Gerar Conteúdo (Bloqueado)", disabled=True, use_container_width=True)
    else:
        if st.button("🚀 Gerar Conteúdo", use_container_width=True, key="btn_gerar_tts"):
            if not texto_final.strip():
                st.warning("Por favor, digite ou envie um texto válido.")
            else:
                audio_path = f"audio_{SID}.mp3"
                video_path = f"video_final_{SID}.mp4"
                capa_path = f"capa_processada_{SID}.png"

                audio_ok = False
                spinner_msg = f"Sintetizando com {engine_label}..."
                with st.spinner(spinner_msg):
                    try:
                        gerar_audio(texto_final, voz_info, velocidade, audio_path)
                        audio_ok = True
                        st.success(f"Sintetizado com sucesso! ({engine_label})")
                    except FileNotFoundError as e:
                        st.error(f"Modelo ausente: {e}")
                    except Exception as e:
                        st.error(f"Falha ao gerar o áudio: {e}")

                if audio_ok and formato_saida == "Audiobook (.mp3)":
                    with open(audio_path, "rb") as file:
                        audio_bytes = file.read()
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(label="📥 Baixar Audiobook (.mp3)", data=audio_bytes, file_name="audiobook.mp3", mime="audio/mpeg", use_container_width=True)

                elif audio_ok and formato_saida == "Videobook (.mp4)":
                    with st.spinner("Renderizando vídeo com FFmpeg..."):
                        try:
                            preparar_imagem_capa(capa_file, formato_video, capa_path)
                            cmd = [
                                "ffmpeg", "-y",
                                "-loop", "1", "-i", capa_path,
                                "-i", audio_path,
                                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
                                "-c:a", "aac", "-b:a", "192k",
                                "-pix_fmt", "yuv420p",
                                "-movflags", "+faststart",
                                "-shortest", video_path,
                            ]
                            subprocess.run(cmd, check=True, capture_output=True)
                            st.success("Vídeo renderizado!")
                        except subprocess.CalledProcessError as e:
                            st.error(f"Falha no ffmpeg: {e.stderr.decode(errors='ignore') if e.stderr else e}")
                        except Exception as e:
                            st.error(f"Falha ao renderizar: {e}")

                    video_bytes = None
                    if os.path.exists(video_path):
                        with open(video_path, "rb") as file:
                            video_bytes = file.read()
                        os.remove(video_path)
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    if os.path.exists(capa_path):
                        os.remove(capa_path)

                    if video_bytes is not None:
                        st.video(video_bytes, format="video/mp4")
                        st.download_button(label="📥 Baixar Videobook (.mp4)", data=video_bytes, file_name="videobook.mp4", mime="video/mp4", use_container_width=True)


# ==============================================================================
# ABA 2: STT
# ==============================================================================
with aba2:
    st.markdown('<h1 class="main-title">🎙️ Transcritor de Áudio para Texto</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Extraia o texto de arquivos de áudio locais.</p>', unsafe_allow_html=True)

    audio_uploaded = st.file_uploader("Selecione ou arraste seu arquivo de áudio:", type=["mp3", "wav", "m4a", "ogg", "aac", "flac"])

    if audio_uploaded is not None:
        st.audio(audio_uploaded)
        nome_seguro = nome_arquivo_seguro(audio_uploaded.name)
        temp_duracao_path = f"temp_measure_{SID}_{nome_seguro}"
        with open(temp_duracao_path, "wb") as f:
            f.write(audio_uploaded.getbuffer())
        try:
            audio_segment = AudioSegment.from_file(temp_duracao_path)
            duracao_audio_minutos = len(audio_segment) / (1000.0 * 60.0)
        except Exception:
            duracao_audio_minutos = 0.0
        finally:
            if os.path.exists(temp_duracao_path):
                os.remove(temp_duracao_path)

        excedeu_limite_stt = duracao_audio_minutos > LIMITE_MINUTOS_STT
        if excedeu_limite_stt and not st.session_state.vip_liberado:
            st.warning(f"⚠️ **Limite de Uso Grátis Excedido!** Seu áudio possui {duracao_audio_minutos:.1f} minutos. O limite gratuito é de **{LIMITE_MINUTOS_STT:.0f} minutos** por arquivo.")
            st.info("💡 Libere arquivos longos obtendo a senha na barra lateral!")
            st.button("⚡ Transcrever Áudio Agora (Bloqueado)", disabled=True, use_container_width=True)
        else:
            if st.button("⚡ Transcrever Áudio Agora", use_container_width=True):
                temp_audio_path = f"temp_{SID}_{nome_seguro}"
                with st.spinner("Processando áudio local com Whisper..."):
                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_uploaded.getbuffer())
                    try:
                        model = carregar_modelo_whisper()
                        resultado = model.transcribe(temp_audio_path, language="pt")
                        texto_transcrito = resultado["text"].strip()
                        st.success("✨ Transcrição concluída!")
                        st.text_area("Texto Transcrito:", value=texto_transcrito, height=250)
                        st.download_button(label="📥 Baixar Transcrição (.txt)", data=texto_transcrito, file_name=f"transcricao_{nome_seguro}.txt", mime="text/plain", use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro no processamento: {e}")
                    finally:
                        if os.path.exists(temp_audio_path):
                            os.remove(temp_audio_path)


# ==============================================================================
# ABA 3: YOUTUBE
# ==============================================================================
with aba3:
    st.markdown('<h1 class="main-title">📺 Downloader do YouTube</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Cole o link do vídeo e prepare o download seguro instantaneamente.</p>', unsafe_allow_html=True)
    st.success("✅ **Downloads ilimitados e gratuitos nesta aba!**")
    url_youtube = st.text_input("Cole o link do vídeo do YouTube aqui:", placeholder="https://www.youtube.com/watch?v=...", key="input_yt_url")
    st.info("ℹ️ **Nota:** O downloader gera o arquivo em formato de **Vídeo (.mp4)**. Se você precisar apenas do áudio para transcrever, você pode subir o próprio arquivo .mp4 diretamente na aba **🎙️ Transcritor**!")
    if st.button("📥 Iniciar Download", use_container_width=True, key="btn_yt_redirect"):
        if not url_youtube.strip():
            st.warning("Por favor, cole um link do YouTube válido primeiro!")
        elif "youtube.com" not in url_youtube and "youtu.be" not in url_youtube:
            st.warning("O link fornecido não parece ser um link válido do YouTube.")
        else:
            url_codificada = urllib.parse.quote(url_youtube, safe="")
            link_final_redirect = f"https://yt-dlp.sh/?url={url_codificada}"
            st.success("🎉 Link processado com sucesso! Clique no botão abaixo para concluir o download de forma rápida e segura.")
            st.markdown(f"""
                <a href="{link_final_redirect}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #22C55E; color: white; font-weight: bold; padding: 15px 20px; border-radius: 8px; text-align: center; box-shadow: 0px 4px 12px rgba(34, 197, 94, 0.3); font-size: 16px; margin-top: 10px;">
                        ⚡ Baixar arquivo agora no yt-dlp.sh
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.info("💡 Após baixar o arquivo no link seguro acima, envie-o na **Aba 🎙️ Transcritor** se precisar extrair o texto!")


# ==============================================================================
# ABA 4: CALCULADORAS
# ==============================================================================
with aba4:
    st.markdown('<h1 class="main-title">🩺 Calculadoras de Saúde</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">IMC, Idade Gestacional, Metabolismo Basal e Consumo Diário de Água.</p>', unsafe_allow_html=True)
    st.warning("⚠️ **Atenção:** Estas calculadoras fornecem apenas **estimativas gerais** e **não substituem** a avaliação de um profissional de saúde qualificado. Em caso de dúvidas, consulte seu médico ou nutricionista.")

    sub_imc, sub_dpp, sub_tmb, sub_agua = st.tabs(["⚖️ IMC", "🤰 Gestacional (DPP)", "🔥 Metabolismo Basal (TMB)", "💧 Água Diária"])

    with sub_imc:
        st.markdown("### ⚖️ Cálculo do Índice de Massa Corporal (IMC)")
        st.write("O IMC é uma medida internacional usada para classificar o peso corporal em relação à altura.")
        col1, col2 = st.columns(2)
        with col1: peso_imc = st.number_input("Peso (kg):", min_value=1.0, max_value=400.0, value=70.0, step=0.1, key=f"imc_peso_{SID}")
        with col2: altura_imc = st.number_input("Altura (cm):", min_value=50.0, max_value=250.0, value=170.0, step=0.5, key=f"imc_altura_{SID}")
        if st.button("Calcular IMC", use_container_width=True, key=f"btn_imc_{SID}"):
            altura_m = altura_imc / 100.0
            imc = peso_imc / (altura_m ** 2)
            if imc < 18.5: categoria, cor, recomendacao = "Abaixo do peso", "🔵", "Procure um nutricionista para ganhar peso de forma saudável."
            elif imc < 25.0: categoria, cor, recomendacao = "Peso normal (saudável)", "🟢", "Mantenha uma alimentação equilibrada e pratique exercícios."
            elif imc < 30.0: categoria, cor, recomendacao = "Sobrepeso", "🟡", "Atenção à dieta e pratique atividades físicas regularmente."
            elif imc < 35.0: categoria, cor, recomendacao = "Obesidade Grau I", "🟠", "Recomenda-se acompanhamento médico e nutricional."
            elif imc < 40.0: categoria, cor, recomendacao = "Obesidade Grau II", "🔴", "Procure orientação médica especializada."
            else: categoria, cor, recomendacao = "Obesidade Grau III", "🟣", "Acompanhamento médico é essencial."
            st.markdown("---")
            st.metric("Seu IMC", f"{imc:.1f} kg/m²")
            st.info(f"**{cor} Classificação:** {categoria}")
            st.write(f"💡 **Recomendação:** {recomendacao}")
            st.caption("**Tabela de referência (OMS):**\n• Abaixo de 18,5 → Abaixo do peso\n• 18,5 – 24,9 → Peso normal\n• 25,0 – 29,9 → Sobrepeso\n• 30,0 – 34,9 → Obesidade Grau I\n• 35,0 – 39,9 → Obesidade Grau II\n• ≥ 40,0 → Obesidade Grau III")

    with sub_dpp:
        st.markdown("### 🤰 Data Provável do Parto (DPP)")
        st.write("Calculada pela **Regra de Naegele** a partir da Data da Última Menstruação (DUM).")
        dum = st.date_input("Data da Última Menstruação (DUM):", value=datetime.date.today() - datetime.timedelta(days=70), min_value=datetime.date(2000, 1, 1), max_value=datetime.date.today(), key=f"dum_{SID}")
        ciclo = st.number_input("Duração do seu ciclo menstrual (dias):", min_value=20, max_value=45, value=28, step=1, key=f"ciclo_{SID}", help="Ciclo regular costuma ser 28 dias. Ajuste se for diferente.")
        if st.button("Calcular DPP", use_container_width=True, key=f"btn_dpp_{SID}"):
            dpp = dum + datetime.timedelta(days=280 + (ciclo - 28))
            hoje = datetime.date.today()
            dias_gestacao = (hoje - dum).days
            semanas_gestacao = dias_gestacao / 7.0
            dias_para_dpp = (dpp - hoje).days
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1: st.metric("📅 DPP (Data Provável do Parto)", dpp.strftime("%d/%m/%Y"))
            with col2: st.metric("⏱️ Idade Gestacional Atual", f"{semanas_gestacao:.1f} semanas")
            if dias_para_dpp > 0: st.success(f"🎯 Faltam **{dias_para_dpp} dias** para a DPP!")
            elif dias_para_dpp == 0: st.success("🎉 **Hoje é a DPP!**")
            else: st.warning(f"⚠️ A DPP já passou há **{abs(dias_para_dpp)} dias**. Consulte seu obstetra.")
            if semanas_gestacao < 13: trimestre = "1º Trimestre (1–13 semanas)"
            elif semanas_gestacao < 27: trimestre = "2º Trimestre (14–27 semanas)"
            elif semanas_gestacao < 42: trimestre = "3º Trimestre (28–42 semanas)"
            else: trimestre = "Pós-DPP - consulte seu obstetra imediatamente"
            st.info(f"📍 Você está no **{trimestre}**")

    with sub_tmb:
        st.markdown("### 🔥 Taxa Metabólica Basal (TMB)")
        st.write("Calculada pela equação de **Mifflin-St Jeor** — a mais recomendada pela literatura atual.")
        col1, col2 = st.columns(2)
        with col1:
            sexo = st.radio("Sexo biológico:", ["Feminino", "Masculino"], key=f"sexo_{SID}", horizontal=True)
            idade = st.number_input("Idade (anos):", min_value=1, max_value=120, value=30, step=1, key=f"idade_{SID}")
        with col2:
            peso_tmb = st.number_input("Peso (kg):", min_value=1.0, max_value=400.0, value=70.0, step=0.1, key=f"tmb_peso_{SID}")
            altura_tmb = st.number_input("Altura (cm):", min_value=50.0, max_value=250.0, value=170.0, step=0.5, key=f"tmb_altura_{SID}")
        atividade = st.selectbox("Nível de Atividade Física:", ["Sedentário (pouco ou nenhum exercício)", "Levemente ativo (exercício leve 1–3 dias/semana)", "Moderadamente ativo (exercício moderado 3–5 dias/semana)", "Muito ativo (exercício intenso 6–7 dias/semana)", "Extremamente ativo (atleta ou trabalho físico pesado)"], key=f"atv_{SID}")
        fatores_atividade = {"Sedentário (pouco ou nenhum exercício)": 1.2, "Levemente ativo (exercício leve 1–3 dias/semana)": 1.375, "Moderadamente ativo (exercício moderado 3–5 dias/semana)": 1.55, "Muito ativo (exercício intenso 6–7 dias/semana)": 1.725, "Extremamente ativo (atleta ou trabalho físico pesado)": 1.9}
        if st.button("Calcular TMB", use_container_width=True, key=f"btn_tmb_{SID}"):
            tmb = (10 * peso_tmb) + (6.25 * altura_tmb) - (5 * idade)
            tmb += 5 if sexo == "Masculino" else -161
            fator = fatores_atividade[atividade]
            get_total = tmb * fator
            st.markdown("---")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.metric("🔥 TMB (repouso)", f"{tmb:.0f} kcal/dia")
                st.caption("Calorias que seu corpo gasta em repouso absoluto.")
            with col_r2:
                st.metric("⚡ GET (gasto total)", f"{get_total:.0f} kcal/dia")
                st.caption("Calorias considerando sua atividade física.")
            st.info(f"💡 **Sugestões de meta calórica diária:**\n\n• Para **manter o peso**: ~**{get_total:.0f} kcal/dia**\n\n• Para **perder peso** (déficit de 500 kcal): ~**{get_total - 500:.0f} kcal/dia**\n\n• Para **ganhar peso** (superávit de 500 kcal): ~**{get_total + 500:.0f} kcal/dia**")

    with sub_agua:
        st.markdown("### 💧 Consumo Diário de Água Recomendado")
        st.write("Estimativa baseada no peso corporal: aproximadamente **35 ml por kg/dia** como base, com ajustes por atividade e clima.")
        peso_agua = st.number_input("Seu peso (kg):", min_value=1.0, max_value=400.0, value=70.0, step=0.1, key=f"agua_peso_{SID}")
        fator_agua_label = st.selectbox("Nível de atividade / clima:", ["Sedentário / clima ameno (35 ml/kg)", "Ativo / clima quente (40 ml/kg)", "Muito ativo / clima muito quente (45 ml/kg)", "Atleta / gestante / lactante (50 ml/kg)"], key=f"agua_fator_{SID}")
        fatores_agua = {"Sedentário / clima ameno (35 ml/kg)": 35, "Ativo / clima quente (40 ml/kg)": 40, "Muito ativo / clima muito quente (45 ml/kg)": 45, "Atleta / gestante / lactante (50 ml/kg)": 50}
        if st.button("Calcular Água Diária", use_container_width=True, key=f"btn_agua_{SID}"):
            ml_por_kg = fatores_agua[fator_agua_label]
            total_ml = peso_agua * ml_por_kg
            total_litros = total_ml / 1000.0
            copos_200ml = total_ml / 200.0
            garrafas_500ml = total_ml / 500.0
            st.markdown("---")
            st.metric("💧 Meta diária de água", f"{total_litros:.2f} L", delta=f"{total_ml:.0f} ml")
            col1, col2 = st.columns(2)
            with col1: st.metric("🥤 Em copos de 200 ml", f"{copos_200ml:.1f} copos")
            with col2: st.metric("🍶 Em garrafas de 500 ml", f"{garrafas_500ml:.1f} garrafas")
            st.info("💡 **Dicas para manter a hidratação:**\n\n• Beba um copo de água ao acordar e antes de cada refeição\n\n• Carregue sempre uma garrafa com você\n\n• Aumente a ingestão em dias quentes ou de exercício intenso\n\n• Frutas e vegetais (melancia, pepino, laranja) também hidratam")

