# Reserva de Salas - LarpTech

Aplicação web para reserva de salas e laboratórios, desenvolvida em **Python** utilizando **Streamlit**.

## Pré-requisitos

Antes de executar o projeto, é necessário ter instalado:

- Python 3
- Git
- pip

Para verificar se o Python está instalado:

```bash
python --version
```

## Como executar o projeto

### 1. Clone o repositório

```bash
git clone URL_DO_REPOSITORIO
```

### 2. Entre na pasta do projeto

```bash
cd reserva_salas_LarpTech
```

### 3. Crie um ambiente virtual

```bash
python -m venv .venv
```

### 4. Ative o ambiente virtual

No Windows (CMD):

```bash
.venv\Scripts\activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

Quando o ambiente estiver ativado, normalmente aparecerá `(.venv)` no início da linha do terminal.

### 5. Instale as dependências

```bash
python -m pip install -r requirements.txt
```

### 6. Execute a aplicação

```bash
python -m streamlit run main.py
```

O Streamlit iniciará um servidor local. A aplicação normalmente estará disponível em:

```text
http://localhost:8501
```

## Estrutura do projeto

```text
reserva_salas_LarpTech/
│
├── app/
│   ├── views/
│   ├── controllers/
│   ├── models/
│   ├── components/
│   └── utils/
│
├── data/
├── docs/
├── assets/
│
├── main.py
├── requirements.txt
└── README.md
```

O projeto utiliza uma organização baseada na arquitetura **MVC (Model-View-Controller)**:

- **Views:** interface e renderização das páginas com Streamlit.
- **Controllers:** intermediam as ações entre as Views e os Models.
- **Models:** representam as entidades, regras de negócio e acesso aos dados.
- **Components:** componentes reutilizáveis da interface.
- **Data:** arquivos CSV utilizados como dados simulados.
- **main.py:** ponto de entrada e responsável pela navegação da aplicação.

## Encerrando a aplicação

Para interromper o servidor do Streamlit, pressione:

```text
Ctrl + C
```

Para sair do ambiente virtual:

```bash
deactivate
```