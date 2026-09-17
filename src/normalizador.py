import re
from pathlib import Path

from setores import identificar_setor
from nomes import normalizar_nome
from logger import log_warning
from datas import (
    completar_periodo,
    formatar_periodo,
    extrair_periodo,
)

def normalizar_arquivo(caminho: Path) -> str | None:
    """
    Recebe o caminho de um PDF e tenta gerar o novo nome.
    """

    nome_original = caminho.stem

    # Identifica e remove o prefixo do arquivo
    resultado_portaria = re.match(
        r"^\s*(Portaria\s+n[ºo°]?\s*\d+\s*-\s*\d{4})\s*-\s*([^-]+?)\s*-\s*(.*)$",
        nome_original,
        flags=re.IGNORECASE
    )

    if resultado_portaria is None:
        log_warning(f"Portaria não identificada: {caminho.name}")
        return None

    portaria = resultado_portaria.group(1)
    tipo = resultado_portaria.group(2).strip().upper()
    texto = resultado_portaria.group(3).strip()

    # Substitui underscore por hífen    
    texto = texto.replace("_", "-")

    # Identifica a marcação de contrato
    eh_contrato = bool(
        re.search(r"\s+(?:CONT|CONTRATO)\s+(?=-)", texto, re.IGNORECASE)
    )

    # Remove a marcação do texto para facilitar a identificação do nome
    if eh_contrato:
        texto = re.sub(
            r"\s+(?:CONT|CONTRATO)\s+(?=-)",
            " ",
            texto,
            flags=re.IGNORECASE
        )

    # converte espaços multiplicados em único
    texto = re.sub(r"\s+", " ", texto).strip()

    resultado_periodo = extrair_periodo(texto)

    if resultado_periodo is None:
        log_warning(
            f"Não foi possível identificar o período: {caminho.name}"
        )
        return None

    inicio, fim, inicio_pos, fim_pos = resultado_periodo

    # Remove exatamente o período encontrado
    texto_sem_periodo = texto[:inicio_pos] + texto[fim_pos:]

    # Limpa separadores duplicados
    texto_sem_periodo = re.sub(
        r"\s*[-–—]\s*",
        " - ",
        texto_sem_periodo
    )

    partes = [
        parte.strip()
        for parte in texto_sem_periodo.split(" - ")
        if parte.strip()
    ]

    if not partes:
        log_warning(
            f"Não foi possível identificar nome/setor: {caminho.name}"
        )
        return None

    resultado_nome_setor = identificar_setor(partes)

    if resultado_nome_setor is None:
        log_warning(
            f"Não foi possível identificar nome/setor: {caminho.name}"
        )
        return None

    nome, setor = resultado_nome_setor

    nome = normalizar_nome(nome)
    setor = setor.upper().strip()
    
    inicio, fim = completar_periodo(inicio, fim)

    periodo = formatar_periodo(inicio, fim)

    if eh_contrato:
        return f"{portaria} - {tipo} - {nome} - {setor} - {periodo} - CONTRATO.pdf"

    return f"{portaria} - {tipo} - {nome} - {setor} - {periodo}.pdf"