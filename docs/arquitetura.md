# 5. Arquitetura Inicial

## 5.1 Estrutura de pastas

**reserva_salas_LarpTech/**
*   **app/**
    *   `views/`: telas do sistema (`detalhes_sala_view`, `home_view`, `login_view`, `minhas_reservas_view`, `reservar_view` e `salas_view`)
    *   `controllers/`: ligação entre as telas e as regras (reservas, salas, sessao e usuarios)
    *   `services/`: regras de negócio (`reservas_service`, `sala_service` e `usuarios_service`)
    *   `models/`: entidades e leitura dos dados (dados, reserva, sala e usuario)
    *   `utils/`: apoio (`sessao` e `salas_ocultas`)
*   **tests/**: testes automatizados (`test_reservas_service.py`)
*   **data/**: dados simulados em CSV (equipamentos, reservas, `sala_equipamento`, salas e usuarios)
*   **docs/**: documentação (`arquitetura.md`, `fluxo_usuario.md`, `modelo.png`, `modelo_dados.md` e `regras_negocio.md`)
*   **assets/**: logos e imagens
*   `main.py`, `requirements.txt`, `README.md` e `.gitignore`

## 5.2 Arquitetura em camadas (MVC)

O projeto segue o padrão MVC, estendido com uma camada de Service (MVCS). A figura abaixo mostra como as camadas se relacionam.

Responsabilidades de cada camada:

*   **main.py**: é o roteador. Define as páginas com `st.Page` e as executa com `st.navigation`. Quando não há usuário logado, mostra só a página de Login. Também monta a barra lateral, com a logo, o usuário logado e o botão Sair.
*   **views**: montam as telas. As ações do usuário (login, reservar, alterar, cancelar, aprovar e negar) são enviadas ao Controller. As telas de listagem (Home, Salas, Detalhes da Sala e Minhas Reservas) leem os dados diretamente pelas funções do Model.
*   **controllers**: recebem a ação vinda da View, chamam o Service, tratam os erros de validação e devolvem à View o resultado, com uma mensagem de sucesso ou de erro.
*   **services**: guardam a regra de negócio que envolve mais de uma entidade. Por exemplo, criar uma reserva exige checar a sala e as reservas existentes. Também gravam as alterações nos CSV.
*   **models**: trazem as entidades (Usuario, Sala e Reserva), com as validações de cada uma, e o `dados.py`, que faz a leitura dos CSV.
*   **data**: guarda os arquivos CSV, que funcionam como base de dados no N1.

## 5.3 Fluxo principal do usuário

*   **Login**: o usuário informa e-mail e senha. Se estiverem corretos e o usuário estiver ativo, ele entra no sistema. Caso contrário, aparece uma mensagem de erro.
*   **Home**: mostra a mensagem de boas-vindas, a próxima reserva do usuário e até cinco salas disponíveis, cada uma com um botão para reservar. O Admin também vê a área de Pendências, onde pode aprovar ou negar as reservas pendentes.
*   **Salas**: lista as salas, com filtros por disponibilidade, capacidade mínima e prédio, e um botão para ver os detalhes. O Admin também tem o botão de ocultar sala.
*   **Detalhes da Sala**: mostra capacidade, prédio, andar e status da sala, além de uma tabela com as reservas confirmadas.
*   **Reservar Sala**: o usuário escolhe a sala, a data e os horários de início e término. O sistema valida a reserva e informa se ela foi confirmada ou ficou pendente.
*   **Minhas Reservas**: lista as reservas do usuário e permite alterar a data e os horários ou cancelar as que estão confirmadas ou pendentes.
*   **Sair**: o botão fica na barra lateral e encerra a sessão.

## 5.4 Gerenciamento de estado

O estado da aplicação fica guardado no `st.session_state`. O login é tratado pelo arquivo `utils/sessao.py`. Os itens guardados na sessão são:

*   `usuario_logado`: o usuário que fez login;
*   `sala_pre_selecionada`: sala escolhida na Home para já aparecer na tela de reserva;
*   `sala_pre_selecionada_detalhes`: sala escolhida na lista de salas para já aparecer na tela de detalhes;
*   `indice_sala_reservar`: sala selecionada no formulário de reserva;
*   `pagina_reservar` e `pagina_detalhes_sala`: referências às páginas, usadas para trocar de tela pelos botões.

As mensagens de sucesso e de erro são exibidas na hora, e os filtros da tela de salas não ficam guardados na sessão.

## 5.5 Estratégia de dados simulados

Todos os dados ficam em arquivos CSV na pasta *data/*. A leitura é feita pelo `dados.py`, com a biblioteca pandas. Quando uma reserva, usuário ou sala é criado ou alterado, o *service* atualiza a tabela em memória e grava o resultado de volta no CSV. Os detalhes de cada arquivo estão na seção 6.
