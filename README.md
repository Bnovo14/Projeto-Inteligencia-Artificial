# Classificação automática de reclamações de usuários de aplicativos de pagamento digital
 
Projeto da disciplina **Inteligência Artificial — 7ºJ SI (Noite)**
Faculdade de Computação e Informática — Universidade Presbiteriana Mackenzie
Prof. Dr. Leandro Zerbinatti — 2026
 
## Integrantes
 
| Nome | RA | E-mail |
|---|---|---|
| Bruno Cruz Bregion Novo | 10409538 | 10409538@mackenzista.com.br |
| Vinicius Silva Almeida | 10409019 | 10409019@mackenzista.com.br |
 
## Apresentação em vídeo
 
**https://youtu.be/8KxDhn7Avmk** — 4min31s, narrado pelos dois integrantes.
 
## Sobre o projeto
 
**Opção escolhida:** Framework (scikit-learn) — classificação supervisionada de texto.
 
Aplicativos de pagamento digital recebem milhares de avaliações públicas por mês,
escritas em texto livre. Esse material contém informação operacional relevante —
falhas de transação, cobranças indevidas, problemas de autenticação — mas chega às
empresas de forma não estruturada, o que inviabiliza a triagem manual em escala.
 
O projeto propõe um classificador supervisionado que atribui automaticamente uma
categoria de problema a cada avaliação, apoiando equipes de suporte na priorização
de demandas.
 
**N1 — concluída:** proposta, captura do dataset, análise exploratória e preparação
dos dados.
**N2 — concluída:** rotulagem por supervisão fraca, treinamento comparativo de
modelos, avaliação de resultados e experimentos de verificação da generalização.
 
### Principais resultados
 
| Métrica | Valor |
|---|---|
| Melhor modelo | SVM linear (TF-IDF, unigramas + bigramas) |
| F1 macro no conjunto de teste | 0,783 |
| F1 macro do classificador trivial (piso) | 0,079 |
| F1 macro sem os termos-gatilho (ablação) | 0,469 |
| Retenção de desempenho após a ablação | 55,4% |
 
O experimento de ablação remove do texto todas as expressões que originaram os
rótulos e treina novamente o modelo. Ele existe porque os rótulos foram gerados por
regras: sem essa medida, o F1 de 0,783 poderia estar apenas indicando que o modelo
memorizou as próprias regras. A retenção de 55,4% acima do piso trivial mostra que
cerca de metade da capacidade do modelo vem de generalização linguística.
 
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
 
### `amostra_rotulagem.csv` — dado derivado da N1
 
1.199 avaliações amostradas de forma estratificada por aplicativo e nota, preparadas
na N1 para rotulagem manual. Essa rotulagem **não chegou a ser realizada**: a
estimativa de esforço mostrou-se incompatível com o prazo da segunda etapa, e optou-se
pela rotulagem por regras descrita abaixo. O arquivo é mantido no repositório como
registro do planejamento original.
 
### `corpus_classificado.csv` — dado derivado da N2
 
As 4.211 avaliações do corpus com sua categoria final. Para as 3.248 avaliações em que
alguma regra disparou, a categoria é a atribuída pelo rotulador; para as 963 restantes,
é a predita pelo modelo treinado. Inclui também a pontuação e a margem de confiança
calculadas pelas regras.
 
## Estrutura do repositório
 
| Arquivo | Descrição |
|---|---|
| `Relatorio_N1.docx` | Relatório da primeira etapa, no template da FCI |
| `Relatorio_N2.docx` | Relatório final, no template da FCI |
| `coleta_avaliacoes.py` | Script de captura das avaliações na Google Play Store |
| `rotulador.py` | Função de rotulagem por regras (supervisão fraca) |
| `analise_exploratoria.ipynb` | Notebook de análise exploratória e preparação dos dados |
| `modelagem_classificacao.ipynb` | Notebook de rotulagem, treinamento e avaliação |
| `avaliacoes_apps_pagamento.csv` | Dataset bruto capturado |
| `corpus_modelagem.csv` | Corpus selecionado para modelagem |
| `amostra_rotulagem.csv` | Amostra preparada na N1 para rotulagem manual |
| `corpus_classificado.csv` | Corpus com a categoria final de cada avaliação |
| `metricas_modelo.csv` | Métricas consolidadas da avaliação |
| `Apresentacao_N2.pptx` | Apresentação com narração embutida e avanço automático |
 
## Como reproduzir
 
```bash
pip install google-play-scraper pandas matplotlib seaborn nltk wordcloud
 
# 1. Captura dos dados (gera dados/avaliacoes_apps_pagamento.csv)
python coleta_avaliacoes.py
 
# Opcional: coletar apenas alguns aplicativos, consolidando com a coleta anterior
python coleta_avaliacoes.py --apps Nubank PicPay
 
# 2. Análise exploratória e preparação
jupyter notebook analise_exploratoria.ipynb
 
# 3. Rotulagem, treinamento e avaliação
jupyter notebook modelagem_classificacao.ipynb
```
 
A coleta é incremental: se já existir um arquivo de coleta anterior, os novos
registros são consolidados aos existentes e as duplicatas removidas pelo
identificador da avaliação.
 
Os notebooks esperam encontrar os dados em `dados/` e gravam as figuras em `figuras/`
e os conjuntos derivados em `dados/`. O segundo notebook importa `rotulador.py`, que
precisa estar na mesma pasta.
 
## Metodologia
 
O conjunto capturado não possui rótulo de categoria na origem: a Play Store informa a
nota atribuída, não o tipo de problema relatado. Diante da inviabilidade de rotular
manualmente 4.211 avaliações no prazo disponível, aplicou-se **supervisão fraca**: uma
função de rotulagem baseada em expressões regulares com pesos atribui a categoria de
maior pontuação acumulada no texto.
 
Os textos foram representados por TF-IDF e submetidos ao treinamento comparativo de
Naive Bayes multinomial, regressão logística e SVM linear, com validação cruzada de
cinco partições e busca em grade. A avaliação usou F1 macro como métrica principal,
dado o desbalanceamento entre categorias.
 
**Limitação principal:** não há conjunto rotulado por humanos. As métricas medem a
concordância do modelo com a função de rotulagem, não com o julgamento humano. O valor
de 0,783 não deve ser lido como taxa de acerto frente a um anotador humano. É o
primeiro trabalho futuro indicado no relatório.
 
## Considerações éticas
 
As avaliações utilizadas são públicas, mas dado público não é sinônimo de dado
livre. O projeto adota pseudonimização na origem, não realiza nenhum esforço de
reidentificação e apresenta análises exclusivamente agregadas. O artefato é
concebido como instrumento de apoio à decisão humana, não de decisão automatizada.
A discussão completa está na seção 4 do relatório.
 
