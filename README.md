# Hemogasometria Venosa Veterinária

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-live-brightgreen?logo=github)](https://wanderson-melo1021.github.io/hemogaso_vet/)

Ferramenta clínica de auxílio à interpretação de hemogasometria venosa e cálculo de reposições em **cães e gatos**.

Desenvolvida para uso à beira do paciente, com suporte a dispositivos móveis.

**Acesse agora:** [wanderson-melo1021.github.io/hemogaso_vet](https://wanderson-melo1021.github.io/hemogaso_vet/)

---

## Funcionalidades

**Interpretação automatizada de:**

- Equilíbrio ácido-base (pH, pCO₂, HCO₃⁻, BE) com classificação do distúrbio primário
- Compensação respiratória e metabólica esperada
- Ânion Gap com correção para albumina e Delta-Delta
- SID aparente
- Eletrólitos: Na⁺, K⁺, Cl⁻, Ca²⁺ ionizado, fósforo, magnésio
- Lactato, glicose, hematócrito

**Cálculo de reposições com dose e taxa por peso:**

| Parâmetro | Reposição calculada |
|-----------|---------------------|
| Bicarbonato | NaHCO₃ — déficit parcial, dose e velocidade |
| Potássio | KCl 19,1% e 10% — concentração, velocidade máxima |
| Sódio | Hipo e hipernatremia — déficit, taxa máxima, tempo mínimo |
| Cálcio | Gluconato e CaCl₂ — volume e velocidade |
| Fósforo | Fosfato de potássio IV |
| Magnésio | MgSO₄ 50% |
| Glicose | Dextrose 50% / D5% / D2,5% |

**Classificação por gravidade:** `Normal` · `Leve` · `Moderado` · `Grave` · `Crítico`

**Valores de referência espécie-específicos** para cão e gato.

---

## Versões disponíveis

| Arquivo | Descrição |
|---------|-----------|
| `index.html` | Ferramenta web — uso direto no navegador, sem instalação |
| `hemogasometria.py` | Script Python — uso em linha de comando |

---

## Como usar (versão web)

1. Selecione a espécie (cão ou gato)
2. Informe o peso e os valores da hemogasometria disponíveis
3. Clique em **Analisar Hemogasometria** ou pressione **Enter**
4. Revise os achados, a classificação de gravidade e os cálculos de reposição
5. Use o botão **Imprimir / PDF** para gerar relatório imprimível

---

## Como usar (versão Python)

```bash
pip install rich   # opcional — melhora a visualização no terminal
python hemogasometria.py
```

Siga as instruções interativas no terminal. Requer Python 3.8 ou superior.

---

## Valores de referência

Baseados em literatura de medicina interna e terapia intensiva veterinária (DiBartola, 2012; Hopper, 2015; AAHA, 2024).

| Parâmetro | Cão | Gato |
|-----------|-----|------|
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

## Deploy automático

O repositório utiliza **GitHub Actions** para publicar automaticamente no GitHub Pages a cada push na branch `main`.

---

## Aviso

Ferramenta de **auxílio clínico**. Não substitui o julgamento do médico-veterinário responsável. Doses e taxas devem ser adaptadas à condição clínica individual do paciente.

---

## Autor

**Wanderson** — Médico-Veterinário · Doutorando em Biotecnologia (RENORBIO/UFPI)  
Área de concentração: Nefrologia Veterinária e Terapia Intensiva  
[![Instagram](https://img.shields.io/badge/@wanderson__nefrovet-E4405F?logo=instagram&logoColor=white)](https://instagram.com/wanderson_nefrovet)

---

## Licença

MIT © Wanderson
