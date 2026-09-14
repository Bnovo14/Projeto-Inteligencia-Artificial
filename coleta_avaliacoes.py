# -*- coding: utf-8 -*-
"""
===============================================================================
UNIVERSIDADE PRESBITERIANA MACKENZIE
Faculdade de Computação e Informática
Disciplina: Inteligência Artificial - 7ºJ SI - Noite
Professor: Prof. Dr. Leandro Zerbinatti

PROJETO: Classificação automática de reclamações de usuários de aplicativos
         de pagamento digital (PIX / carteiras digitais)

INTEGRANTES:
    Bruno Cruz Bregion Novo - RA 10409538 - 10409538@mackenzista.com.br
    Vinicius Silva Almeida  - RA 10409019 - 10409019@mackenzista.com.br
    Gabriel Bello           - RA 10416808 - 10416808@mackenzista.com.br

SÍNTESE DO CONTEÚDO DO ARQUIVO:
    Script responsável pela COLETA (captura própria) do dataset do projeto.
    Utiliza a biblioteca google-play-scraper para extrair as avaliações
    públicas de seis aplicativos brasileiros de pagamento digital na Google
    Play Store. Para cada avaliação são capturados: aplicativo de origem, nota
    atribuída (1 a 5), texto livre da avaliação, data de publicação, número de
    curtidas, versão do aplicativo e indicação de resposta da empresa.

    O nome do usuário é descartado e substituído por identificador
    pseudonimizado (hash SHA-256 truncado), de modo que o dataset publicado não
    contenha dados pessoais diretamente identificáveis, em atenção à Lei nº
    13.709/2018 (LGPD).

    A execução é incremental: caso já exista arquivo de coleta anterior, os
    novos registros são consolidados aos existentes, com remoção de duplicatas
    por identificador de avaliação. Isso permite reexecutar o script para
    ampliar o conjunto ou para capturar um aplicativo que tenha falhado, sem
    perder a coleta já realizada.

HISTÓRICO DE ALTERAÇÕES:
    2026-09-08 | Bruno Cruz Bregion Novo | Criação do script de coleta.
    2026-09-08 | Bruno Cruz Bregion Novo | Correção do identificador de pacote
                                           do aplicativo Nubank, que estava
                                           incorreto e resultou em zero
                                           registros na primeira execução. O
                                           valor correto é com.nu.production.
    2026-09-10 | Bruno Cruz Bregion Novo | Unificação do script de coleta
                                           complementar neste arquivo, com
                                           adição do modo incremental e do
                                           parâmetro de coleta seletiva.
    2026-09-14 | Bruno Cruz Bregion Novo | Tratamento de argumentos desconhecidos,
                                           permitindo a execução do script
                                           também de dentro de uma célula de
                                           notebook (Jupyter/Colab).
===============================================================================
"""

import argparse
import csv
import hashlib
import os
import sys
import time
from datetime import datetime

try:
    from google_play_scraper import Sort, reviews
except ImportError:
    sys.exit(
        "Biblioteca ausente. Instale com:\n"
        "    pip install google-play-scraper\n"
    )

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Aplicativos-alvo da coleta.
# O identificador é o valor do parâmetro "id=" na URL do app na Play Store.
# Ex.: https://play.google.com/store/apps/details?id=com.picpay  ->  com.picpay
APLICATIVOS = {
    "PicPay":       "com.picpay",
    "Mercado Pago": "com.mercadopago.wallet",
    "Nubank":       "com.nu.production",
    "PagBank":      "br.com.uol.ps.myaccount",
    "Banco Inter":  "br.com.intermedium",
    "RecargaPay":   "com.recarga.recarga",
}

META_POR_APP = 4000   # quantidade-alvo de avaliações por aplicativo
LOTE = 200            # registros por requisição (máximo aceito pela API)
PAUSA = 1.5           # segundos entre requisições, para evitar bloqueio

PASTA_SAIDA = "dados"
ARQUIVO_SAIDA = os.path.join(PASTA_SAIDA, "avaliacoes_apps_pagamento.csv")

COLUNAS = [
    "id_avaliacao",
    "aplicativo",
    "usuario_pseudonimizado",
    "nota",
    "texto",
    "data",
    "curtidas",
    "versao_app",
    "houve_resposta_empresa",
]


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def pseudonimizar(nome_usuario: str) -> str:
    """Converte o nome do usuário em hash irreversível de 12 caracteres.

    Preserva a capacidade de identificar avaliações repetidas do mesmo autor
    sem expor a identidade da pessoa no dataset publicado.
    """
    if not nome_usuario:
        return "anonimo"
    return hashlib.sha256(nome_usuario.encode("utf-8")).hexdigest()[:12]


def coletar_app(nome_app: str, app_id: str, meta: int) -> list:
    """Coleta avaliações de um aplicativo, paginando até atingir a meta.

    Retorna lista de dicionários já no formato final das colunas.
    """
    coletadas, token, pagina = [], None, 0

    while len(coletadas) < meta:
        pagina += 1
        try:
            resultado, token = reviews(
                app_id,
                lang="pt",
                country="br",
                sort=Sort.NEWEST,
                count=LOTE,
                continuation_token=token,
            )
        except Exception as erro:
            print(f"   [!] Falha na página {pagina} de {nome_app}: {erro}")
            break

        if not resultado:
            print(f"   [i] Sem mais avaliações disponíveis para {nome_app}.")
            break

        for item in resultado:
            data = item.get("at")
            coletadas.append({
                "id_avaliacao": item.get("reviewId", ""),
                "aplicativo": nome_app,
                "usuario_pseudonimizado": pseudonimizar(item.get("userName", "")),
                "nota": item.get("score", ""),
                "texto": (item.get("content") or "").replace("\n", " ").strip(),
                "data": data.strftime("%Y-%m-%d %H:%M:%S") if data else "",
                "curtidas": item.get("thumbsUpCount", 0),
                "versao_app": item.get("reviewCreatedVersion") or "",
                "houve_resposta_empresa": 1 if item.get("replyContent") else 0,
            })

        print(f"   pagina {pagina:>3} | acumulado: {len(coletadas):>5}")

        if token is None:
            print(f"   [i] Fim da paginação para {nome_app}.")
            break

        time.sleep(PAUSA)

    return coletadas[:meta]


def carregar_existente(caminho: str) -> list:
    """Lê o arquivo de uma coleta anterior, se houver."""
    if not os.path.exists(caminho):
        return []

    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        registros = list(csv.DictReader(arquivo))

    apps = sorted({r["aplicativo"] for r in registros})
    print(f"Coleta anterior encontrada: {len(registros):,} registros".replace(",", "."))
    print(f"Aplicativos ja presentes: {', '.join(apps)}\n")
    return registros


def consolidar(anteriores: list, novos: list) -> tuple:
    """Une as duas listas removendo duplicatas por identificador de avaliação."""
    consolidado, vistos = [], set()
    for registro in anteriores + novos:
        chave = registro["id_avaliacao"]
        if chave and chave in vistos:
            continue
        vistos.add(chave)
        consolidado.append({coluna: registro.get(coluna, "") for coluna in COLUNAS})

    duplicadas = len(anteriores) + len(novos) - len(consolidado)
    return consolidado, duplicadas


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main():
    analisador = argparse.ArgumentParser(
        description="Coleta avaliacoes de aplicativos de pagamento na Google Play Store."
    )
    analisador.add_argument(
        "--apps", nargs="+", metavar="NOME", default=None,
        help="coletar apenas os aplicativos indicados (padrao: todos). "
             "Ex.: --apps Nubank PicPay",
    )
    analisador.add_argument(
        "--meta", type=int, default=META_POR_APP,
        help=f"quantidade de avaliacoes por aplicativo (padrao: {META_POR_APP})",
    )
    # parse_known_args (em vez de parse_args) ignora argumentos desconhecidos.
    # Isso permite que o script seja executado tanto pela linha de comando
    # quanto colado dentro de uma célula de notebook (Jupyter/Colab), ambiente
    # que injeta argumentos próprios como "-f kernel.json".
    argumentos, ignorados = analisador.parse_known_args()
    if ignorados:
        print(f"[i] Argumentos ignorados: {' '.join(ignorados)}\n")

    if argumentos.apps:
        desconhecidos = [a for a in argumentos.apps if a not in APLICATIVOS]
        if desconhecidos:
            sys.exit(f"[ERRO] Aplicativo(s) nao configurado(s): {', '.join(desconhecidos)}\n"
                     f"       Disponiveis: {', '.join(APLICATIVOS)}")
        alvos = {nome: APLICATIVOS[nome] for nome in argumentos.apps}
    else:
        alvos = APLICATIVOS

    inicio = datetime.now()
    print("=" * 70)
    print("COLETA DE AVALIACOES - APLICATIVOS DE PAGAMENTO DIGITAL")
    print(f"Inicio: {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    anteriores = carregar_existente(ARQUIVO_SAIDA)

    novos, falhas = [], []
    for nome_app, app_id in alvos.items():
        print(f">> {nome_app}  ({app_id})")
        registros = coletar_app(nome_app, app_id, argumentos.meta)
        if not registros:
            falhas.append((nome_app, app_id))
        novos.extend(registros)
        print()

    if not novos and not anteriores:
        sys.exit("[ERRO] Nenhuma avaliacao coletada e nenhuma coleta anterior encontrada.")

    consolidado, duplicadas = consolidar(anteriores, novos)

    with open(ARQUIVO_SAIDA, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(consolidado)

    contagem = {}
    for registro in consolidado:
        contagem[registro["aplicativo"]] = contagem.get(registro["aplicativo"], 0) + 1

    print("=" * 70)
    print("RESUMO DA COLETA")
    print("=" * 70)
    for nome_app in sorted(contagem):
        print(f"  {nome_app:<15} {contagem[nome_app]:>6} avaliacoes")
    print("-" * 70)
    print(f"  {'Coleta anterior':<15} {len(anteriores):>6}")
    print(f"  {'Novos registros':<15} {len(novos):>6}")
    print(f"  {'Duplicadas':<15} {duplicadas:>6}")
    print(f"  {'Total final':<15} {len(consolidado):>6}")

    if falhas:
        print("\n[!] Nenhum registro retornado para:")
        for nome_app, app_id in falhas:
            print(f"    {nome_app} ({app_id})")
        print("    Confira o identificador abrindo a URL no navegador:")
        print("    https://play.google.com/store/apps/details?id=<identificador>")

    print(f"\nArquivo gerado: {ARQUIVO_SAIDA}")
    print(f"Duracao: {datetime.now() - inicio}")
    print("=" * 70)


if __name__ == "__main__":
    main()