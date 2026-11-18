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

### 6. Configure o banco de dados

Crie o arquivo `.streamlit/secrets.toml` (ele não é versionado) com as credenciais do MySQL:

```toml
[mysql]
host = "SEU_HOST"
port = 3306
database = "NOME_DO_BANCO"
user = "SEU_USUARIO"
password = "SUA_SENHA"
ssl_ca = "ca.pem"
```

Coloque o certificado `ca.pem` na raiz do projeto.

### 7. Execute a aplicação

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
│   ├── services/
|   ├── messaging/
│   └── utils/
│
├── tests/
│   └── integration/
├── docs/
├── assets/
├── migrar_senhas.py
│
├── main.py
├── requirements.txt
└── README.md
```

O projeto utiliza uma organização baseada na arquitetura **MVC (Model-View-Controller)**:

- **Views:** interface e renderização das páginas com Streamlit.
- **Controllers:** intermediam as ações entre as Views e os Models.
- **Models:** representam as entidades e suas validações (inclusive os limites das colunas do banco) e a conexão com o MySQL.
- **Services:** concentram as regras de negócio, as consultas e as gravações no banco.
- **Messaging:** notificações do sistema.
- **main.py:** ponto de entrada e responsável pela navegação da aplicação.

- migrar_senhas.py: um script utilitário/one-off de migração de senhas em texto para hash.
## Testes

```bash
python -m pytest                       # tudo (os de integração são pulados sem banco de teste)
python -m pytest -m "not integration"  # só os unitários, que não precisam de banco
python -m pytest -m integration        # só os de integração (veja tests/integration/README.md)
```

Os testes unitários usam mocks e **não podem** acessar o banco real: um bloqueio em `tests/conftest.py`
faz o teste falhar se isso acontecer. Datas dos testes são sempre calculadas a partir do relógio do app
(`tests/datas.py`), nunca fixas.

## Encerrando a aplicação

Para interromper o servidor do Streamlit, pressione:

```text
Ctrl + C
```

Para sair do ambiente virtual:

```bash
deactivate
```
