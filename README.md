# Aplicação para Reserva de Salas

Aplicação web para consulta e reserva de salas e laboratórios, desenvolvida em **Python** utilizando o framework **Streamlit**.

##  Sobre o projeto

O sistema tem como objetivo facilitar a consulta de salas disponíveis e o gerenciamento de reservas de ambientes acadêmicos.

O projeto está sendo desenvolvido de forma modular, separando a interface, os controladores, os serviços de lógica, os modelos e os dados da aplicação.

Na arquitetura do projeto, `services` concentra as regras de negócio e as validações, enquanto `controllers` faz a ponte entre a interface (`view`) e os serviços.

##  Tecnologias utilizadas

- Python
- Streamlit
- Pandas
- Git
- GitHub

##  Estrutura do projeto

```text
reserva_salas_LarpTech/
├── app/
│   ├── views/
│   │   ├── detalhes_sala_view.py
│   │   ├── home_view.py
│   │   ├── login_view.py
│   │   ├── minhas_reservas_view.py
│   │   ├── reservar_view.py
│   │   └── salas_view.py
│   ├── controllers/      
│   ├── services/
│   ├── models/                    
│   └── utils/
├── tests/
├── data/
│   ├── equipamentos.csv
│   ├── reservas.csv
│   ├── sala_equipamento.csv
│   ├── salas.csv
│   └── usuarios.csv
├── docs/
├── assets/
├── .gitignore
├── requirements.txt
├── main.py
└── README.md
```

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
streamlit run main.py
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
streamlit run main.py
```

