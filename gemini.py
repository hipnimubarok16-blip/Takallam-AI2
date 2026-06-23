import streamlit as st
import requests
import json

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Takallam AI - Teman Belajar Bicara Anda",
    page_icon="💬",
    layout="centered"
)

st.markdown("""
    <style>
    .main-title { font-size: 2.8rem; font-weight: 700; color: #2E7D32; text-align: center; margin-bottom: 0px; }
    .subtitle { font-size: 1.1rem; color: #555555; text-align: center; margin-bottom: 30px; font-style: italic; }
    .sidebar-title { font-size: 1.2rem; font-weight: bold; color: #1B5E20; }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = ""

BASE_PROMPT = """
Anda adalah 'Takallam AI', seorang tutor bahasa Arab virtual untuk kelas 10 Madrasah Aliyah (MA).
Respons harus menggunakan bahasa Arab yang fasih berharakat, diikuti terjemahan Indonesia di bawahnya.
Selalu akhiri dengan pertanyaan terbuka untuk memancing siswa berbicara.
"""

MODE_PROMPTS = {
    "التعارف (Perkenalan Diri)": "Fokus pada topik perkenalan diri, hobi, dan cita-cita.",
    "الحياة اليومية في المدرسة (Kehidupan Sehari-hari di Sekolah)": "Fokus pada aktivitas di Sekolah.",
    "النشاطات في العطلة (Aktivitas di Hari Libur)": "Fokus pada kegiatan saat liburan."
}

with st.sidebar:
    st.markdown("<div class='sidebar-title'>🔑 Akses Takallam AI</div>", unsafe_allow_html=True)
    username = st.text_input("Masukkan Username:", key="username_input", placeholder="Nama Anda")
    api_key = st.text_input("Masukkan Gemini API Key:", type="password", placeholder="AIzaSy...")
    
    st.markdown("---")
    selected_mode = st.selectbox("Pilih Topik Percakapan:", options=list(MODE_PROMPTS.keys()))
    
    if st.button("🔄 Reset Sesi Percakapan", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_mode = ""
        st.rerun()

# --- FUNGSI MULTI-URL FALLBACK (MEMUTARKAN SEMUA PINTU GOOGLE) ---
def panggil_gemini_api(key_user, prompt_text):
    clean_key = key_user.strip()
    
    # Kita coba 3 jalur URL berbeda sekaligus. Jika jalur 1 gagal 404, dia otomatis coba jalur 2, dst.
    jalur_url = [
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={clean_key}",
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={clean_key}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={clean_key}"
    ]
    
    terakhir_error = ""
    for url in jalur_url:
        try:
            payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
            response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
            if response.status_code == 200:
                res_json = response.json()
                return res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                terakhir_error = response.text
        except Exception as e:
            terakhir_error = str(e)
            continue
            
    raise Exception(f"Semua jalur pintu API menolak. Detail terakhir: {terakhir_error}")

# --- HALAMAN UTAMA ---
st.markdown("<div class='main-title'>💬 Takallam AI</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Teman Belajar Bicara Anda</div>", unsafe_allow_html=True)

if not username or not api_key:
    st.warning("👋 Silakan masukkan **Username** dan **Gemini API Key** Anda di sidebar.")
    st.stop()

if st.session_state.current_mode != selected_mode:
    st.session_state.current_mode = selected_mode
    st.session_state.messages = [] 

if len(st.session_state.messages) == 0:
    with st.spinner("Menghubungkan dengan Tutor..."):
        try:
            system_instruction = BASE_PROMPT + "\nTema: " + MODE_PROMPTS[selected_mode]
            prompt_awal = f"{system_instruction}\n\nSapa murid bernama {username} dengan ramah dan beri 1 pertanyaan pembuka."
            pembuka_text = panggil_gemini_api(api_key, prompt_awal)
            st.session_state.messages.append({"role": "assistant", "content": pembuka_text})
            st.rerun()
        except Exception as e:
            st.error("❌ Gagal Terhubung ke Google Gemini API.")
            st.code(str(e))
            st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("Tulis respon bahasa Arab Anda di sini..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("Takallam AI sedang mengetik..."):
            try:
                full_context = BASE_PROMPT + "\nTema: " + MODE_PROMPTS[selected_mode] + "\n\n"
                for msg in st.session_state.messages[:-1]:
                    full_context += f"{msg['role'].capitalize()}: {msg['content']}\n"
                full_context += f"User ({username}): {user_input}\nAssistant:"
                
                balasan_text = panggil_gemini_api(api_key, full_context)
                st.session_state.messages.append({"role": "assistant", "content": balasan_text})
                st.rerun()
            except Exception as e:
                st.error(f"Gagal mengirim tanggapan: {e}")