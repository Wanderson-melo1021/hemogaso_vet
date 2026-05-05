# Hemogasometria Venosa Veterinária

Ferramenta clínica de auxílio à interpretação de hemogasometria venosa e cálculo de reposições em cães e gatos.

Desenvolvida para uso à beira do paciente, com suporte a dispositivos móveis.

**Acesse:** [wanderson-melo1021.github.io/hemogaso_vet](https://wanderson-melo1021.github.io/hemogaso_vet/)

---

## Funcionalidades

**Interpretação automatizada de:**

- Equilíbrio ácido-base (pH, pCO₂, HCO₃⁻, BE)
- Distúrbio primário e compensação esperada
- Ânion Gap com correção para albumina
- Delta-Delta e SID aparente
- Eletrólitos: Na⁺, K⁺, Cl⁻, Ca²⁺ ionizado, fósforo, magnésio
- Lactato, glicose, hematócrito

**Cálculo de reposições com dose e taxa para:**

- Bicarbonato (NaHCO₃)
- Potássio (KCl) — com concentração e velocidade máxima por peso
- Sódio (hipo e hipernatremia) — com déficit e tempo mínimo de correção
- Cálcio ionizado (gluconato e cloreto de cálcio)
- Fósforo e magnésio
- Glicose (hipoglicemia leve, moderada e grave)

**Classificação por gravidade:** normal · leve · moderado · grave · crítico

**Valores de referência espécie-específicos** para cão e gato, com destaque visual conforme espécie selecionada.

---

## Versões disponíveis

| Arquivo | Descrição |
|---|---|
| `index.html` | Ferramenta web — uso direto no navegador, sem instalação |
| `hemogasometria.py` | Script Python — uso em linha de comando ou ambiente computacional |

---

## Como usar (versão web)

1. Selecione a espécie (cão ou gato)
2. Informe o peso e os valores da hemogasometria disponíveis
3. Clique em **Analisar Hemogasometria**
4. Revise os achados, a classificação de gravidade e os cálculos de reposição
5. Use o botão **Imprimir / PDF** para gerar relatório

---

## Como usar (versão Python)

```bash
python hemogasometria.py
```

Siga as instruções interativas no terminal. Requer Python 3.8 ou superior, sem dependências externas.

---

## Valores de referência

Baseados em literatura de medicina interna e terapia intensiva veterinária (Dibartola, 2012; DiBartola & Bateman, 2006; Hopper, 2015).

| Parâmetro | Cão | Gato |
|---|---|---|
| pH | 7,32 – 7,40 | 7,28 – 7,41 |
| pCO₂ (mmHg) | 35 – 50 | 33 – 45 |
| HCO₃⁻ (mEq/L) | 18 – 24 | 17 – 22 |
| Na⁺ (mEq/L) | 140 – 155 | 149 – 160 |
| K⁺ (mEq/L) | 3,5 – 5,5 | 3,5 – 5,0 |
| Cl⁻ (mEq/L) | 105 – 115 | 112 – 129 |
| Ca²⁺ ion. (mmol/L) | 1,12 – 1,40 | 1,12 – 1,40 |
| Lactato (mmol/L) | < 2,5 | < 2,5 |
| Glicose (mg/dL) | 70 – 120 | 65 – 130 |
| Hematócrito (%) | 37 – 60 | 25 – 55 |

---

## Aviso

Ferramenta de auxílio clínico. Não substitui o julgamento do médico-veterinário responsável. Doses e taxas devem ser adaptadas à condição clínica individual do paciente.

---

## Autor

**Wanderson** — Médico-Veterinário · Doutorando em Biotecnologia (RENORBIO/UFPI)  
Área de concentração: Nefrologia Veterinária e Terapia Intensiva  
[@wanderson_nefrovet](https://instagram.com/wanderson_nefrovet)
