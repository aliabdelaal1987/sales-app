import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. إعدادات الصفحة والواجهة الرسمية ---
st.set_page_config(
    page_title="مساعد المحاسبة والمبيعات",
    page_icon="📊",
    layout="wide"
)

st.title("📊 نظام المساعد المحاسبي للمبيعات والمديونيات")
st.caption("برنامج مخصص لتحليل وتتبع المبيعات والعملاء لشركة استيراد ألبان الأطفال")
st.divider()

# --- 2. الشريط الجانبي (Sidebar) للتحكم والملفات ---
with st.sidebar:
    st.header("⚙️ لوحة التحكم")
    api_key = st.text_input("أدخل مفتاح Gemini API Key:", type="password")
    st.divider()
    st.header("📁 ملف البيانات")
    uploaded_file = st.file_uploader("قم برفع ملف Sales (Excel أو CSV):", type=["xlsx", "csv"])
    if uploaded_file:
        st.success("تم رفع الملف بنجاح! ✅")

# --- 3. التعليمات البرمجية الدائمة للبوت ---
SYSTEM_INSTRUCTION = """
أنت "مساعد المحاسبة والمبيعات"، بوت مخصص لتحليل وتتبع بيانات مبيعات ومديونيات شركة استيراد وتوزيع ألبان الأطفال.

قواعد وأسلوب العمل:
1. المصدر الرئيسي المعتمد لبياناتك هو البيانات المرفقة من المستخدم عبر الملف.
2. عند الإجابة على أي استفسار، اعتمد حصراً وقبل كل شيء على البيانات المرفقة فقط دون أي تخمين أو افتراضات خارجية.
3. قدم إجاباتك ودراساتك بأسلوب محاسبي دقيق، مختصر، ومباشر موثق بالأرقام.
4. جدول المخرجات والبيانات (مثل المبيعات، المدفوعات، المتبقي، والمديونيات) يجب أن يعكس الحالة الحقيقية والمحدثة في الملف.
5. إذا سُئلت عن التحليل المالي أو مخاطر النسب، استند للمفاهيم المحاسبية والمالية بناءً على الأرقام الحقيقية.
"""

# --- 4. إدارة سجل المحادثة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. استقبال أسئلة المستخدم ومعالجتها ---
if prompt := st.chat_input("اكتب سؤالك المحاسبي هنا (مثال: كم إجمالي المتبقي على العميل عماد؟)..."):
    if not api_key:
        st.error("يرجى إدخل مفتاح API Key الجديد في الشريط الجانبي أولاً.")
        st.stop()
    if not uploaded_file:
        st.warning("يرجى رفع ملف المبيعات (Sales) من الشريط الجانبي لكي يتمكن البوت من الإجابة.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # تحويل البيانات لصيغة CSV مضغوطة لتوفير استهلاك الكلمات (Tokens)
        data_string = df.to_csv(index=False)
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner("جاري تحليل البيانات وإعداد الإجابة المحاسبية..."):
            try:
                genai.configure(api_key=api_key.strip())
                full_prompt = f"إليك بيانات ملف Sales الحالية:\n\n{data_string}\n\nسؤال المستخدم: {prompt}"

                # قائمة بالنماذج المتاحة للربط التلقائي
                models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
                response = None
                last_err = None

                for m_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(
                            model_name=m_name,
                            system_instruction=SYSTEM_INSTRUCTION
                        )
                        response = model.generate_content(full_prompt)
                        if response and response.text:
                            break
                    except Exception as e:
                        last_err = e
                        continue

                if response and response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.error(f"لم نتمكن من الاتصال. تأكد من إدخال المفتاح الجديد بشكل صحيح. تفاصيل الخطأ: {last_err}")

            except Exception as err:
                st.error(f"حدث خطأ في النظام: {err}")
