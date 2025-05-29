import requests
import json

def produces_anamnese(texto):
    with open("anamnese_structure.json", "r", encoding="utf-8") as f:
        estrutura = json.load(f)

    prompt = f"""
    Preencha os campos do seguinte JSON de anamnese com base no texto abaixo.

    Estrutura:
    {json.dumps(estrutura, indent=2, ensure_ascii=False)}

    Texto:
    {texto}
    """

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer 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",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "deepseek/deepseek-prover-v2:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )

    if response.status_code == 200:
        data = response.json()
        resposta = data["choices"][0]["message"]["content"]

        try:
            anamnese_preenchida = json.loads(resposta)
            with open("anamnese_output.json", "w", encoding="utf-8") as f:
                json.dump(anamnese_preenchida, f, ensure_ascii=False, indent=2)
            #print("✅ Anamnese preenchida salva em anamnese_output.json")
        except json.JSONDecodeError:
            #print("⚠️ A resposta da IA não está em JSON válido. Verifique o conteúdo:")
            print(resposta)
    else:
        print(f"Erro ao chamar API: {response.status_code}")
        print(response.content)
