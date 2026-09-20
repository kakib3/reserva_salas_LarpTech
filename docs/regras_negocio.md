#  Regras de Negócio

As regras abaixo definem como o sistema deve se comportar nas reservas, nos status e nos perfis de usuário. Elas foram conferidas com o código e ajustadas onde havia diferença.

## 1. Regras de reserva

1. Uma sala só pode ser reservada por um usuário por vez no mesmo horário, sem sobreposição. Reservas canceladas não entram nessa verificação.
2. O horário de início deve ser anterior ao horário de fim.
3. A duração mínima de uma reserva é de 30 minutos.
4. A duração máxima de uma reserva é de 4 horas.
5. Só é permitido reservar salas com status Disponivel.
6. Não é permitido reservar salas com status Manutencao ou Indisponivel.
7. As reservas só podem ser feitas de segunda a sábado. O domingo não é permitido.
8. O horário permitido para reservas é das 07:00 às 22:00.
9. O usuário só pode cancelar reservas próprias que estejam com status Confirmada ou Pendente.
10. O usuário só pode alterar reservas próprias, e apenas enquanto o status for Confirmada ou Pendente.
11. Reservas de sala comum e de sala de reunião são criadas com status Confirmada automaticamente. Reservas de laboratório e de auditório entram como Pendente até que um usuário com perfil Admin as confirme.
12. Ao alterar uma reserva (data e horário), o sistema valida o conflito de horário novamente, como se fosse uma reserva nova.
13. Se a alteração envolver uma sala do tipo laboratório ou auditório, o status da reserva volta para Pendente, mesmo que estivesse Confirmada.
14. Se a alteração envolver uma sala comum ou de reunião, o status permanece ou volta para Confirmada. Como o status é recalculado a cada alteração, uma reserva de laboratório ou auditório também volta para Pendente quando só a data ou o horário mudam.

## 2. Regras de status

### Status da sala

*   **Disponivel**: a sala pode ser reservada.
*   **Manutencao**: a sala não pode ser reservada.
*   **Indisponivel**: a sala não pode ser reservada.

### Status da reserva

*   **Confirmada**: reserva ativa.
*   **Cancelada**: reserva cancelada pelo usuário ou negada por um Admin. O registro continua no histórico.
*   **Pendente**: reserva aguardando confirmação de um Admin.

### Status do usuário

*   **Ativo**: o usuário pode entrar no sistema.
*   **Inativo**: o usuário foi desativado e não consegue fazer login.

## 3. Regras de usuário

1. O acesso ao sistema é feito por login, com e-mail e senha conferidos com o cadastro em `usuarios.csv`. Sem login, só a tela de Login fica disponível.
2. O usuário logado fica guardado na sessão e é usado em todas as operações.
3. Apenas o próprio usuário pode alterar ou cancelar suas reservas.

## 4. Permissões e prioridade

*   Os **Admins** são os responsáveis por confirmar ou negar as reservas pendentes. Essa opção aparece na tela Home, na área de Pendências, e só é exibida para eles.
*   Somente os **Admins** veem o botão de ocultar salas na tela Salas.
*   Cadastrar, editar e desativar salas e usuários já existem na parte interna do sistema, mas ainda não têm tela.
*   A prioridade dos professores sobre os alunos em caso de conflito estava prevista para uma etapa futura e ainda não foi implementada.

## 5. Regras técnicas

1. Ao tentar criar uma reserva com conflito de horário, o sistema bloqueia a reserva e mostra uma mensagem de erro clara.
2. Ao cancelar uma reserva, o status muda para Cancelada. O registro não é apagado.
3. Os dados devem ser consistentes entre os arquivos CSV, ou seja, os IDs usados em um arquivo precisam existir no arquivo de origem.
