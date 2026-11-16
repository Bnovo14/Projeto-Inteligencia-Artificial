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

SÍNTESE DO CONTEÚDO DO ARQUIVO:
    Implementa a ROTULAGEM FRACA (weak supervision) do corpus de modelagem.
    O conjunto capturado não possui rótulo de categoria na origem, e a
    rotulagem manual integral das 4.211 avaliações seria inviável no prazo do
    projeto. Adota-se, portanto, uma função de rotulagem baseada em regras:
    para cada categoria de problema é definido um conjunto de expressões
    regulares com pesos, e a categoria atribuída é a de maior pontuação
    acumulada no texto da avaliação.

    A escolha por pontuação acumulada, em vez de uma ordem fixa de prioridade
    entre categorias, permite que avaliações que mencionam mais de um tema
    sejam atribuídas àquela com maior evidência textual.

    Os rótulos produzidos aqui são aproximados por construção. A qualidade da
    rotulagem é medida separadamente, por validação manual de uma amostra
    estratificada, cujo resultado serve como conjunto padrão-ouro na avaliação
    dos modelos.

HISTÓRICO DE ALTERAÇÕES:
    2026-11-15 | Bruno Cruz Bregion Novo | Criação do rotulador por regras,
                                           com pesos por expressão e geração
                                           da amostra de validação manual.
===============================================================================
"""

import re
import unicodedata

# =============================================================================
# CATEGORIAS E REGRAS
# =============================================================================
# Cada categoria possui uma lista de pares (expressão regular, peso).
# Pesos maiores indicam expressões mais específicas da categoria: "biometria"
# é sinal forte de problema de acesso, ao passo que "conta" sozinho é fraco,
# por aparecer em praticamente qualquer reclamação bancária.

CATEGORIAS = {
    "Acesso e autenticacao": [
        # Verbos de acesso aparecem em muitas conjugações e com grafia
        # informal, por isso as expressões usam radicais em vez de formas
        # fechadas: "entra", "entrar", "entrando" são todas capturadas.
        (r"(nao|n|nunca)\s+(estou |to |tou |ta |consigo |consegui |da pra |"
         r"conseguindo |to conseguindo |estou conseguindo )*"
         r"(entra|acessa|acesso|logar|loga|fazer login|abrir a conta|criar (a |minha )?conta|"
         r"cria (a |minha )?conta|terminar o cadastro|concluir o cadastro|finalizar o cadastro)", 5),
        (r"(sem conseguir|nao da pra|impossivel)\s+(entrar|acessar|logar)", 5),
        (r"(biometria|biometrico|reconhecimento facial|leitura facial|selfie|foto do rosto|"
         r"pedindo (toda hora )?meu rosto)", 5),
        (r"(conta|acesso|cpf)\s+\w*\s*(bloqueada|bloqueado|suspensa|suspenso|restrita|"
         r"nao (esta |ta )?autorizad)", 5),
        (r"(bloquearam|bloquearao|bloquearem)\s+(a\s+|minha\s+|meu\s+)*(conta|acesso)", 5),
        (r"(senha|login|logar|autenticacao|token|codigo de verificacao|isafe|i-safe)", 3),
        (r"(nao|n)\s+(entra|abre|loga|carrega)\s+(na|a|o)\s+(minha\s+|meu\s+)?(conta|app|aplicativo)", 4),
        (r"(validacao|verificacao)\s+(de\s+)?(identidade|documento|cadastro)", 3),
        (r"(cadastro|recadastr)", 2),
        (r"(sms|email|e-mail)\s+(de\s+)?(confirmacao|verificacao)", 2),
        (r"fora da conta|me desconect|caiu a sessao|conta sumiu|sem acesso", 3),
        (r"(suspenderam|cancelaram|encerraram|desativaram)\s+(a\s+|minha\s+)*conta", 5),
    ],
    "Falha em transacao": [
        (r"\b(pix)\b", 3),
        (r"\b(qr ?code|qrcode|leitor de qr)", 4),
        (r"\b(transferencia|transferir|tranferencia)", 3),
        (r"\b(pagamento|pagar|boleto|recarga)\b", 2),
        (r"\b(comprovante|extrato)", 3),
        (r"\b(nao|n)\s+(caiu|chegou|entrou)\s+(o\s+)?(dinheiro|valor|pix|pagamento)", 5),
        (r"\b(dinheiro|valor|pix)\s+(sumiu|desapareceu|nao chegou|nao caiu|preso|retido)", 5),
        (r"\b(saque|sacar|resgatar|resgate)", 3),
        (r"\b(maquininha|tap to pay|aproximacao|nfc)", 3),
        (r"\b(estorno|devolucao do valor)", 2),
        (r"\b(nao|n)\s+(consigo|consegui)\s+(pagar|transferir|receber|sacar|fazer pix)", 5),
    ],
    "Cartao, credito e limite": [
        (r"\b(cartao|cartoes)\b", 4),
        (r"\b(limite)\b", 4),
        (r"\b(fatura|faturas)", 4),
        (r"\b(emprestimo|consignado|refinanciamento|portabilidade|credito pessoal)", 5),
        (r"\b(antecipa(r|cao|ndo)|parcela|parcelamento|parcelas)", 3),
        (r"\b(credito|creditos)\b", 3),
        (r"\b(analise de credito|score|negativad|serasa|divida|renegocia)", 3),
        (r"\b(cartao)\s+(nao\s+)?(chegou|chega|entregue|demora)", 5),
        (r"\b(aumenta|aumentar|liberar|liberou|negaram|negou)\s+(o\s+)?limite", 5),
        (r"\b(pre ?aprovad|nao dao cartao|nao liberam)", 3),
    ],
    "Tarifas e cobrancas": [
        (r"\b(taxa|taxas|tarifa|tarifas)", 5),
        (r"\b(cobranca|cobrando|cobraram|cobrou|cobram)", 4),
        (r"\b(desconto|descontando|descontaram|descontou|descontam)", 4),
        (r"\b(juros)", 4),
        (r"\b(abusiv|absurdo o valor|roubo|roubando|ladrao|propaganda enganosa)", 3),
        (r"\b(cobranca|valor)\s+(indevida|indevido|errada|errado)", 5),
        (r"\b(mensalidade|anuidade)", 4),
        (r"\b(sem\s+(a\s+)?(minha\s+)?(autorizacao|permissao|previa)|sem meu conhecimento|"
         r"sem avisar|sem eu autorizar)", 4),
        (r"\b(retirou|tirou|sumiu|pegaram)\s+(o\s+|um\s+)?dinheiro\s+(da|de)\s+(minha\s+)?conta", 4),
    ],
    "Desempenho do aplicativo": [
        (r"\b(trava|travando|travou|travad)", 5),
        (r"\b(lento|lentidao|demora pra abrir|muito devagar|congela|congelando)", 4),
        (r"\b(bug|bugado|bugou|bulgand)", 5),
        (r"\b(fecha sozinho|fechando sozinho|cai sozinho|sai sozinho|clicar.{0,20}fecha)", 5),
        (r"\b(atualiza(cao|r|ram|ções|coes))", 3),
        (r"(nao|n)\s+(abre|carrega|funciona|roda)\s*(o\s+)?(app|aplicativo)?", 4),
        (r"\b(parou de funcionar|deixou de funcionar|saiu do ar|fora do ar)", 5),
        (r"\b(erro|falha)\s+(no|do|ao)\s+(app|aplicativo|sistema|abrir)", 4),
        (r"\b(app|aplicativo)\s+\w*\s*(travando|lento|pesado|ruim demais|nao funciona|nao abre)", 4),
        (r"(tela)\s+\w*\s*(branca|preta|cinza)|nao carrega", 4),
        (r"\b(desinstalei|reinstalei|limpei o cache)", 2),
        (r"\b(so da erro|da erro|dando erro)", 3),
    ],
    "Atendimento ao cliente": [
        (r"\b(atendimento|atendente|suporte|sac|ouvidoria|central de atendimento)", 5),
        (r"\b(chat|chatbot|robo|bot)\b", 3),
        (r"\b(ninguem|nao tem como falar|impossivel falar)\s*(resolve|responde|atende|me ajuda)?", 4),
        (r"\b(nao|n)\s+(me\s+)?(respondem|responderam|retornam|retornaram|resolvem|resolveram)", 4),
        (r"\b(abri|abertura de|protocolo|reclamacao)\s*(chamado|reclamacao|protocolo)?", 2),
        (r"\b(descaso|desrespeito com o cliente|jogam de um lado pro outro)", 3),
        (r"\b(falar com|atendido por)\s+(um\s+)?(humano|pessoa|atendente)", 4),
    ],
}

# Expressões compiladas uma única vez, por eficiência.
REGRAS = {
    categoria: [(re.compile(padrao), peso) for padrao, peso in regras]
    for categoria, regras in CATEGORIAS.items()
}

CATEGORIA_PADRAO = "Outros"


def normalizar(texto: str) -> str:
    """Prepara o texto para a aplicação das regras.

    Converte para caixa baixa, remove acentuação e colapsa espaços, de modo
    que as expressões regulares possam ser escritas sem acento e sem variação
    de maiúsculas.
    """
    texto = str(texto).lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"\s+", " ", texto)
    return texto


def pontuar(texto: str) -> dict:
    """Retorna a pontuação acumulada do texto para cada categoria."""
    normalizado = normalizar(texto)
    placar = {}
    for categoria, regras in REGRAS.items():
        total = 0
        for padrao, peso in regras:
            if padrao.search(normalizado):
                total += peso
        placar[categoria] = total
    return placar


def rotular(texto: str, margem_minima: int = 0) -> tuple:
    """Atribui uma categoria ao texto.

    Retorna a tupla (categoria, pontuacao, confianca), em que a confiança é a
    diferença entre a maior e a segunda maior pontuação. Confiança baixa
    indica avaliação ambígua, que menciona mais de um tema com evidência
    semelhante — informação útil tanto para a amostragem da validação manual
    quanto para a discussão de limitações.

    Textos sem nenhuma correspondência recebem a categoria 'Outros'.
    """
    placar = pontuar(texto)
    ordenado = sorted(placar.items(), key=lambda item: item[1], reverse=True)

    melhor, pontos = ordenado[0]
    segundo_pontos = ordenado[1][1] if len(ordenado) > 1 else 0
    confianca = pontos - segundo_pontos

    if pontos == 0 or confianca < margem_minima:
        return CATEGORIA_PADRAO, pontos, confianca

    return melhor, pontos, confianca


def rotular_series(textos) -> "pd.DataFrame":
    """Aplica o rotulador a uma sequência de textos.

    Retorna um DataFrame com as colunas categoria_regra, pontuacao e
    confianca, alinhado ao índice da entrada.
    """
    import pandas as pd

    resultados = [rotular(t) for t in textos]
    return pd.DataFrame(
        resultados,
        columns=["categoria_regra", "pontuacao", "confianca"],
        index=getattr(textos, "index", None),
    )
