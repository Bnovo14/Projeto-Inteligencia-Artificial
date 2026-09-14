# Classificação automática de reclamações de usuários de aplicativos de pagamento digital

Projeto da disciplina **Inteligência Artificial — 7ºJ SI (Noite)**
Faculdade de Computação e Informática — Universidade Presbiteriana Mackenzie
Prof. Dr. Leandro Zerbinatti — 2026

## Integrantes

| Nome | RA | E-mail |
|---|---|---|
| Bruno Cruz Bregion Novo | 10409538 | 10409538@mackenzista.com.br |
| Vinicius Silva Almeida | 10409019 | 10409019@mackenzista.com.br |
| Gabriel Bello | 10416808 | 10416808@mackenzista.com.br |

## Sobre o projeto

**Opção escolhida:** Framework (scikit-learn) — classificação supervisionada de texto.

Aplicativos de pagamento digital recebem milhares de avaliações públicas por mês,
escritas em texto livre. Esse material contém informação operacional relevante —
falhas de transação, cobranças indevidas, problemas de autenticação — mas chega às
empresas de forma não estruturada, o que inviabiliza a triagem manual em escala.

O projeto propõe um classificador supervisionado que atribui automaticamente uma
categoria de problema a cada avaliação, apoiando equipes de suporte na priorização
de demandas.

**Etapa atual (N1):** proposta, captura do dataset, análise exploratória e preparação
dos dados.
**Etapa seguinte (N2):** rotulagem manual, treinamento comparativo de modelos e
avaliação de resultados.

## Dados

Os dados são **originais, capturados pelo próprio grupo**. Não foi utilizada nenhuma
base pronta de terceiros. A captura foi feita por script Python desenvolvido pelos
integrantes (`coleta_avaliacoes.py`), que extrai as avaliações públicas da Google
Play Store por meio da biblioteca `google-play-scraper`.

### `avaliacoes_apps_pagamento.csv` — dataset bruto

24.000 avaliações públicas de seis aplicativos brasileiros de pagamento digital,
publicadas entre **20/07/2026 e 07/09/2026**, com 4.000 registros por aplicativo:
PicPay, Mercado Pago, Nubank, PagBank, Banco Inter e RecargaPay.

| Campo | Tipo | Descrição |
|---|---|---|
| `id_avaliacao` | texto | Identificador único da avaliação na plataforma |
| `aplicativo` | categórico | Nome comercial do aplicativo avaliado |
| `usuario_pseudonimizado` | texto | Hash SHA-256 truncado do nome de exibição do autor |
| `nota` | inteiro | Nota atribuída pelo usuário, de 1 a 5 |
| `texto` | texto | Conteúdo livre da avaliação |
| `data` | data/hora | Momento de publicação |
| `curtidas` | inteiro | Usuários que marcaram a avaliação como útil |
| `versao_app` | texto | Versão do aplicativo no momento da avaliação |
| `houve_resposta_empresa` | binário | Indica se houve resposta pública da empresa |

**Anonimização.** O nome de exibição do autor é dado pessoal na acepção da LGPD
(Lei nº 13.709/2018) e **não é armazenado**. No momento da captura, o campo é
convertido em hash SHA-256 truncado, preservando a capacidade de identificar
múltiplas avaliações de um mesmo autor sem expor sua identidade.

### `corpus_modelagem.csv` — dado derivado

4.211 avaliações selecionadas para a etapa de modelagem, resultantes de dois
critérios de recorte aplicados ao dataset bruto: nota de 1 a 3 (o objeto do projeto
é a reclamação) e mínimo de 5 palavras (textos menores não permitem identificar a
natureza do problema). Inclui as colunas de texto normalizado e radicalizado
geradas na preparação.

### `amostra_rotulagem.csv` — dado derivado

1.199 avaliações amostradas de forma estratificada por aplicativo e nota,
distribuídas igualmente entre os três integrantes para rotulagem manual na etapa
seguinte. 120 registros (10%) estão marcados para dupla checagem, permitindo
mensurar a concordância entre anotadores. A coluna `categoria` é preenchida
manualmente.

## Estrutura do repositório

| Arquivo | Descrição |
|---|---|
| `Relatorio_N1.docx` | Relatório do projeto no template da FCI |
| `coleta_avaliacoes.py` | Script de captura das avaliações na Google Play Store |
| `analise_exploratoria.ipynb` | Notebook de análise exploratória e preparação dos dados |
| `avaliacoes_apps_pagamento.csv` | Dataset bruto capturado |
| `corpus_modelagem.csv` | Corpus selecionado para modelagem |
| `amostra_rotulagem.csv` | Amostra estratificada para rotulagem manual |

## Como reproduzir

```bash
pip install google-play-scraper pandas matplotlib seaborn nltk wordcloud

# 1. Captura dos dados (gera dados/avaliacoes_apps_pagamento.csv)
python coleta_avaliacoes.py

# Opcional: coletar apenas alguns aplicativos, consolidando com a coleta anterior
python coleta_avaliacoes.py --apps Nubank PicPay

# 2. Análise exploratória e preparação
jupyter notebook analise_exploratoria.ipynb
```

A coleta é incremental: se já existir um arquivo de coleta anterior, os novos
registros são consolidados aos existentes e as duplicatas removidas pelo
identificador da avaliação.

O notebook espera encontrar o dataset em `dados/avaliacoes_apps_pagamento.csv` e
grava as figuras em `figuras/` e os dados derivados em `dados/`.

## Considerações éticas

As avaliações utilizadas são públicas, mas dado público não é sinônimo de dado
livre. O projeto adota pseudonimização na origem, não realiza nenhum esforço de
reidentificação e apresenta análises exclusivamente agregadas. O artefato é
concebido como instrumento de apoio à decisão humana, não de decisão automatizada.
A discussão completa está na seção 4 do relatório.