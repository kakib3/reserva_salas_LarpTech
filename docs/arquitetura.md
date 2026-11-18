# Arquitetura Inicial

## 1. Estrutura de pastas

**reserva_salas_LarpTech/**
*   **app/**
    *   `views/`: telas do sistema (`detalhes_sala_view`, `gerenciar_salas_view`, `gerenciar_usuarios_view`, `home_view`, `login_view`, `minhas_reservas_view`, `reservar_view` e `salas_view`)
    *   `controllers/`: ligação entre as telas e as regras (reservas, salas e usuarios)
    *   `services/`: regras de negócio (`reservas_service`, `sala_service` e `usuarios_service`)
    *   `models/`: entidades e conexão com o banco (conexao, constantes, dados, reserva, sala e usuario)
    *   `utils/`: apoio (`sessao`, `salas_ocultas`, `mensagens`, `excecoes`, `formatacao`, `horarios`, `relogio` e `seguranca`)
    *   `messaging/`: notificações do sistema (envio de e-mail e mensagens de reserva - confirmada, pendente, aprovada e recusada).
*   **tests/**: testes automatizados. Os unitários ficam em `tests/` (usam mocks e não precisam de banco) e os de integração em `tests/integration/` (usam um MySQL de teste; veja o README da pasta)
*   **docs/**: documentação (`arquitetura.md`, `contrato_services.md`, `modelo.png`, `modelo_dados.md` e `regras_negocio.md`)
*   **assets/**: logos e imagens
*   `main.py`, `requirements.txt`, `README.md` e `.gitignore`

## 2. Arquitetura em camadas (MVC)

O projeto segue o padrão MVC, estendido com uma camada de Service (MVCS). A figura abaixo mostra como as camadas se relacionam.

Responsabilidades de cada camada:

*   **main.py**: é o roteador. Define as páginas com `st.Page` e as executa com `st.navigation`. Quando não há usuário logado, mostra só a página de Login. Também monta a barra lateral, com a logo, o usuário logado e o botão Sair.
*   **views**: montam as telas. As ações do usuário (login, reservar, alterar, cancelar, aprovar e negar) são enviadas ao Controller. As telas de listagem (Home, Salas, Detalhes da Sala e Minhas Reservas) também consultam os dados pelo Controller. As views não decidem regras de negócio: permissões, visibilidade de salas, status das reservas e validações dos formulários chegam prontos do Controller/Service.
*   **controllers**: recebem a ação vinda da View, chamam o Service, tratam os erros de validação e de acesso ao banco (decorator `tratar_erro_de_dados`, que também registra a causa no log) e devolvem à View o resultado, com uma mensagem de sucesso ou de erro.
*   **services**: guardam a regra de negócio que envolve mais de uma entidade. Por exemplo, criar uma reserva exige checar a sala e as reservas existentes. Também fazem as consultas e gravações no banco MySQL.
*   **models**: trazem as entidades (Usuario, Sala e Reserva), com as validações de cada uma, e a `conexao.py`, que mantém o pool de conexões com o MySQL. Os modelos também validam os limites das colunas do banco (por exemplo, nome de sala com até 10 caracteres).
*   **messaging**: são disparadas pelos services após a persistência, de forma tolerante a falhas (uma falha no envio não compromete a operação principal).
*   **banco de dados**: MySQL, acessado com `mysql-connector-python`. As credenciais ficam em `.streamlit/secrets.toml`, que não é versionado.

## 3. Fluxo principal do usuário

*   **Login**: o usuário informa e-mail e senha. Se estiverem corretos e o usuário estiver ativo, ele entra no sistema. Caso contrário, aparece uma mensagem de erro.
*   **Home**: mostra a mensagem de boas-vindas, a próxima reserva do usuário e até cinco salas disponíveis, cada uma com um botão para reservar. O Admin também vê a área de Pendências, onde pode aprovar ou negar as reservas pendentes.
*   **Salas**: lista as salas, com filtros por disponibilidade, capacidade mínima e prédio, e um botão para ver os detalhes. O Admin também tem o botão de ocultar sala.
*   **Detalhes da Sala**: mostra capacidade, prédio, andar e status da sala, além de uma tabela com as reservas confirmadas e pendentes (que ocupam o horário) e os horários livres do dia.
*   **Reservar Sala**: o usuário escolhe a sala, a data e os horários de início e término. O sistema valida a reserva e informa se ela foi confirmada ou ficou pendente.
*   **Minhas Reservas**: lista as reservas do usuário e permite alterar a data e os horários ou cancelar as que estão confirmadas ou pendentes.
*   **Sair**: o botão fica na barra lateral e encerra a sessão.

## 4. Gerenciamento de estado

O estado da aplicação fica guardado no `st.session_state`. O login é tratado pelo arquivo `utils/sessao.py`. Os itens guardados na sessão são:

*   `usuario_logado`: o usuário que fez login;
*   `sala_pre_selecionada`: sala escolhida na Home para já aparecer na tela de reserva;
*   `sala_pre_selecionada_detalhes`: sala escolhida na lista de salas para já aparecer na tela de detalhes;
*   `indice_sala_reservar`: sala selecionada no formulário de reserva;
*   `pagina_reservar` e `pagina_detalhes_sala`: referências às páginas, usadas para trocar de tela pelos botões.

As mensagens de ações que recarregam a página (aprovar, cancelar, ocultar, cadastrar...) são agendadas com `utils/mensagens.py` e exibidas uma única vez na renderização seguinte, porque um `st.success()` seguido de `st.rerun()` desapareceria antes de ser lido. Os filtros da tela de salas não ficam guardados na sessão.

## 5. Persistência dos dados

Os dados ficam em um banco MySQL, nas tabelas `usuarios`, `salas` e `reservas` (veja `modelo.png`). A conexão é feita por um pool (`models/conexao.py`) e cada *service* abre e fecha a conexão a cada operação. Falhas do banco chegam ao usuário como mensagem amigável, e a causa real é registrada no log. A lista de salas ocultas não é persistida: fica em memória (`utils/salas_ocultas.py`).
