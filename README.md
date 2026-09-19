# Aplicação para Reserva de Salas

Aplicação web para consulta e reserva de salas e laboratórios, desenvolvida em **Python** utilizando o framework **Streamlit**.

##  Sobre o projeto

O sistema tem como objetivo facilitar a consulta de salas disponíveis e o gerenciamento de reservas de ambientes acadêmicos.

O projeto está sendo desenvolvido de forma modular, separando a interface, os serviços de lógica e os dados da aplicação.

A camada `services/` concentra as **regras de negócio e validações**, enquanto os `controllers/` fazem a **ponte entre a view e os services**.

##  Tecnologias utilizadas

- Python
- Streamlit
- Pandas
- Git
- GitHub

##  Estrutura do projeto

```text
├── app/
│   ├── main.py
│   ├── pages/
│   │   ├── 1_Home.py
│   │   ├── 2_Salas.py
│   │   ├── 3_Detalhes_Sala.py
│   │   ├── 4_Reservar.py
│   │   └── 5_Minhas_Reservas.py
│   ├── controllers/
│   ├── services/
│   └── utils/
│
├── data/
│   ├── usuarios.csv
│   ├── salas.csv
│   ├── equipamentos.csv
│   ├── sala_equipamento.csv
│   └── reservas.csv
│
├── tests/
├── docs/
├── assets/
├── requirements.txt
└── README.md

## Como rodar o projeto

### Pré-requisitos

Antes de executar o projeto, é necessário ter instalado:

- Python 3
- Git

Para verificar se o Python está instalado:

```cmd
python --version
```

Para verificar se o Git está instalado:

```cmd
git --version
```

### 1. Clonar o repositório

Abra o terminal e clone o repositório:

```cmd
git clone <URL_DO_REPOSITORIO>
```

Depois, entre na pasta do projeto:

```cmd
cd <PASTA_DO_PROJETO>
```

### 2. Criar o ambiente virtual

Dentro da pasta do projeto, execute:

```cmd
python -m venv .venv
```

### 3. Ativar o ambiente virtual

No Windows utilizando o CMD:

```cmd
.venv\Scripts\activate.bat
```

Após a ativação, `(.venv)` deverá aparecer no início da linha do terminal.

### 4. Instalar as dependências

Com o ambiente virtual ativado, execute:

```cmd
pip install -r requirements.txt
```

### 5. Executar a aplicação

Execute:

```cmd
streamlit run app\main.py
```

O Streamlit iniciará a aplicação. Normalmente, ela ficará disponível em:

```text
http://localhost:8501
```

Caso o navegador não abra automaticamente, acesse esse endereço manualmente.

### 6. Encerrar a aplicação

Para parar o servidor do Streamlit, volte ao terminal e pressione:

```text
Ctrl + C
```

### Próximas execuções

Depois da primeira configuração, não é necessário criar novamente o ambiente virtual nem reinstalar as dependências.

Basta ativar o ambiente virtual e iniciar o Streamlit:

```cmd
.venv\Scripts\activate.bat
streamlit run app\main.py
```

