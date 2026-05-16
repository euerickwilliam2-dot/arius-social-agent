from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Arius Social Agent")
templates = Jinja2Templates(directory="templates")

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass

def get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Você é um especialista sênior em social media strategy e marketing digital para o mercado brasileiro.
Analise perfis de negócios e gere planejamentos editoriais completos e estratégicos para Instagram.
Foco em B2B (donos de negócio) e conversão via reunião/call.
Responda APENAS com JSON válido, sem markdown, sem texto fora do JSON."""


def build_prompt(data: dict) -> str:
    return f"""
Analise este perfil e gere um planejamento de social media completo para Instagram:

PERFIL:
- Instagram: {data.get('instagram', '')}
- Segmento: {data.get('segmento', '')}
- Problema que resolve: {data.get('problema', '')}
- Público-alvo: {data.get('publico', '')}
- Faixa de renda do público: {data.get('preco_publico', '')}
- Posicionamento: {data.get('posicionamento', '')}
- Produtos/Serviços e Preços: {data.get('produtos', '')}
- Canais de aquisição: {data.get('canais', '')}
- Meta de faturamento: {data.get('meta', '')}
- Rotina disponível: {data.get('rotina', '')}
- Onde encontrar leads: {data.get('leads', '')}
- Ferramentas de gestão: {data.get('ferramentas', '')}
- Série de conteúdo principal: {data.get('serie', '')}
- Estado atual: {data.get('estado_atual', '')}
- Objetivo em 90 dias: {data.get('objetivo_90', '')}
- Contexto extra: {data.get('contexto', '')}

Retorne este JSON exato (sem campos extras, sem markdown):
{{
  "perfil_resumo": "2 frases resumindo o negócio e diferencial",
  "bio_otimizada": "bio otimizada para Instagram máx 150 chars com emoji",
  "posicionamento_unico": "USP em 1 frase poderosa",
  "pilares": [
    {{
      "nome": "nome do pilar",
      "descricao": "o que esse pilar faz pelo negócio",
      "porcentagem": 20,
      "cor": "#cor hex",
      "formatos": ["Reels", "Carrossel"],
      "exemplo_post": "exemplo de título/gancho de post"
    }}
  ],
  "rotina_semanal": [
    {{
      "dia": "Segunda",
      "foco": "tema do dia",
      "formato": "Reels / Carrossel / Story",
      "horario": "18h",
      "tema_exemplo": "título exemplo do conteúdo"
    }}
  ],
  "roadmap_90_dias": [
    {{
      "fase": "Fase 1 - Fundação",
      "periodo": "Dias 1-30",
      "foco": "objetivo desta fase",
      "meta_seguidores": "+500",
      "acoes_principais": ["ação 1", "ação 2", "ação 3"],
      "kpi_semana": "métrica a acompanhar"
    }}
  ],
  "hashtags": {{
    "alto_alcance": ["#hashtag"],
    "medio_alcance": ["#hashtag"],
    "nicho": ["#hashtag"],
    "estrategia": "como usar as hashtags"
  }},
  "ganchos_virais": [
    {{
      "gancho": "texto do gancho",
      "formato": "Reels",
      "objetivo": "o que esse gancho gera"
    }}
  ],
  "script_prospeccao": {{
    "abordagem_inicial": "mensagem de primeiro contato",
    "seguimento": "mensagem de follow-up",
    "fechamento": "mensagem para fechar reunião"
  }},
  "ctas_principais": ["CTA 1", "CTA 2", "CTA 3"],
  "kpis": [
    {{
      "metrica": "nome da métrica",
      "meta_30_dias": "valor",
      "meta_60_dias": "valor",
      "meta_90_dias": "valor"
    }}
  ],
  "checklist_imediato": ["ação imediata 1", "ação imediata 2"],
  "erros_evitar": ["erro 1", "erro 2"]
}}"""


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/gerar", response_class=HTMLResponse)
async def gerar_relatorio(
    request: Request,
    instagram: str = Form(...),
    segmento: str = Form(...),
    problema: str = Form(...),
    publico: str = Form(...),
    preco_publico: str = Form(""),
    posicionamento: str = Form(...),
    produtos: str = Form(...),
    canais: str = Form(...),
    meta: str = Form(...),
    rotina: str = Form(""),
    leads: str = Form(""),
    ferramentas: str = Form(""),
    serie: str = Form(""),
    estado_atual: str = Form(""),
    objetivo_90: str = Form(""),
    contexto: str = Form(""),
):
    data = {k: v for k, v in locals().items() if k not in ("request",)}

    message = get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(data)}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    strategy = json.loads(raw)

    return templates.TemplateResponse(
        "report.html", {"request": request, "data": data, "s": strategy}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
