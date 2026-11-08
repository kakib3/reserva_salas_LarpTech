# Contrato de retorno dos Services

As operações de escrita dos Services seguem uma convenção única:

- **Dados inválidos:** lançar `ValueError` com mensagem que explique a validação.
- **Regra de estado impede a operação:** retornar exatamente `False`. Exemplos: registro inexistente, estado incompatível, conflito ou duplicidade.
- **Sucesso:** retornar a entidade de domínio criada ou atualizada (`Reserva`, `Sala` ou `Usuario`), nunca apenas `True`.

## Exceções específicas

- `PermissionError` representa falha de autorização e permanece separado de `ValueError`.
- `ErroDeDados` representa falha de leitura/gravação do armazenamento e é convertido pelos Controllers em resposta amigável.

## Consultas e predicados

Esta convenção não transforma consultas em operações de escrita. Funções de busca podem retornar `None` quando não encontram um registro; listagens retornam seus dados; predicados como `checar_admin`, `verificar_email_disponivel`, `verificar_sala_disponivel` e `verificar_conflito_horario` continuam retornando booleanos.

## Controllers

Os Controllers identificam impedimentos usando `resultado is False`, tratam as exceções aplicáveis e, no sucesso, devolvem a entidade no terceiro elemento da tupla `(sucesso, mensagem, resultado)`. As Views podem ignorar esse terceiro elemento quando não precisam dos dados.
