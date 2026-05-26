# Detector de Fake News Eleitorais

Projeto desenvolvido para classificar afirmações e notícias do contexto político-eleitoral como `Fake`, `True` ou `Inconclusiva`, utilizando aprendizado supervisionado.

O sistema possui duas formas de uso:

- Classificação pelo terminal, usando `classify.py`.
- Interface web local, usando `app.py`, com um semáforo visual para indicar o resultado.

## Integrantes

- Samira de Jesus Santos
- Victor Rogério Aguiar do Rosário


## Imagens da interface


| Verdadeiro | Fake | Inconclusivo |
| --- | --- | --- |
| ![Semáforo indicando notícia verdadeira](docs/images/verdadeiro.jpeg) | ![Semáforo indicando fake news](docs/images/falso.jpeg) | ![Semáforo indicando resultado inconclusivo](docs/images/inconclusivo.jpeg) |

## Preparação do dataset

O dataset principal fica em `data/dataset.csv` e possui duas colunas:

| Coluna | Descrição |
| --- | --- |
| `Texto` | Afirmação, notícia, alegação ou correção factual. |
| `Label` | Classe esperada: `Fake` para conteúdo falso/enganoso e `True` para conteúdo verdadeiro. |

Os dados foram coletados principalmente com a biblioteca [`factcheckexplorer`](https://github.com/GONZOsint/factcheckexplorer), que consulta o Google Fact Check Explorer.

Para melhorar o reconhecimento de fatos verdadeiros comuns, também foram adicionadas notícias e frases de fontes confiáveis, como `gov.br`/Planalto, TSE, Câmara, Senado, Agência Brasil e G1. Esses exemplos foram marcados como `True`.

Importante: a classificação final não faz checagem online em tempo real. O modelo responde apenas com base no dataset preparado e no modelo treinado.

## Arquivos gerados

- `data/raw/`: arquivos CSV brutos retornados pelo `factcheckexplorer`.
- `data/factcheck_sources.csv`: textos coletados, rótulos convertidos, vereditos originais, fontes e URLs das checagens.
- `data/official_true_sources.csv`: exemplos `True` vindos de fontes confiáveis.
- `data/dataset_unique.csv`: dataset sem duplicatas, antes da reamostragem.
- `data/dataset.csv`: dataset final balanceado, usado no treinamento.
- `data/balance_report.json`: resumo do balanceamento.
- `models/logistic_regression_model.joblib`: modelo treinado.
- `models/metrics.json`: métricas calculadas no treinamento.

## Tamanho do dataset

O dataset único possui `5.718` exemplos:

| Classe | Exemplos únicos |
| --- | ---: |
| `Fake` | 4.724 |
| `True` | 994 |

Como a base original tinha muito mais exemplos falsos do que verdadeiros, o dataset final foi balanceado por reamostragem com reposição.

O dataset final usado no treinamento possui `50.000` linhas:

| Classe | Exemplos no dataset final |
| --- | ---: |
| `Fake` | 25.000 |
| `True` | 25.000 |

As buscas incluíram temas eleitorais e políticos, como `eleição`, `urna`, `voto`, `Bolsonaro`, `Lula`, `TSE`, `STF`, `Alexandre de Moraes`, `Bolsonaro preso`, `prisão Bolsonaro`, `deputado`, `senador`, `Congresso Nacional`, `Pablo Marçal`, `Guilherme Boulos`, `Fernando Haddad`, entre outros.


## Algoritmo utilizado

O modelo utiliza **TF-IDF + Logistic Regression**.

O TF-IDF transforma os textos em atributos numéricos. Em seguida, a Logistic Regression aprende a separar os textos entre as classes `Fake` e `True`.

O vetorizador usa n-gramas de caracteres de tamanho 3 a 6. Essa escolha ajuda o modelo a lidar melhor com variações de escrita, acentos, nomes próprios e termos políticos.

## Treinamento

O treinamento é feito pelo arquivo `train.py`.

Etapas principais:

1. O script lê o arquivo `data/dataset.csv`.
2. Para calcular as métricas, remove duplicatas antes da divisão entre treino e teste.
3. O texto é transformado em números com `TfidfVectorizer`.
4. O modelo é treinado com `LogisticRegression`.
5. O conjunto de treino é balanceado internamente.
6. O modelo é avaliado no conjunto de teste.
7. O modelo final é treinado com todos os dados disponíveis.
8. O modelo treinado é salvo em `models/logistic_regression_model.joblib`.
9. As métricas são salvas em `models/metrics.json`.

## Métricas analisadas

As métricas abaixo foram calculadas no conjunto de teste, usando exemplos únicos para evitar avaliação em dados repetidos.

| Métrica | Resultado |
| --- | ---: |
| Accuracy geral | 86,50% |
| Precision `Fake` | 93,33% |
| Recall `Fake` | 90,09% |
| F1-score `Fake` | 91,68% |
| Precision `True` | 59,66% |
| Recall `True` | 69,48% |
| F1-score `True` | 64,19% |

Matriz de confusão:

```text
Linhas: classes reais ["Fake", "True"]
Colunas: classes previstas ["Fake", "True"]

[[1064, 117],
 [  76, 173]]
```

## Sobre o filtro de 95%

A acurácia geral do modelo foi de `86,50%`. Porém, o sistema não aceita qualquer resposta automaticamente.

Para exibir uma classificação final, o classificador usa:

- confiança mínima de `95%`;
- similaridade mínima de `35%` com exemplos do dataset local.

Quando o texto não passa nesses critérios, o sistema retorna `Inconclusiva`.

Com esse filtro, os resultados aceitos no teste tiveram:

| Indicador | Resultado |
| --- | ---: |
| Previsões aceitas | 291 |
| Cobertura do conjunto de teste | 20,35% |
| Accuracy nas previsões aceitas | 99,31% |

Isso significa que o modelo é mais conservador: ele prefere retornar `Inconclusiva` quando não encontra segurança suficiente para responder.

## Como executar

Instale as dependências:

```bash
py -m pip install -r requirements.txt
```

Coletar ou reconstruir os dados com `factcheckexplorer`:

```bash
py collect_data.py
```

Adicionar exemplos verdadeiros de fontes confiáveis:

```bash
py collect_official_true_data.py
```

Balancear o dataset para 50.000 linhas:

```bash
py balance_dataset.py
```

Treinar o modelo:

```bash
py train.py
```

Classificar uma afirmação pelo terminal:

```bash
py classify.py "Urna foi fraudada sem prova"
```

Exemplos:

```bash
py classify.py "lula é o presidente do brasil"
py classify.py "bolsonaro está preso"
py classify.py "bolsonaro levou uma facada"
```

## Interface web

Para abrir a interface local:

```bash
py app.py
```

Depois, acesse no navegador:

```text
http://localhost:8000
```

Na interface:

- verde indica `True`;
- vermelho indica `Fake`;
- amarelo indica `Inconclusiva`.

## Observação

A base de checagens possui naturalmente mais conteúdos falsos ou enganosos, pois sites de fact-checking costumam verificar boatos e alegações suspeitas.

Por isso, mesmo com o dataset final balanceado, a quantidade de exemplos verdadeiros únicos ainda é menor. O retorno `Inconclusiva` foi usado para evitar respostas muito confiantes quando o texto não é parecido o suficiente com o material usado no treinamento.
