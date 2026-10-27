import streamlit as st
from google import genai
from PIL import Image
import asyncio
import edge_tts
import json
import re
import urllib.parse
import random
import requests
from io import BytesIO
import os
from dotenv import load_dotenv

# .env dosyasındaki şifreyi sisteme yükler
load_dotenv()

# --- 1. SAYFA AYARLARI VE TASARIM ---
st.set_page_config(page_title="Dijital Dönüşüm Rehberi", page_icon="♻️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1b5e20;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

# API BAĞLANTISI 
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None

if "final_visual_url" not in st.session_state:
    st.session_state.final_visual_url = None

if "messages" not in st.session_state:
    st.session_state.messages = []
    
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "tr-TR-EmelNeural", rate="+20%")
    await communicate.save("plan.mp3")

# --- 2. ÜST BAŞLIK VE AÇIKLAMA ---
st.title("♻️ Dijital Dönüşüm Rehberi")
st.caption("Sürdürülebilir Moda ve Akıllı Dönüşüm Platformu")

with st.expander("✨ Platform Nasıl Çalışır?", expanded=False):
    st.markdown("""
        1.  📸 **Fotoğrafını Yükle:** Gardırobunda bekleyen parçanın fotoğrafını seç ve saniyeler içinde yapay zekanın onu analiz etmesini izle.
        2.  🎭 **Tarzını Seç:** Kıyafetinin hangi moda akımına göre dönüşmesini istediğini belirle.
        3.  🤖 **Analizi Başlat:** 'Dönüşümü Başlat' butonuna basarak dijital tasarımcı ajanlarımızı ve sürdürülebilirlik motorumuzu harekete geçir.
        4.  🌈 **Dönüşüm Dünyasını Keşfet:** Analiz bittiğinde seni 5 farklı uzmanlık alanı karşılayacak.
    """)

st.write("---")

# --- 3. ANA UYGULAMA MANTIĞI ---
uploaded_file = st.file_uploader("Kıyafet fotoğrafını buraya yükleyin...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1.5]) 
    
    with col1:
        img_input = Image.open(uploaded_file)
        st.image(img_input, caption='Yüklenen Parça', use_container_width=True)
    
    with col2:
        st.markdown("<h4 style='color:#2e7d32;'>🎭 Dönüşüm Tarzını Belirle</h4>", unsafe_allow_html=True)
        secilen_tarz = st.selectbox(
            "Yapay zeka bu kıyafeti hangi tarza göre yeniden tasarlasın?",
            [
                "Modern & Sürdürülebilir Klasik", 
                "Y2K (2000'ler Nostaljisi)", 
                "Cyberpunk / Fütüristik", 
                "Grunge / Rock / Asimetrik", 
                "Minimalist / Kapsül Dolap", 
                "Haute Couture / Avangard Moda"
            ]
        )
        st.write("") 
        
        if st.button("Dönüşüm Analizini Başlat", use_container_width=True):
            prompt = f"""
            Sen usta bir moda tasarımcısı ve upcycle uzmanısın. Fotoğrafı incele ve yanıtını SADECE aşağıdaki JSON formatında ver. 
            ÇOK ÖNEMLİ: Kullanıcı bu kıyafeti kesinlikle **{secilen_tarz}** tarzında dönüştürmek istiyor!
            Tüm tasarım planını, vizyonunu ve görsel istemini bu {secilen_tarz} tarzını yansıtacak şekilde abartılı, yaratıcı ve detaylı hazırla.

            {{
                "kumas": "Kumaş ve model durumu hakkında bilgi...",
                "etki": "Çevresel etki tahmini...",
                "tasarim": "Adım adım {secilen_tarz} tarzı DIY tasarım planı...",
                "su_miktari": "SADECE RAKAM VE BİRİM YAZ (Örn: 2100 L). Kesinlikle açıklama veya parantez içi metin ekleme.",
                "atik_miktari": "SADECE RAKAM VE BİRİM YAZ (Örn: 1.2 kg). Kesinlikle açıklama veya parantez içi metin ekleme.",
                "kiyaslama": "Çarpıcı bir tasarruf örneği.",
                "gorsel_istemi": "A professional upcycled clothing design in {secilen_tarz} fashion style, highly detailed, photorealistic, 8k, cinematic lighting, editorial fashion photography"
            }}
            """
            
            try:
                with st.spinner(f"Yapay Zeka {secilen_tarz} Tarzında Tasarlıyor... ✂️🎨"):
                    response = client.models.generate_content(model="models/gemini-2.5-flash", contents=[prompt, img_input])
                    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    
                    if json_match:
                        data = json.loads(json_match.group())
                        st.session_state.analysis_data = data
                        
                        try:
                            raw_prompt = data.get("gorsel_istemi", f"Upcycled fashion design in {secilen_tarz} style")
                            safe_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', str(raw_prompt))
                            encoded_prompt = urllib.parse.quote_plus(safe_prompt)
                            st.session_state.final_visual_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={random.randint(1,9999)}"
                        except:
                            st.session_state.final_visual_url = None

                        tasarim_metni = data.get('tasarim', '')
                        temiz_metin = tasarim_metni.replace("*", "").replace("#", "")
                        v_text = f"{secilen_tarz} tarzı dönüşüm planınız hazır. Lütfen adımları dinleyin: {temiz_metin}"
                        
                        # 403 HATASINI ÖNLEMEK İÇİN SES DEVRE DIŞI BIRAKILDI
                        # asyncio.run(generate_voice(v_text))
                        
                        st.success(f"✅ {secilen_tarz} Tarzında Analiz Başarıyla Tamamlandı!")
                    else:
                        st.error("JSON formatı çözülemedi.")
            except Exception as e:
                st.error(f"Hata oluştu: {e}")
        
        # --- 4. SEKMELER KISMI ---
        if st.session_state.analysis_data:
            data = st.session_state.analysis_data
            
            t1, t2, t3, t4, t5 = st.tabs([
                "🧵 Analiz", 
                "📊 Etki", 
                "💡 Tasarım", 
                "🖼️ Örnek Görünüm", 
                "🎧 Sesli Rehber"
            ])
            
            with t1:
                st.subheader("🔍 Teknik Detaylar")
                st.write(data.get("kumas", "Veri yok."))
            
            with t2:
                st.subheader("📈 Sürdürülebilirlik Raporu")
                m1, m2 = st.columns(2)
                m1.metric("Su Tasarrufu", data.get("su_miktari", "---"))
                m2.metric("Atık Azaltımı", data.get("atik_miktari", "---"))
                st.info(f"💡 {data.get('kiyaslama', '')}")
                st.write(data.get("etki", ""))
            
            with t3:
                st.subheader("📝 Dönüşüm Yol Haritası")
                st.markdown(data.get("tasarim", "Veri yok."))

            with t4:
                st.subheader("🖼️ Nihai Tasarım Prototipi")
                if st.session_state.final_visual_url:
                    try:
                        img_response = requests.get(st.session_state.final_visual_url)
                        if img_response.status_code == 200:
                            img = Image.open(BytesIO(img_response.content))
                            st.info("✨ **Tasarımcı Notu:** Yapay zeka ajanımız, kıyafetinizin potansiyelini analiz ederek aşağıdaki modern tasarımı oluşturdu.")
                            st.image(img, caption="Hayalinizdeki Yeni Tarz", use_container_width=True)
                            st.markdown("""
                            <div style="background-color: #f1f8e9; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32;">
                                <p style="color: #1b5e20; font-size: 18px; font-weight: bold; margin-bottom: 5px;">🎨 Harikalar Yaratmaya Hazır Mısınız?</p>
                                <p style="color: #33691e; font-size: 16px;">
                                    Yukarıdaki görsel, kıyafetinizin dönüşümden sonraki halini temsil etmektedir. 
                                    <b>"Tasarım"</b> sekmesindeki adımları takip ederek siz de bu benzersiz parçayı hayata geçirebilirsiniz.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("Görsel sunucu tarafından oluşturulamadı. Lütfen tekrar deneyin.")
                    except Exception as e:
                        st.error(f"Görsel görüntülenirken bir hata oluştu: {e}")
                else:
                    st.warning("Görsel adresi oluşturulamadı.")

            with t5:
                st.subheader("🔊 Asistan Sesli Rehberi")
                st.warning("Microsoft sunucularındaki erişim kısıtlaması nedeniyle sesli rehber geçici olarak devre dışıdır.")

# --- 🤖 5. SOHBET KISMI (SOL YAN MENÜ) ---
with st.sidebar:
    st.markdown("""
    <div style="background-color:#f1f8e9; padding:15px; border-radius:15px; border:1px solid #c5e1a5; margin-bottom:20px;">
        <h3 style="color:#2e7d32; font-size: 18px; margin-top:0;">🤖 Akıllı Stil Danışmanı</h3>
        <p style="color:#33691e; font-size: 14px; margin-bottom:0;">Aklına takılanları bana sorabilirsin.</p>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Bir şeyler sor 👗"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Düşünüyor... 💭"):
                try:
                    kumas_detayi = st.session_state.analysis_data.get('kumas', 'bir kıyafet') if st.session_state.analysis_data else 'bir kıyafet'
                    
                    chat_prompt = f"""Sen samimi ve enerjik bir 'Sürdürülebilir Moda ve Upcycle' asistanısın. 
                    Kullanıcının elindeki parça: '{kumas_detayi}'
                    
                    ÇOK ÖNEMLİ KURALLAR:
                    1. ASLA destan yazma! Cevapların ÇOK KISA, ÖZ ve EN FAZLA 2-3 CÜMLE olmalı.
                    2. Kullanıcı sadece doğrudan sorusunun pratik cevabını duymak istiyor, lafı uzatma.
                    
                    Kullanıcının mesajı: '{user_input}'"""
                    
                    chat_response = client.models.generate_content(
                        model="models/gemini-2.5-flash", 
                        contents=chat_prompt
                    )
                    bot_reply = chat_response.text
                    st.markdown(bot_reply)
                except Exception as e:
                    bot_reply = "Kısa bir bağlantı sorunu yaşadım, tekrar sorar mısın?"
                    st.markdown(bot_reply)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})