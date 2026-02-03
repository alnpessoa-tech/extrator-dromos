import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io  # Faltava importar o 'io' para gerar o Excel
import json # Usar json em vez de eval é mais seguro e estável

# 1. Configuração da API (Lendo dos Secrets)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # DEFINIÇÃO DO MODELO (Faltava definir a variável 'model' no seu código)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erro na chave da API. Verifique os Secrets do Streamlit.")

st.set_page_config(page_title="Extrator Dromos", layout="wide")
st.title("🏗️ Extrator de Fichas de Apropriação - Dromos")

uploaded_files = st.file_uploader("Upload de PDFs ou Fotos das Fichas", type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True)

if st.button("Processar Documentos"):
    if uploaded_files:
        resultados = []
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                img = Image.open(file)
                
                # Prompt otimizado para os campos da sua ficha
                prompt = """
                Analise esta Ficha de Apropriação da Dromos Infraestrutura.
                Extraia os dados manuscritos e retorne APENAS um objeto JSON com as chaves exatas:
                DATA, FRENTE DE SERVIÇO, SENTIDO, ESTACA, MATERIAL, UNID., QUANT., SERVIÇO, ESTACA INICIAL, ESTACA FINAL, COMP.(m), LARG.(m), ALTURA(m), OBS:
                
                Instruções extras:
                - Converta QUANT. para número se possível.
                - Se um campo estiver vazio, retorne "".
                - Extraia exatamente o que estiver escrito à mão.
                """
                
                response = model.generate_content([prompt, img])
                
                # Limpeza da resposta para garantir que seja um JSON válido
                json_text = response.text.replace("```json", "").replace("```", "").strip()
                dados = json.loads(json_text)
                resultados.append(dados)
                
            except Exception as e:
                st.error(f"Erro ao processar o arquivo {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if resultados:
            df = pd.DataFrame(resultados)
            
            # Reorganiza as colunas na ordem que você solicitou
            colunas_obrigatorias = ["DATA", "FRENTE DE SERVIÇO", "SENTIDO", "ESTACA", "MATERIAL", "UNID.", "QUANT.", "SERVIÇO", "ESTACA INICIAL", "ESTACA FINAL", "COMP.(m)", "LARG.(m)", "ALTURA(m)", "OBS:"]
            # Adiciona colunas faltantes se a IA esquecer alguma
            for col in colunas_obrigatorias:
                if col not in df.columns:
                    df[col] = ""
            
            df = df[colunas_obrigatorias]
            
            st.write("### Dados Extraídos", df)
            
            # Gerar Excel na memória
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Baixar Planilha Excel",
                data=output.getvalue(),
                file_name="apropriacao_dromos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Por favor, faça o upload de pelo menos um arquivo.")
