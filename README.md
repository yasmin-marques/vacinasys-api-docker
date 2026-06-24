# VacinaSys

API Web para gerenciamento de um sistema de vacinação, desenvolvida com **FastAPI**, **SQLModel**, **Alembic**, **PostgreSQL**, **SQLite** e **UV**.

---

## 1. Requisitos

Antes de executar o projeto, garanta que você possui os seguintes componentes instalados:

- **Python 3.12** ou superior
- **UV** — gerenciador de pacotes e ambientes
- **PostgreSQL** — caso utilize banco PostgreSQL local

### Verificar instalação do UV

```powershell
uv --version
````

### Verificar instalação do PostgreSQL

```powershell
psql --version
```

Caso o comando `psql` não funcione diretamente no Windows, utilize o caminho completo padrão:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" --version
```

---

## 2. Diretório de Execução

Todos os comandos listados neste documento devem ser executados na raiz do projeto.

---

## 3. Instalar Dependências

Para preparar o ambiente virtual e instalar todas as dependências necessárias, execute:

```powershell
uv sync
```

O comando `uv sync` utiliza os arquivos `pyproject.toml` e `uv.lock` para criar o ambiente do projeto.

> **Erro com PostgreSQL assíncrono?** Caso apareça um erro relacionado ao driver `asyncpg` após o `uv sync`, instale-o manualmente:
>
> ```powershell
> uv add asyncpg
> ```
>
> Isso é necessário para que a aplicação consiga se conectar ao PostgreSQL de forma assíncrona.

---

## 4. Configuração do Ambiente `.env`

Crie um arquivo chamado `.env` na raiz do projeto.

Mantenha apenas uma linha de `DATABASE_URL` ativa por vez.

### Exemplo com PostgreSQL assíncrono

```env
DATABASE_URL=postgresql+asyncpg://usuario:senha@host:5432/nome_do_banco
SQL_ECHO=true
```

### Exemplo com SQLite assíncrono

```env
DATABASE_URL=sqlite+aiosqlite:///./vacinasys.db
SQL_ECHO=true
```

---


## 5. Gerar a Migration

Com o banco criado e o `.env` configurado, gere a migration automaticamente:

```powershell
uv run alembic revision --autogenerate -m "criar tabelas"
```

Esse comando cria um novo arquivo de migration dentro de:

```text
migrations/versions/
```

---

## 6. Aplicar a Migration

Para criar as tabelas no banco configurado na `DATABASE_URL`, execute:

```powershell
uv run alembic upgrade head
```
> Verifique se o arquivo gerado tem em seu imports "import sqlmodel".
---

## 7. Conferir as Tabelas Criadas

Caso esteja usando PostgreSQL local, acesse o banco:

```powershell
psql -U postgres -d vacinasys
```

Ou, no Windows:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d vacinasys
```

Liste as tabelas:

```sql
\dt
```

Devem aparecer tabelas como:

* `usuarios`
* `pacientes`
* `profissionais_saude`
* `administradores`
* `vacinas`
* `lotes`
* `campanhas`
* `campanhas_vacinas`
* `aplicacoes`
* `documents`
* `alembic_version`

Para sair:

```sql
\q
```

---

## 8. Popular o Banco de Dados

Após criar as tabelas, execute o script de carga de dados:

```powershell
uv run python -m scripts.seed
```

O script utiliza o banco configurado no arquivo `.env`.

---

## 9. Executar a Aplicação

Com o ambiente instalado, o banco configurado e as tabelas criadas, inicialize o servidor de desenvolvimento:

```powershell
uv run fastapi dev app/main.py
```

Ou utilizando o Uvicorn diretamente:

```powershell
uv run uvicorn app.main:app --reload
```

---
## 10. Diagrama Mermaid



```mermaid
classDiagram
direction TB

class Usuario {
  id_usuario
  pnome
  unome
  email
  senha
  telefone
  cpf_usuario
}

class Administrador {
  id_admin
}

class Lote {
  id_lote
  data_chegada
  quantidade
  validade
  id_estoque
  codigo_vacina
  cnpj_fornecedor
}

class Vacina {
  codigo_vacina
  nome
  doenca
  quantidade_doses
  publico_alvo
  cnpj_fabricante
}

class Campanha {
  id_campanha
  nome_campanha
  data_inicio
  data_fim
  id_admin
}

class CampanhaVacina {
  id_campanha
  codigo_vacina
}

class Aplicacao {
  id_aplicacao
  data
  id_paciente
  id_profissional
  id_admin
  id_lote
  local
}

class Paciente {
  id_paciente
}

class ProfissionalSaude {
  id_profissional
  grau_formacao
}

class Document {
  id
  original_filename
  content_type
  extension
  size_bytes
  created_at
  id_campanha
}

Vacina "1" -- "*" Lote
Campanha "1" -- "*" CampanhaVacina
Vacina "1" -- "*" CampanhaVacina
Usuario "1" -- "0..1" Administrador
Usuario "1" -- "0..1" Paciente
Usuario "1" -- "0..1" ProfissionalSaude
Administrador "1" -- "*" Campanha
Paciente "1" -- "*" Aplicacao
ProfissionalSaude "1" -- "*" Aplicacao
Administrador "1" -- "*" Aplicacao
Lote "1" -- "*" Aplicacao
Campanha "1" -- "*" Document
```
