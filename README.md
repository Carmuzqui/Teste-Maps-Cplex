# Otimizador de eletropostos - Implementação do modelo FCSA MILP proposto por Caio dos Santos

Este repositório contém a implementação computacional de um modelo de otimização para o dimensionamento e localização de estações de recarga para veículos elétricos. O projeto baseia-se no modelo FCSA MILP (*Flow Capturing Location Allocation - Mixed Integer Linear Programming*) proposto por Caio dos Santos (Unicamp, 2022).

A ferramenta foi desenvolvida em Python 3.10 e utiliza o solver IBM ILOG CPLEX para a resolução matemática, contando com uma interface gráfica web desenvolvida em Streamlit para visualização de resultados e análise de cenários.

---

## Sobre o modelo

O modelo matemático implementado visa otimizar a infraestrutura de recarga considerando restrições técnicas, econômicas e geográficas.

### Características principais

* **Cobertura espacial:** utiliza restrição de raio geográfico para garantir o atendimento da demanda.
* **Integração fotovoltaica:** dimensionamento simultâneo de sistemas fotovoltaicos (*carports* PV) nas estações.
* **Gestão energética:** implementação de *net-metering* para gestão de créditos de energia.
* **Otimização econômica:** análise baseada no Valor Presente (VP), considerando investimento inicial (CAPEX) e custos operacionais (OPEX).
* **Benefícios de transporte:** considera a conectividade dos trechos (*links*) e a demanda de veículos elétricos.

### Método de resolução

O problema é resolvido através de uma abordagem de **otimização lexicográfica em dois passos**, em busca do equilíbrio entre qualidade de serviço e viabilidade econômica:

1.  **Passo 1 (maximização de benefícios):**
    minimizar a função objetivo negativa (equivalentemente, maximizar a positiva) focada na cobertura e importância dos trechos:
    *Função:* $f = \sum (xl \cdot rol \cdot betal)$
    Onde *xl* é a variável binária de cobertura, *rol* é o parâmetro de conectividade e *betal* o benefício de transporte.

2.  **Passo 2 (minimização de custos):**
    minimizar a soma dos custos de investimento ($C_{in}$) e operação ($C_{op}$), sujeito à restrição de que o valor da função de benefícios $f$ seja igual ao valor ótimo ($f_{optimo}$) encontrado no Passo 1.

---

## Requisitos do sistema

Para a execução correta deste projeto, é estritamente necessário o cumprimento dos requisitos abaixo.

### Ambiente Python
* **Python 3.10** (Versão estável recomendada para compatibilidade com CPLEX).
  * [Download do instalador Python 3.10.11 para Windows](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)

### Software de otimização
* **IBM ILOG CPLEX Optimization Studio**: é necessário ter o CPLEX instalado e licenciado na máquina local para a resolução dos modelos MILP.

### Bibliotecas Python
As dependências estão listadas no arquivo `requirements.txt`. As versões mínimas testadas são:

* `docplex` >= 2.25.0
* `pandas` >= 1.3.0
* `numpy` >= 1.21.0
* `PyYAML` >= 6.0
* `streamlit` >= 1.28.0
* `streamlit-folium` >= 0.15.0
* `folium` >= 0.14.0
* `plotly` >= 5.15.0
* `python-dotenv`
* `googlemaps`

### Editor de código (sugestão)
Embora o usuário seja livre para utilizar o ambiente de sua preferência, sugere-se o uso do **Visual Studio Code (VS Code)** para edição e execução do projeto.
* [Download do VS Code](https://code.visualstudio.com/download)

---

## Instalação

Siga os passos abaixo para configurar o ambiente de desenvolvimento.

1.  **Clonar o repositório:**
    baixe os arquivos do projeto para o diretório local desejado.

2.  **Criar e ativar ambiente virtual (recomendado):**
    é altamente recomendável isolar as dependências do projeto.
    
    *Criação (selecionando a versão 3.10):*
    ```bash
    py -3.10 -m venv venv
    ```
    
    *Ativação (Windows PowerShell):*
    ```bash
    .\venv\Scripts\Activate.ps1
    ```

3.  **Instalar dependências:**
    com o ambiente ativo (verifique se aparece `(venv)` no terminal), instale as bibliotecas:
    ```bash
    python -m pip install -r requirements.txt
    ```

4.  **Verificar instalação do CPLEX:**
    execute o comando abaixo para confirmar se a biblioteca `docplex` consegue acessar o solver localmente.
    ```bash
    python -c "from docplex.mp.model import Model; print('CPLEX OK')"
    ```
    
---

## Uso

### Execução do dashboard (Streamlit)
Para iniciar a interface visual interativa, certifique-se de que o ambiente virtual está ativo e execute:

```bash
python -m streamlit run streamlit_app/app_modelo_Caio.py