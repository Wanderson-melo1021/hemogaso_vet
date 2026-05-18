#!/usr/bin/env python3
"""
Hemogasometria Venosa — Interpretação e Reposição para Cães e Gatos
Ferramenta de auxílio clínico em nefrologia/terapia intensiva veterinária
"""

import sys
import math
from dataclasses import dataclass
from typing import Optional, List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.rule import Rule
    from rich import box
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    print("Instale rich para melhor visualização: pip3 install rich")

# ──────────────────────────────────────────────────────────────────────────────
# Valores de referência (hemogasometria VENOSA)
# ──────────────────────────────────────────────────────────────────────────────

REF = {
    "dog": {
        "pH":       (7.32, 7.40),
        "pCO2":     (35.0, 50.0),   # mmHg
        "HCO3":     (18.0, 24.0),   # mEq/L
        "BE":       (-4.0,  4.0),   # mEq/L
        "Na":       (140.0, 155.0), # mEq/L
        "K":        (3.5,   5.5),   # mEq/L
        "Cl":       (105.0, 115.0), # mEq/L
        "iCa":      (1.12,  1.40),  # mmol/L
        "Pi":       (2.9,   6.2),   # mg/dL
        "Mg":       (1.7,   2.7),   # mg/dL
        "lactate":  (0.0,   2.5),   # mmol/L
        "glucose":  (70.0,  120.0), # mg/dL
        "AG_range": (12.0,  24.0),
        # Alvos de correção
        "Na_target":   148.0,
        "HCO3_target": 15.0,   # alvo parcial seguro na acidose
        "K_target":    4.0,
    },
    "cat": {
        "pH":       (7.28, 7.41),
        "pCO2":     (33.0, 45.0),
        "HCO3":     (17.0, 22.0),
        "BE":       (-4.0,  4.0),
        "Na":       (149.0, 160.0),
        "K":        (3.5,   5.0),
        "Cl":       (112.0, 129.0),
        "iCa":      (1.12,  1.40),
        "Pi":       (3.0,   7.0),
        "Mg":       (1.8,   2.9),
        "lactate":  (0.0,   2.5),
        "glucose":  (65.0,  130.0),
        "AG_range": (13.0,  27.0),
        "Na_target":   154.0,
        "HCO3_target": 15.0,
        "K_target":    4.0,
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Estruturas de dados
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Valores:
    species: str   # "dog" | "cat"
    weight: float  # kg
    pH: Optional[float] = None
    pCO2: Optional[float] = None
    HCO3: Optional[float] = None
    BE: Optional[float] = None
    Na: Optional[float] = None
    K: Optional[float] = None
    Cl: Optional[float] = None
    iCa: Optional[float] = None
    Pi: Optional[float] = None    # fósforo mg/dL
    Mg: Optional[float] = None    # magnésio mg/dL
    lactate: Optional[float] = None
    glucose: Optional[float] = None
    Hct: Optional[float] = None   # hematócrito %
    albumin: Optional[float] = None  # g/dL


@dataclass
class Achado:
    categoria: str
    severidade: str   # normal | leve | moderado | grave | critico | info
    mensagem: str


@dataclass
class Reposicao:
    parametro: str
    indicacao: str
    calculo: str
    taxa: str
    atencao: str = ""


HARD_LIMITS = {
    "weight": (0.1, 250.0),
    "pH": (6.0, 8.5),
    "pCO2": (1.0, 300.0),
    "HCO3": (1.0, 120.0),
    "BE": (-80.0, 80.0),
    "Na": (50.0, 250.0),
    "K": (0.5, 20.0),
    "Cl": (30.0, 250.0),
    "iCa": (0.1, 5.0),
    "Pi": (0.1, 40.0),
    "Mg": (0.1, 20.0),
    "lactate": (0.0, 40.0),
    "glucose": (0.0, 3000.0),
    "Hct": (1.0, 90.0),
    "albumin": (0.1, 10.0),
}

EXTREME_WARN_LIMITS = {
    "weight": (0.1, 150.0),
    "pH": (6.5, 7.9),
    "pCO2": (5.0, 150.0),
    "HCO3": (1.0, 60.0),
    "BE": (-30.0, 30.0),
    "Na": (100.0, 210.0),
    "K": (1.0, 12.0),
    "Cl": (60.0, 170.0),
    "iCa": (0.1, 5.0),
    "Pi": (0.1, 25.0),
    "Mg": (0.1, 10.0),
    "lactate": (0.0, 30.0),
    "glucose": (0.0, 1500.0),
    "Hct": (1.0, 80.0),
    "albumin": (0.1, 8.0),
}

INPUT_LABELS = {
    "weight": "Peso",
    "pH": "pH",
    "pCO2": "pCO2",
    "HCO3": "HCO3",
    "BE": "BE",
    "Na": "Na⁺",
    "K": "K⁺",
    "Cl": "Cl⁻",
    "iCa": "Ca²⁺ ionizado",
    "Pi": "Fósforo",
    "Mg": "Magnésio",
    "lactate": "Lactato",
    "glucose": "Glicose",
    "Hct": "Hematócrito",
    "albumin": "Albumina",
}


def validar_valores(v: Valores) -> List[str]:
    if v.species not in REF:
        raise ValueError("Espécie inválida. Use 'dog' ou 'cat'.")
    if v.weight is None:
        raise ValueError("Peso é obrigatório.")
    if v.pH is None:
        raise ValueError("pH é obrigatório.")

    erros = []
    for campo, (vmin, vmax) in HARD_LIMITS.items():
        valor = getattr(v, campo)
        if valor is None:
            continue
        if valor < vmin or valor > vmax:
            erros.append(f"{INPUT_LABELS.get(campo, campo)} fora da faixa aceitável ({vmin}–{vmax}).")

    if erros:
        raise ValueError("Dados inválidos:\n  - " + "\n  - ".join(erros))

    avisos = []
    for campo, (vmin, vmax) in EXTREME_WARN_LIMITS.items():
        valor = getattr(v, campo)
        if valor is None:
            continue
        if valor < vmin or valor > vmax:
            avisos.append(
                f"{INPUT_LABELS.get(campo, campo)} = {valor} (faixa habitual {vmin}–{vmax})"
            )
    return avisos


# ──────────────────────────────────────────────────────────────────────────────
# Análise ácido-base
# ──────────────────────────────────────────────────────────────────────────────

def analisar_acido_base(v: Valores) -> List[Achado]:
    achados = []
    ref = REF[v.species]

    if v.pH is None:
        achados.append(Achado("Ácido-Base", "info", "pH não informado — análise incompleta."))
        return achados

    pH_lo, pH_hi = ref["pH"]
    pCO2_lo, pCO2_hi = ref["pCO2"]
    HCO3_lo, HCO3_hi = ref["HCO3"]

    acidemia  = v.pH < pH_lo
    alcalemia = v.pH > pH_hi

    # Gravidade do pH
    if acidemia:
        d = pH_lo - v.pH
        sev = "critico" if v.pH < 7.10 else ("grave" if d >= 0.10 else ("moderado" if d >= 0.05 else "leve"))
        achados.append(Achado("pH", sev, f"ACIDEMIA — pH {v.pH:.3f}  (ref {pH_lo}–{pH_hi})"))
    elif alcalemia:
        d = v.pH - pH_hi
        sev = "grave" if d >= 0.10 else ("moderado" if d >= 0.05 else "leve")
        achados.append(Achado("pH", sev, f"ALCALEMIA — pH {v.pH:.3f}  (ref {pH_lo}–{pH_hi})"))
    else:
        achados.append(Achado("pH", "normal", f"pH normal — {v.pH:.3f}"))

    if v.HCO3 is None or v.pCO2 is None:
        achados.append(Achado("Ácido-Base", "info", "HCO3 e/ou pCO2 ausentes — análise de distúrbio incompleta."))
        return achados

    meta_acid = v.HCO3 < HCO3_lo
    meta_alk  = v.HCO3 > HCO3_hi
    resp_acid = v.pCO2 > pCO2_hi
    resp_alk  = v.pCO2 < pCO2_lo

    # Distúrbio primário
    if acidemia:
        if meta_acid and resp_acid:
            d = "Distúrbio MISTO: Acidose Metabólica + Respiratória"
        elif meta_acid:
            d = "Acidose Metabólica"
        elif resp_acid:
            d = "Acidose Respiratória"
        else:
            d = "Acidemia — componentes em limites (misto?)"
        sev = "grave" if "MISTO" in d else "moderado"
    elif alcalemia:
        if meta_alk and resp_alk:
            d = "Distúrbio MISTO: Alcalose Metabólica + Respiratória"
        elif meta_alk:
            d = "Alcalose Metabólica"
        elif resp_alk:
            d = "Alcalose Respiratória"
        else:
            d = "Alcalemia — componentes em limites (misto?)"
        sev = "grave" if "MISTO" in d else "moderado"
    else:
        # pH normal — verificar compensação ou misto
        if meta_acid and resp_alk:
            d = "Misto: Acidose Metabólica + Alcalose Respiratória (pH compensado)"
        elif meta_alk and resp_acid:
            d = "Misto: Alcalose Metabólica + Acidose Respiratória (pH compensado)"
        elif meta_acid:
            d = "Acidose Metabólica compensada"
        elif resp_acid:
            d = "Acidose Respiratória compensada"
        elif meta_alk:
            d = "Alcalose Metabólica compensada"
        elif resp_alk:
            d = "Alcalose Respiratória compensada"
        else:
            d = "Equilíbrio ácido-base dentro dos limites"
        sev = "normal" if d.startswith("Equilíbrio") else ("moderado" if "Misto" in d else "leve")

    achados.append(Achado("Distúrbio Primário", sev, d))

    # Verificação de compensação
    if meta_acid and acidemia:
        pCO2_esp = 1.5 * v.HCO3 + 8.0   # Fórmula de Winter
        tol = 2.0
        if v.pCO2 < pCO2_esp - tol:
            achados.append(Achado("Compensação Resp.", "moderado",
                f"pCO2 ({v.pCO2:.1f}) abaixo do esperado ({pCO2_esp:.1f} ±{tol:.0f}) → provável alcalose resp. concomitante"))
        elif v.pCO2 > pCO2_esp + tol:
            achados.append(Achado("Compensação Resp.", "moderado",
                f"pCO2 ({v.pCO2:.1f}) acima do esperado ({pCO2_esp:.1f} ±{tol:.0f}) → provável acidose resp. concomitante"))
        else:
            achados.append(Achado("Compensação Resp.", "normal",
                f"Compensação respiratória adequada — pCO2 esperado {pCO2_esp:.1f} ±{tol:.0f} mmHg"))

    if meta_alk and alcalemia:
        pCO2_esp = 0.7 * v.HCO3 + 21.0
        tol = 2.0
        if abs(v.pCO2 - pCO2_esp) <= tol:
            achados.append(Achado("Compensação Resp.", "normal",
                f"Compensação respiratória adequada — pCO2 esperado {pCO2_esp:.1f} ±{tol:.0f} mmHg"))
        else:
            achados.append(Achado("Compensação Resp.", "moderado",
                f"Compensação inadequada — pCO2 esperado {pCO2_esp:.1f}, medido {v.pCO2:.1f}"))

    if resp_acid and acidemia:
        delta = v.pCO2 - pCO2_hi
        esp_aguda   = HCO3_hi + (delta / 10.0) * 1.5
        esp_cronica = HCO3_hi + (delta / 10.0) * 3.5
        achados.append(Achado("Compensação Met.", "info",
            f"HCO3 esperado → Aguda: {esp_aguda:.1f}  |  Crônica: {esp_cronica:.1f}  (medido: {v.HCO3:.1f} mEq/L)"))

    if resp_alk and alcalemia:
        delta = pCO2_lo - v.pCO2
        esp_aguda   = HCO3_lo - (delta / 10.0) * 2.0
        esp_cronica = HCO3_lo - (delta / 10.0) * 5.0
        achados.append(Achado("Compensação Met.", "info",
            f"HCO3 esperado → Aguda: {esp_aguda:.1f}  |  Crônica: {esp_cronica:.1f}  (medido: {v.HCO3:.1f} mEq/L)"))

    # Ânion Gap
    if v.Na is not None and v.Cl is not None:
        AG = v.Na - (v.Cl + v.HCO3)
        AG_corr = AG
        corr_txt = ""
        if v.albumin is not None:
            alb_norm = 2.5 if v.species == "cat" else 3.0
            AG_corr = AG + 2.5 * (alb_norm - v.albumin)
            corr_txt = f"  (corrigido albumina: {AG_corr:.1f})"
        AG_lo, AG_hi = ref["AG_range"]
        if AG_corr > AG_hi:
            sev = "grave" if AG_corr > AG_hi + 12 else "moderado"
            achados.append(Achado("Ânion Gap", sev,
                f"ELEVADO: {AG:.1f} mEq/L{corr_txt}  (ref {AG_lo:.0f}–{AG_hi:.0f})"
                " → MUDPILES: uremia, cetoacidose, acidose lática, etilenoglicol, salicilato"))
        elif AG_corr < AG_lo:
            achados.append(Achado("Ânion Gap", "leve",
                f"BAIXO: {AG:.1f} mEq/L{corr_txt} → hipoalbuminemia, hiperglobulinemia"))
        else:
            achados.append(Achado("Ânion Gap", "normal",
                f"Normal: {AG:.1f} mEq/L{corr_txt}"))

        # Delta-Delta (acidose metabólica AG elevado)
        if AG_corr > AG_hi and meta_acid:
            AG_mid = (AG_lo + AG_hi) / 2
            delta_AG  = AG_corr - AG_mid
            delta_HCO3 = HCO3_hi - v.HCO3
            if delta_HCO3 > 0:
                dd = delta_AG / delta_HCO3
                if dd < 0.4:
                    txt = f"Δ/Δ = {dd:.2f} (<0,4) → acidose AG alto + AG normal concomitante"
                    sev = "moderado"
                elif dd > 2.0:
                    txt = f"Δ/Δ = {dd:.2f} (>2,0) → alcalose metabólica subjacente"
                    sev = "moderado"
                else:
                    txt = f"Δ/Δ = {dd:.2f} (0,4–2,0) → acidose metabólica pura com AG elevado"
                    sev = "normal"
                achados.append(Achado("Delta-Delta", sev, txt))

    # SID simplificado
    if v.Na is not None and v.K is not None and v.Cl is not None:
        SID = (v.Na + v.K) - v.Cl
        SID_norm = 40 if v.species == "dog" else 38
        if SID < SID_norm - 4:
            achados.append(Achado("SID Aparente", "moderado",
                f"SID = {SID:.1f} mEq/L (esperado ~{SID_norm}) → acidose por íons fortes"))
        elif SID > SID_norm + 4:
            achados.append(Achado("SID Aparente", "leve",
                f"SID = {SID:.1f} mEq/L → alcalose por íons fortes"))

    return achados


# ──────────────────────────────────────────────────────────────────────────────
# Análise de eletrólitos e metabólitos
# ──────────────────────────────────────────────────────────────────────────────

def analisar_eletrolitos(v: Valores) -> List[Achado]:
    achados = []
    ref = REF[v.species]

    def classifica(val, lo, hi):
        if val < lo:
            d = lo - val
        elif val > hi:
            d = val - hi
        else:
            return "normal", 0.0
        span = (hi - lo) or 1.0
        frac = d / span
        sev = "critico" if frac > 1.0 else ("grave" if frac > 0.6 else ("moderado" if frac > 0.2 else "leve"))
        return ("baixo" if val < lo else "alto"), sev, d

    def add(parametro, val, unidade, lo, hi, nome_baixo, nome_alto, dicas_baixo="", dicas_alto=""):
        res = classifica(val, lo, hi)
        if res[0] == "normal":
            achados.append(Achado(parametro, "normal", f"Normal: {val} {unidade}  (ref {lo}–{hi})"))
        else:
            direcao, sev, _ = res
            nome = nome_baixo if direcao == "baixo" else nome_alto
            dica = dicas_baixo if direcao == "baixo" else dicas_alto
            txt = f"{nome}: {val} {unidade}  (ref {lo}–{hi})"
            if dica:
                txt += f" → {dica}"
            achados.append(Achado(parametro, sev, txt))

    if v.Na is not None:
        lo, hi = ref["Na"]
        add("Sódio", v.Na, "mEq/L", lo, hi,
            "HIPONATREMIA", "HIPERNATREMIA",
            "retenção hídrica, vômito/diarreia intensos, Addison",
            "desidratação, diabetes insipidus, hiper-osmolaridade")

    if v.K is not None:
        lo, hi = ref["K"]
        res = classifica(v.K, lo, hi)
        if res[0] == "normal":
            achados.append(Achado("Potássio", "normal", f"Normal: {v.K} mEq/L  (ref {lo}–{hi})"))
        else:
            direcao, sev, _ = res
            if direcao == "baixo":
                if v.K < 2.0:
                    sev = "critico"
                achados.append(Achado("Potássio", sev,
                    f"HIPOCALEMIA: {v.K} mEq/L  (ref {lo}–{hi}) → vômito/diarreia, anorexia, diuréticos, alcalose"))
            else:
                if v.K > 7.0:
                    sev = "critico"
                achados.append(Achado("Potássio", sev,
                    f"HIPERCALEMIA: {v.K} mEq/L  (ref {lo}–{hi}) → IRA/IRC, obstrução uretral, Addison, acidose"))

    if v.Cl is not None:
        lo, hi = ref["Cl"]
        add("Cloreto", v.Cl, "mEq/L", lo, hi,
            "HIPOCLOREMIA", "HIPERCLOREMIA",
            "vômito, alcalose hipoclorêmica",
            "acidose hiperclorêmica, NaCl 0.9% excessivo")

    if v.iCa is not None:
        lo, hi = ref["iCa"]
        add("Ca²⁺ Ionizado", v.iCa, "mmol/L", lo, hi,
            "HIPOCALCEMIA", "HIPERCALCEMIA",
            "hipoparatireoidismo, eclâmpsia, pancreatite, EDTA",
            "neoplasia, hiperparatireoidismo, hipervit. D, granuloma")

    if v.Pi is not None:
        lo, hi = ref["Pi"]
        add("Fósforo", v.Pi, "mg/dL", lo, hi,
            "HIPOFOSFATEMIA", "HIPERFOSFATEMIA",
            "desnutrição, lipidose hepática (gatos), refeeding syndrome",
            "IRC, hipoparatireoidismo, rabdomiólise")

    if v.Mg is not None:
        lo, hi = ref["Mg"]
        add("Magnésio", v.Mg, "mg/dL", lo, hi,
            "HIPOMAGNESEMIA", "HIPERMAGNESEMIA",
            "vômito/diarreia crônica, ITU, diuréticos, má-absorção",
            "IRC avançada, suplementação excessiva")

    if v.lactate is not None:
        lo, hi = ref["lactate"]
        if v.lactate > hi:
            sev = "critico" if v.lactate > 8 else ("grave" if v.lactate > 5 else ("moderado" if v.lactate > 3.5 else "leve"))
            achados.append(Achado("Lactato", sev,
                f"HIPERLACTATEMIA: {v.lactate} mmol/L  (normal <{hi}) → hipoperfusão, hipóxia, sépsis, neoplasia"))
        else:
            achados.append(Achado("Lactato", "normal", f"Normal: {v.lactate} mmol/L"))

    if v.glucose is not None:
        lo, hi = ref["glucose"]
        if v.glucose < lo:
            sev = "critico" if v.glucose < 45 else ("grave" if v.glucose < 55 else ("moderado" if v.glucose < 65 else "leve"))
            achados.append(Achado("Glicose", sev,
                f"HIPOGLICEMIA: {v.glucose} mg/dL  (ref {lo}–{hi}) → insulinoma, sepse, hepatopatia, neonato"))
        elif v.glucose > hi:
            sev = "grave" if v.glucose > 400 else ("moderado" if v.glucose > 250 else "leve")
            achados.append(Achado("Glicose", sev,
                f"HIPERGLICEMIA: {v.glucose} mg/dL  (ref {lo}–{hi}) → DM, estresse, pancreatite, corticóide"))
        else:
            achados.append(Achado("Glicose", "normal", f"Normal: {v.glucose} mg/dL"))

    if v.Hct is not None:
        lo = 25 if v.species == "cat" else 37
        hi = 55 if v.species == "cat" else 60
        if v.Hct < lo:
            sev = "critico" if v.Hct < 12 else ("grave" if v.Hct < 18 else ("moderado" if v.Hct < 22 else "leve"))
            achados.append(Achado("Hematócrito", sev,
                f"ANEMIA: Hct {v.Hct:.0f}%  (ref {lo}–{hi}%) → investigar causa (hemorrágica, hemolítica, não-regenerativa)"))
        elif v.Hct > hi:
            achados.append(Achado("Hematócrito", "moderado",
                f"POLICITEMIA/HEMOCONCENTRAÇÃO: Hct {v.Hct:.0f}%  (ref {lo}–{hi}%)"))
        else:
            achados.append(Achado("Hematócrito", "normal", f"Normal: Hct {v.Hct:.0f}%"))

    return achados


# ──────────────────────────────────────────────────────────────────────────────
# Cálculos de reposição
# ──────────────────────────────────────────────────────────────────────────────

def calcular_reposicoes(v: Valores) -> List[Reposicao]:
    repos = []
    ref = REF[v.species]
    W = v.weight

    # ── Bicarbonato (acidose metabólica) ─────────────────────────────────────
    if v.pH is not None and v.HCO3 is not None:
        pH_lo = ref["pH"][0]
        HCO3_lo = ref["HCO3"][0]
        if v.HCO3 < HCO3_lo and v.pH < pH_lo:
            # Alvo parcial conservador (15 mEq/L) — correção total nunca de uma vez
            alvo = ref["HCO3_target"]
            deficit = (alvo - v.HCO3) * W * 0.3
            dose_ini = deficit / 3  # 1/3 do déficit calculado na 1ª dose
            vol_8_4  = dose_ini     # NaHCO3 8.4% = 1 mEq/mL
            vol_total = vol_8_4 * 2 # diluído 1:1 em NaCl 0.9%
            urgencia = v.pH < 7.10
            tempo = "15-30 min (URGÊNCIA)" if urgencia else "60–120 min"
            repos.append(Reposicao(
                parametro="Bicarbonato (HCO₃⁻)",
                indicacao=f"Acidose metabólica: pH {v.pH:.3f}  /  HCO3 {v.HCO3:.1f} mEq/L",
                calculo=(
                    f"Déficit parcial (alvo HCO3 {alvo} mEq/L) = (alvo−atual) × 0,3 × peso\n"
                    f"  = ({alvo} − {v.HCO3:.1f}) × 0,3 × {W:.1f} = {deficit:.1f} mEq\n"
                    f"  → 1ª dose: {dose_ini:.1f} mEq  (⅓ do déficit)\n"
                    f"  → NaHCO3 8,4% (1 mEq/mL): {vol_8_4:.1f} mL\n"
                    f"  → Diluído 1:1 em NaCl 0,9% → volume final: {vol_total:.0f} mL"
                ),
                taxa=f"IV em {tempo}  —  reavaliação de hemogasometria 1–2 h após",
                atencao=(
                    "⚠ CRITICO: monitorar ECG e ionograma — pH <7,10 pode causar arritmias\n"
                    "  Não corrigir para pH normal de uma vez — risco de alcalose rebote"
                    if urgencia else
                    "Não usar para compensação respiratória — tratar causa primária"
                )
            ))

    # ── Alcalose metabólica ───────────────────────────────────────────────────
    if v.HCO3 is not None and v.pH is not None:
        HCO3_hi = ref["HCO3"][1]
        pH_hi   = ref["pH"][1]
        if v.HCO3 > HCO3_hi and v.pH > pH_hi:
            repos.append(Reposicao(
                parametro="Alcalose Metabólica",
                indicacao=f"HCO3 {v.HCO3:.1f} mEq/L  /  pH {v.pH:.3f}",
                calculo=(
                    "Tratamento etiológico:\n"
                    "1) Hipocloremia → NaCl 0,9% (escolha preferencial)\n"
                    "2) Hipocalemia → KCl (vide seção K⁺)\n"
                    "3) Alcalose por vômito/sonda nasogástrica → omeprazol + NaCl 0,9%\n"
                    "4) Refratária → acetazolamida 5–10 mg/kg VO BID"
                ),
                taxa="Monitorar HCO3 a cada 4–6 h",
                atencao="NÃO usar NaHCO3 — investigar causa (vômito, diurético, pós-hipercapnia)"
            ))

    # ── Potássio ──────────────────────────────────────────────────────────────
    if v.K is not None:
        K_lo, K_hi = ref["K"]

        if v.K < K_lo:
            # Concentração de KCl no fluido por faixa
            if v.K >= 3.0:   conc, urgstr = 20,  "rotina"
            elif v.K >= 2.5: conc, urgstr = 30,  "moderada"
            elif v.K >= 2.0: conc, urgstr = 40,  "urgente"
            elif v.K >= 1.5: conc, urgstr = 60,  "emergência"
            else:             conc, urgstr = 80,  "emergência crítica"

            max_mEqh = 0.5 * W
            # KCl 19,1% = 2,56 mEq/mL
            vol_KCl_por_L = conc / 2.56
            # KCl 10% = 1,34 mEq/mL
            vol_KCl10_por_L = conc / 1.34
            repos.append(Reposicao(
                parametro="Potássio (K⁺) — Hipocalemia",
                indicacao=f"K⁺ = {v.K:.2f} mEq/L  (ref {K_lo}–{K_hi})  —  urgência: {urgstr}",
                calculo=(
                    f"Concentração no fluido: {conc} mEq/L de KCl\n"
                    f"  → KCl 19,1% (2,56 mEq/mL): {vol_KCl_por_L:.1f} mL por litro de fluido\n"
                    f"  → KCl 10% (1,34 mEq/mL): {vol_KCl10_por_L:.1f} mL por litro de fluido\n"
                    f"  → Taxa máxima: 0,5 mEq/kg/h  =  {max_mEqh:.1f} mEq/h"
                ),
                taxa=f"Não ultrapassar 0,5 mEq/kg/h  —  monitorar K⁺ a cada 2–4 h",
                atencao=(
                    "⚠ K⁺ < 2,0 mEq/L: risco de arritmias fatais — UTI e ECG contínuo obrigatório\n"
                    "  NUNCA infundir KCl puro não diluído"
                    if v.K < 2.0 else
                    "Monitorar ECG se K⁺ <2,5 ou infusão acima de 0,3 mEq/kg/h"
                )
            ))

        elif v.K > K_hi:
            if v.K > 7.0:
                repos.append(Reposicao(
                    parametro="Potássio (K⁺) — HIPERCALEMIA GRAVE",
                    indicacao=f"⚠ K⁺ = {v.K:.2f} mEq/L — EMERGÊNCIA CARDÍACA",
                    calculo=(
                        "1) Gluconato de cálcio 10%: 0,5–1,5 mL/kg IV lento (5–10 min)\n"
                        f"   → Volume: {1.0 * W:.1f} mL  (estabilização de membrana — início em 1–5 min)\n"
                        "2) Insulina regular: 0,25–0,5 U/kg IV  +  Dextrose 50%: 1–2 mL/kg (0,5–1,0 g/kg)\n"
                        f"   → Dextrose 50%: {1.5 * W:.1f} mL IV  (dose intermediária; redistribuição em 20–30 min)\n"
                        "3) NaHCO3 (se acidose concomitante): reduz K⁺ por alcalinização\n"
                        "4) Salina hipertônica 7,5%: se bradicardia/colapso\n"
                        "5) Considerar diálise peritoneal se causa renal irreversível"
                    ),
                    taxa="URGÊNCIA — ECG contínuo — reavaliação a cada 30 min",
                    atencao="⚠ RISCO DE PARADA CARDÍACA — iniciar tratamento simultaneamente ao diagnóstico"
                ))
            else:
                repos.append(Reposicao(
                    parametro="Potássio (K⁺) — Hipercalemia",
                    indicacao=f"K⁺ = {v.K:.2f} mEq/L  (ref {K_lo}–{K_hi})",
                    calculo=(
                        "1) Fluido ISENTO de K⁺ (NaCl 0,9% ou Ringer sem K⁺)\n"
                        "2) Investigar causa: IRA, obstrução uretral, hipoadrenocorticismo, acidose\n"
                        "3) Se K⁺ > 6,5 com alterações de ECG → gluconato de cálcio 10%: 0,5 mL/kg IV"
                    ),
                    taxa="Monitorar K⁺ a cada 2–4 h",
                    atencao="Evitar fluidos com KCl — monitorar ECG continuamente"
                ))

    # ── Sódio ─────────────────────────────────────────────────────────────────
    if v.Na is not None:
        Na_lo, Na_hi = ref["Na"]
        Na_alvo = ref["Na_target"]

        if v.Na < Na_lo:
            deficit_Na = (Na_alvo - v.Na) * 0.6 * W   # mEq
            vol_NaCl09 = deficit_Na / 154 * 1000       # mL (NaCl 0,9% = 154 mEq/L)
            tx_max_h   = 0.5  # mEq/L/h
            h_min      = (Na_alvo - v.Na) / tx_max_h
            repos.append(Reposicao(
                parametro="Sódio (Na⁺) — Hiponatremia",
                indicacao=f"Na⁺ = {v.Na:.1f} mEq/L  (ref {Na_lo}–{Na_hi})",
                calculo=(
                    f"Déficit de Na⁺ = (alvo − atual) × 0,6 × peso\n"
                    f"  = ({Na_alvo:.0f} − {v.Na:.1f}) × 0,6 × {W:.1f} = {deficit_Na:.1f} mEq\n"
                    f"  → NaCl 0,9%: ~{vol_NaCl09:.0f} mL para correção gradual\n"
                    "  → Se sintomática com sinais neurológicos: NaCl hipertônico 3–7,5%:\n"
                    "    2–6 mL/kg em 10–15 min"
                ),
                taxa=(
                    f"Máximo 0,5 mEq/L/h e ≤10–12 mEq/L nas primeiras 24 h\n"
                    f"  → Correção em pelo menos {h_min:.0f} h  —  monitorar Na⁺ a cada 2–4 h"
                ),
                atencao="Correção rápida → mielinólise osmótica — NUNCA ultrapassar 12 mEq/L/24 h"
            ))

        elif v.Na > Na_hi:
            FWD = 0.6 * W * (v.Na / Na_alvo - 1)   # litros
            h_min = (v.Na - Na_alvo) / 0.5
            repos.append(Reposicao(
                parametro="Sódio (Na⁺) — Hipernatremia",
                indicacao=f"Na⁺ = {v.Na:.1f} mEq/L  (ref {Na_lo}–{Na_hi})",
                calculo=(
                    f"Déficit de água livre = 0,6 × peso × (Na_atual/Na_alvo − 1)\n"
                    f"  = 0,6 × {W:.1f} × ({v.Na:.1f}/{Na_alvo:.0f} − 1) = {FWD:.2f} L ({FWD*1000:.0f} mL)\n"
                    f"  → SG 5% (água livre) ou NaCl 0,45%\n"
                    f"  → Acrescentar às necessidades de manutenção e perdas em curso"
                ),
                taxa=(
                    f"Redução máxima: 0,5 mEq/L/h  (≤10–12 mEq/L/24 h)\n"
                    f"  → Tempo mínimo de correção: ~{h_min:.0f} h  —  monitorar Na⁺ a cada 2 h"
                ),
                atencao="Correção rápida → edema cerebral e herniação — atenção especial se crónica (>48 h)"
            ))

    # ── Cálcio Ionizado ───────────────────────────────────────────────────────
    if v.iCa is not None:
        iCa_lo, iCa_hi = ref["iCa"]

        if v.iCa < iCa_lo:
            vol_gluconato = 0.5 * W   # mL/kg — dose baixa a moderada
            repos.append(Reposicao(
                parametro="Cálcio Ionizado — Hipocalcemia",
                indicacao=f"iCa²⁺ = {v.iCa:.2f} mmol/L  (ref {iCa_lo:.2f}–{iCa_hi:.2f})",
                calculo=(
                    f"Gluconato de cálcio 10% (0,465 mEq Ca/mL):\n"
                    f"  Dose: 0,5–1,5 mL/kg  →  {vol_gluconato:.1f}–{vol_gluconato*3:.1f} mL total\n"
                    f"  Diluir 1:1 em NaCl 0,9% → {vol_gluconato*2:.0f}–{vol_gluconato*6:.0f} mL\n"
                    f"  ─ OU ─\n"
                    f"  CaCl2 10% (mais biodisponível, mais cáustico): 5–15 mg/kg IV\n"
                    f"  → {5*W:.0f}–{15*W:.0f} mg  total  (cautela em acesso periférico)"
                ),
                taxa="Infundir em 10–20 min com monitoração de ECG",
                atencao="⚠ Bradicardia durante infusão → reduzir velocidade ou suspender temporariamente"
            ))

        elif v.iCa > iCa_hi:
            repos.append(Reposicao(
                parametro="Cálcio Ionizado — Hipercalcemia",
                indicacao=f"iCa²⁺ = {v.iCa:.2f} mmol/L  (ref {iCa_lo:.2f}–{iCa_hi:.2f})",
                calculo=(
                    "1) NaCl 0,9%: fluidoterapia 2–3× manutenção (diluição e calciúria)\n"
                    "2) Furosemida 1–2 mg/kg IV após reidratação (calciúrese)\n"
                    f"   → {1.5 * W:.1f} mg IV (dose 1,5 mg/kg)\n"
                    "3) Prednisolona 1–2 mg/kg VO/IV se hipercalcemia maligna/granulomatosa\n"
                    "4) Investigar: neoplasia, hiperparatireoidismo, hipervit. D, calcipotriol"
                ),
                taxa="Monitorar iCa a cada 4–6 h",
                atencao="NÃO usar fluidos com Ca²⁺ (Ringer Lactato) — evitar vitamina D"
            ))

    # ── Fósforo ───────────────────────────────────────────────────────────────
    if v.Pi is not None:
        Pi_lo, Pi_hi = ref["Pi"]
        if v.Pi < Pi_lo:
            repos.append(Reposicao(
                parametro="Fósforo (Pi) — Hipofosfatemia",
                indicacao=f"Pi = {v.Pi:.1f} mg/dL  (ref {Pi_lo}–{Pi_hi})",
                calculo=(
                    "Leve (>2,0 mg/dL): suplementação oral — fosfato de sódio/potássio VO\n"
                    "Moderada/grave (<2,0 mg/dL):\n"
                    "  Fosfato de potássio: 0,03–0,12 mmol/kg/h IV (infusão lenta)\n"
                    f"  Dose inicial: 0,06 mmol/kg/h  →  {0.06 * W:.2f} mmol/h\n"
                    "  Diluir em NaCl 0,9% ou SG 5% — evitar cálcio no mesmo acesso"
                ),
                taxa="Monitorar Pi, Ca²⁺ e K⁺ a cada 4–6 h",
                atencao="Atenção em lipidose hepática felina e refeeding syndrome — risco de morte súbita"
            ))

    # ── Magnésio ──────────────────────────────────────────────────────────────
    if v.Mg is not None:
        Mg_lo, _ = ref["Mg"]
        if v.Mg < Mg_lo:
            repos.append(Reposicao(
                parametro="Magnésio (Mg²⁺) — Hipomagnesemia",
                indicacao=f"Mg²⁺ = {v.Mg:.1f} mg/dL  (ref {Mg_lo}–{REF[v.species]['Mg'][1]:.1f})",
                calculo=(
                    "Sulfato de magnésio (MgSO4 50%): 0,75–1,0 mEq/kg/dia IV\n"
                    f"  → MgSO4 50% (4 mEq/mL): {0.875 * W / 4:.1f} mL/dia\n"
                    "  Diluir em NaCl 0,9% ou SG 5% — infusão lenta"
                ),
                taxa="Infundir em 24 h  —  pode prolongar meia-vida de outros fármacos",
                atencao="Hipomagnesemia frequentemente coexiste com hipocalemia refratária"
            ))

    # ── Glicose ───────────────────────────────────────────────────────────────
    if v.glucose is not None:
        glu_lo, _ = ref["glucose"]
        if v.glucose < glu_lo:
            if v.glucose < 55:
                repos.append(Reposicao(
                    parametro="Glicose — Hipoglicemia Grave",
                    indicacao=f"Glicose = {v.glucose:.0f} mg/dL — URGÊNCIA",
                    calculo=(
                        f"Dextrose 50% (D50%): 0,5–1,0 mL/kg IV bolus\n"
                        f"  → Volume: {0.75 * W:.1f} mL IV (dose 0,75 mL/kg)\n"
                        "  → Diluir 1:2 a 1:4 em NaCl 0,9%\n"
                        "  Manutenção (concentração): D5% = 100 mL de D50% + 900 mL de fluido (1 L final)"
                    ),
                    taxa="Bolus em 2–5 min  —  medir glicemia em 15 e 30 min após",
                    atencao="Investigar causa: insulinoma, sepse, hepatopatia grave, xylitol (cão)"
                ))
            else:
                repos.append(Reposicao(
                    parametro="Glicose — Hipoglicemia Leve/Moderada",
                    indicacao=f"Glicose = {v.glucose:.0f} mg/dL",
                    calculo=(
                        f"Suplementação no fluido de manutenção:\n"
                        "  D5%: 100 mL de D50% + 900 mL de fluido (1 L final)\n"
                        "  D2,5%: 50 mL de D50% + 950 mL de fluido (1 L final)"
                    ),
                    taxa="Gotejamento contínuo  —  monitorar glicemia a cada 1–2 h",
                    atencao="Investigar causa e corrigir"
                ))

    return repos


# ──────────────────────────────────────────────────────────────────────────────
# Entrada de dados
# ──────────────────────────────────────────────────────────────────────────────

def pedir_float(rotulo: str, unidade: str = "", obrigatorio: bool = False,
                vmin: float = None, vmax: float = None) -> Optional[float]:
    unid_str = f" [{unidade}]" if unidade else ""
    opc_str  = "" if obrigatorio else "  (Enter para pular)"
    while True:
        raw = input(f"  {rotulo}{unid_str}{opc_str}: ").strip()
        if not raw:
            if obrigatorio:
                print("    ⚠  Campo obrigatório.")
                continue
            return None
        try:
            v = float(raw.replace(",", "."))
            if vmin is not None and v < vmin:
                print(f"    ⚠  Mínimo: {vmin}")
                continue
            if vmax is not None and v > vmax:
                print(f"    ⚠  Máximo: {vmax}")
                continue
            return v
        except ValueError:
            print("    ⚠  Digite um número válido (ex: 7.35 ou 7,35).")


# ──────────────────────────────────────────────────────────────────────────────
# Exibição — Rich
# ──────────────────────────────────────────────────────────────────────────────

SEV_RICH = {
    "normal":   ("[green]✓ Normal[/green]",   "green"),
    "leve":     ("[yellow]⚡ Leve[/yellow]",   "yellow"),
    "moderado": ("[orange3]⚠ Moderado[/orange3]", "orange3"),
    "grave":    ("[red]✗ Grave[/red]",         "red"),
    "critico":  ("[bold red]☠ CRÍTICO[/bold red]", "bold red"),
    "info":     ("[cyan]ℹ Info[/cyan]",        "cyan"),
}

SEV_PLAIN = {
    "normal":  "[OK]     ",
    "leve":    "[LEVE]   ",
    "moderado":"[MODER]  ",
    "grave":   "[GRAVE]  ",
    "critico": "[CRITICO]",
    "info":    "[INFO]   ",
}


def exibir_achados_rich(titulo: str, achados: List[Achado]):
    t = Table(title=titulo, box=box.ROUNDED, border_style="blue",
              show_header=True, header_style="bold")
    t.add_column("Parâmetro", min_width=22)
    t.add_column("Severidade", min_width=14)
    t.add_column("Achado")
    for a in achados:
        label, _ = SEV_RICH.get(a.severidade, (a.severidade, "white"))
        t.add_row(a.categoria, label, a.mensagem)
    console.print(t)
    console.print()


def exibir_reposicoes_rich(repos: List[Reposicao]):
    if not repos:
        console.print("[green]✓  Nenhuma reposição urgente indicada neste momento.[/green]\n")
        return
    console.print(Rule("[bold yellow]REPOSIÇÕES INDICADAS[/bold yellow]"))
    console.print()
    for r in repos:
        txt = Text()
        txt.append("Indicação:\n", style="bold cyan")
        txt.append(f"  {r.indicacao}\n\n")
        txt.append("Cálculo / Dose:\n", style="bold green")
        for linha in r.calculo.split("\n"):
            txt.append(f"  {linha}\n")
        txt.append("\nTaxa / Velocidade:\n", style="bold blue")
        for linha in r.taxa.split("\n"):
            txt.append(f"  {linha}\n")
        if r.atencao:
            txt.append("\nAtenção:\n", style="bold red")
            for linha in r.atencao.split("\n"):
                txt.append(f"  {linha}\n")
        console.print(Panel(txt,
            title=f"[bold yellow]{r.parametro}[/bold yellow]",
            border_style="yellow", padding=(0, 1)))
        console.print()


def exibir_referencia_rich(species: str):
    r = REF[species]
    s = "dog"
    t = Table(title="Referências — Hemogasometria Venosa", box=box.SIMPLE_HEAVY,
              border_style="dim", header_style="bold dim")
    t.add_column("Parâmetro")
    t.add_column("Cão",  justify="center")
    t.add_column("Gato", justify="center")
    linhas = [
        ("pH",                "7,32 – 7,40",   "7,28 – 7,41"),
        ("pCO₂ (mmHg)",       "35 – 50",       "33 – 45"),
        ("HCO₃⁻ (mEq/L)",    "18 – 24",       "17 – 22"),
        ("BE (mEq/L)",        "−4 a +4",       "−4 a +4"),
        ("Na⁺ (mEq/L)",       "140 – 155",     "149 – 160"),
        ("K⁺ (mEq/L)",        "3,5 – 5,5",     "3,5 – 5,0"),
        ("Cl⁻ (mEq/L)",       "105 – 115",     "112 – 129"),
        ("iCa²⁺ (mmol/L)",    "1,12 – 1,40",   "1,12 – 1,40"),
        ("Fósforo (mg/dL)",   "2,9 – 6,2",     "3,0 – 7,0"),
        ("Magnésio (mg/dL)",  "1,7 – 2,7",     "1,8 – 2,9"),
        ("Lactato (mmol/L)",  "< 2,5",         "< 2,5"),
        ("Glicose (mg/dL)",   "70 – 120",      "65 – 130"),
        ("Hematócrito (%)",   "37 – 60",       "25 – 55"),
        ("Ânion Gap (mEq/L)", "12 – 24",       "13 – 27"),
    ]
    for p, d, c in linhas:
        t.add_row(p, f"[{'bold' if species == 'dog' else 'dim'}]{d}",
                     f"[{'bold' if species == 'cat' else 'dim'}]{c}")
    console.print(t)


def exibir_literatura_rich():
    refs = (
        "1) AAHA. 2024 AAHA Fluid Therapy Guidelines for Dogs and Cats\n"
        "2) DiBartola SP. Fluid, Electrolyte, and Acid-Base Disorders in Small Animal Practice\n"
        "3) Hopper K. referências de terapia intensiva veterinária para distúrbios ácido-base e eletrólitos"
    )
    console.print(Panel(refs, title="[bold dim]Literatura de Referência[/bold dim]", border_style="dim"))


# ──────────────────────────────────────────────────────────────────────────────
# Exibição — texto puro (fallback)
# ──────────────────────────────────────────────────────────────────────────────

def exibir_achados_plain(titulo: str, achados: List[Achado]):
    print(f"\n{'─'*70}")
    print(f"  {titulo}")
    print(f"{'─'*70}")
    for a in achados:
        s = SEV_PLAIN.get(a.severidade, "         ")
        print(f"  {s} {a.categoria}: {a.mensagem}")


def exibir_reposicoes_plain(repos: List[Reposicao]):
    if not repos:
        print("\n[OK] Nenhuma reposição urgente indicada.\n")
        return
    print(f"\n{'═'*70}")
    print("  REPOSIÇÕES INDICADAS")
    print(f"{'═'*70}")
    for r in repos:
        print(f"\n  ── {r.parametro} ──")
        print(f"  Indicação : {r.indicacao}")
        print(f"  Cálculo   : {r.calculo}")
        print(f"  Taxa      : {r.taxa}")
        if r.atencao:
            print(f"  ATENÇÃO   : {r.atencao}")


def exibir_literatura_plain():
    print(f"\n{'─'*70}")
    print("  LITERATURA DE REFERÊNCIA")
    print(f"{'─'*70}")
    print("  1) AAHA. 2024 AAHA Fluid Therapy Guidelines for Dogs and Cats")
    print("  2) DiBartola SP. Fluid, Electrolyte, and Acid-Base Disorders in Small Animal Practice")
    print("  3) Hopper K. referências de terapia intensiva veterinária para distúrbios ácido-base e eletrólitos")


# ──────────────────────────────────────────────────────────────────────────────
# Loop principal
# ──────────────────────────────────────────────────────────────────────────────

def coletar_valores() -> Valores:
    print()
    # Espécie
    while True:
        esp = input("  Espécie  [1] Cão  [2] Gato: ").strip()
        if esp == "1":
            species = "dog"; break
        elif esp == "2":
            species = "cat"; break
        print("    ⚠  Digite 1 ou 2.")

    nome = "Cão" if species == "dog" else "Gato"
    weight = pedir_float("Peso", "kg", obrigatorio=True, vmin=0.1, vmax=150)

    print(f"\n  Paciente: {nome}  •  {weight:.2f} kg")
    if HAS_RICH:
        console.print("  [dim]Preencha os valores disponíveis. Enter pula o campo.[/dim]")
    else:
        print("  Preencha os valores disponíveis. Enter pula o campo.")

    print("\n  ── Hemogasometria ──────────────────────────────────")
    pH    = pedir_float("pH",           obrigatorio=True, vmin=6.5,  vmax=7.9)
    pCO2  = pedir_float("pCO2",  "mmHg",               vmin=5,    vmax=150)
    HCO3  = pedir_float("HCO3",  "mEq/L",              vmin=1,    vmax=60)
    BE    = pedir_float("BE",    "mEq/L",              vmin=-30,  vmax=30)

    print("\n  ── Eletrólitos ──────────────────────────────────────")
    Na    = pedir_float("Na⁺",   "mEq/L",              vmin=100,  vmax=210)
    K     = pedir_float("K⁺",    "mEq/L",              vmin=1.0,  vmax=12)
    Cl    = pedir_float("Cl⁻",   "mEq/L",              vmin=60,   vmax=170)
    iCa   = pedir_float("Ca²⁺ ionizado", "mmol/L",     vmin=0.1,  vmax=5)
    Pi    = pedir_float("Fósforo (Pi)", "mg/dL",        vmin=0.1,  vmax=25)
    Mg    = pedir_float("Magnésio",     "mg/dL",        vmin=0.1,  vmax=10)

    print("\n  ── Metabólitos / Hemograma ──────────────────────────")
    lact  = pedir_float("Lactato", "mmol/L",            vmin=0,    vmax=30)
    gluc  = pedir_float("Glicose", "mg/dL",             vmin=0,    vmax=1500)
    Hct   = pedir_float("Hematócrito", "%",             vmin=1,    vmax=80)
    alb   = pedir_float("Albumina (para AG corrigido)", "g/dL",    vmin=0.1, vmax=8)

    return Valores(
        species=species, weight=weight,
        pH=pH, pCO2=pCO2, HCO3=HCO3, BE=BE,
        Na=Na, K=K, Cl=Cl, iCa=iCa, Pi=Pi, Mg=Mg,
        lactate=lact, glucose=gluc, Hct=Hct, albumin=alb,
    )


def run():
    if HAS_RICH:
        t = Text()
        t.append("  HEMOGASOMETRIA VENOSA\n", style="bold cyan")
        t.append("  Interpretação e Reposição — Cães e Gatos\n", style="cyan")
        t.append("  Nefrologia / Terapia Intensiva Veterinária", style="dim cyan")
        console.print(Panel(t, border_style="cyan"))
    else:
        print("\n" + "="*70)
        print("  HEMOGASOMETRIA VENOSA — Cães e Gatos")
        print("="*70)

    v = coletar_valores()
    avisos = validar_valores(v)
    nome = "Cão" if v.species == "dog" else "Gato"
    if avisos:
        if HAS_RICH:
            console.print(
                Panel(
                    "\n".join(f"• {a}" for a in avisos)
                    + "\n\nOs valores foram mantidos para análise (casos graves podem sair da faixa habitual).",
                    title="[bold yellow]Aviso — valores extremos[/bold yellow]",
                    border_style="yellow",
                )
            )
        else:
            print("\n[AVISO] Valores extremos detectados:")
            for a in avisos:
                print(f"  - {a}")
            print("  (Análise continuada; casos graves podem sair da faixa habitual.)\n")

    achados_ab  = analisar_acido_base(v)
    achados_ele = analisar_eletrolitos(v)
    repos       = calcular_reposicoes(v)

    if HAS_RICH:
        console.print()
        console.print(Rule(f"[bold cyan]RESULTADO — {nome.upper()}  {v.weight:.1f} kg[/bold cyan]"))
        console.print()
        exibir_achados_rich("Equilíbrio Ácido-Base", achados_ab)
        exibir_achados_rich("Eletrólitos e Metabólitos", achados_ele)
        exibir_reposicoes_rich(repos)
        exibir_referencia_rich(v.species)
        exibir_literatura_rich()
        console.print("\n[dim]⚕  Ferramenta de auxílio clínico — não substitui o julgamento veterinário[/dim]\n")
    else:
        print(f"\n{'='*70}")
        print(f"  RESULTADO — {nome.upper()}  {v.weight:.1f} kg")
        print(f"{'='*70}")
        exibir_achados_plain("EQUILÍBRIO ÁCIDO-BASE", achados_ab)
        exibir_achados_plain("ELETRÓLITOS E METABÓLITOS", achados_ele)
        exibir_reposicoes_plain(repos)
        exibir_literatura_plain()
        print("\n[Ferramenta de auxílio — não substitui julgamento clínico]\n")

    print()
    novamente = input("Analisar outro paciente? [s/N]: ").strip().lower()
    if novamente in ("s", "sim", "y", "yes"):
        run()


if __name__ == "__main__":
    try:
        run()
    except ValueError as exc:
        print(f"\n⚠ {exc}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSaindo...\n")
        sys.exit(0)
