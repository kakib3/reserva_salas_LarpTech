# Testes de integração com MySQL

Estes testes rodam os *services* de verdade, com o `conexao.py` de verdade, contra
um banco **separado** (`..._test`). Os testes unitários da pasta `tests/` continuam
usando mocks e não precisam de banco.

## 1. Criar o banco de teste (uma vez)

No mesmo servidor do Aiven (assim o `ca.pem` e o SSL são os mesmos):

```sql
CREATE DATABASE larptech_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

O nome **precisa terminar em `_test`**. Os testes apagam e recriam as tabelas, e se o
nome não terminar assim a execução é abortada antes de tocar no banco.

## 2. Configurar as variáveis de ambiente

PowerShell:

```powershell
$env:LARPTECH_TEST_DB_HOST="SEU_HOST"
$env:LARPTECH_TEST_DB_PORT="3306"
$env:LARPTECH_TEST_DB_NAME="larptech_test"
$env:LARPTECH_TEST_DB_USER="SEU_USUARIO"
$env:LARPTECH_TEST_DB_PASSWORD="SUA_SENHA"
$env:LARPTECH_TEST_DB_SSL_CA="ca.pem"
```

Bash:

```bash
export LARPTECH_TEST_DB_HOST=SEU_HOST LARPTECH_TEST_DB_PORT=3306 \
       LARPTECH_TEST_DB_NAME=larptech_test LARPTECH_TEST_DB_USER=SEU_USUARIO \
       LARPTECH_TEST_DB_PASSWORD=SUA_SENHA LARPTECH_TEST_DB_SSL_CA=ca.pem
```

## 3. Rodar

```bash
python -m pytest -m integration        # só os de integração
python -m pytest -m "not integration"  # só os unitários (não precisam de banco)
python -m pytest                       # tudo; sem as variáveis, os de integração são pulados
```

Sem as variáveis, os testes desta pasta aparecem como *skipped*. É o que acontece no
GitHub Actions hoje, e por isso o CI não quebra.

## Como escrever um teste novo

1. **Monte os dados com as fábricas**, direto no banco (`criar_usuario_db`,
   `criar_sala_db`, `criar_reserva_db`) ou use `id_admin`, `id_professor`, `id_aluno`,
   `id_sala`, `id_lab`.
2. **Chame o service** que está sendo testado.
3. **Confira o resultado e o estado do banco** com a fixture `banco`
   (`banco.um(...)`, `banco.todos(...)`, `banco.contar(...)`). O banco é a fonte da
   verdade: não confie só no retorno da função.
4. Use `segunda` e `domingo` para datas (sempre no futuro, no fuso do app).
5. Use `emails` para conferir notificações: nenhum e-mail é enviado de verdade.

Cada teste começa com as tabelas vazias e os IDs recomeçando em 1.

## Cuidados

- `schema.sql` é uma **cópia** do schema real. Quando o banco mudar, gere
  `mysqldump --no-data` e atualize o arquivo, senão os testes passam contra um banco
  diferente do real.
- Os testes `xfail(strict=True)` em `test_schema_mysql.py` documentam lacunas
  conhecidas. Quando você corrigir a validação, o teste passa e o pytest avisa
  (XPASS); remova o marcador `xfail`.
- No CI (`.github/workflows/testes.yml`) estes testes ficam *skipped*, porque não há banco lá. Para rodá-los no CI seria preciso guardar as credenciais do banco de teste como *secrets* do GitHub e exportá-las como as variáveis acima.
- Não rode em paralelo (`pytest -n`): todos os testes compartilham o mesmo banco.
