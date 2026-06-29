# Executando o projeto

## Pré-requisitos

Antes de executar a aplicação, certifique-se de possuir instalado:

* Docker
* Docker Compose
* uv (gerenciador de dependências Python)

Também é necessário criar um arquivo `.env` na raiz do projeto utilizando o `.env.example` como base.

---

# Subindo a aplicação

Com o Docker em execução, basta executar:

```bash
docker compose up --build
```

Na primeira execução, o Docker irá:

* construir a imagem da API;
* baixar as imagens do MongoDB e do MinIO;
* criar os volumes persistentes;
* iniciar todos os serviços.

Nas próximas execuções, o comando abaixo normalmente é suficiente:

```bash
docker compose up
```

Para executar em segundo plano:

```bash
docker compose up -d
```

Para interromper os containers:

```bash
docker compose down
```

Para ver as dependências instaladas nos containers:

```bash
docker compose exec api uv pip list
```

Para realizar testes com o mesmo ambiente (.venv) do Dockerfile:

```bash
docker compose exec api uv run python -m app.tests.test_document
```

---

# Serviços disponíveis

Após a inicialização, os serviços estarão disponíveis nos seguintes endereços.

## API FastAPI

```
http://localhost:8000
```

Endpoint de teste:

```
GET /
```

Resposta esperada:

```json
{
    "message": "VacinaSys API funcionando.",
    "database": "MongoDB",
    "odm": "Beanie"
}
```

---

## Documentação Swagger

A documentação automática da API pode ser acessada em:

```
http://localhost:8000/docs
```

Nela é possível:

* visualizar todos os endpoints;
* testar requisições diretamente pelo navegador;
* consultar os modelos de entrada e saída.

Também está disponível a documentação ReDoc:

```
http://localhost:8000/redoc
```

---

## Console do MinIO

O console administrativo do MinIO está disponível em:

```
http://localhost:9001
```

Credenciais padrão:

```
Usuário: minioadmin
Senha:   minioadmin
```

Após o login é possível:

* visualizar os buckets;
* verificar os arquivos enviados;
* remover arquivos;
* acompanhar os uploads realizados pela aplicação.

---

## API S3 do MinIO

A API compatível com S3 está disponível em:

```
http://localhost:9000
```

Esse endpoint é utilizado exclusivamente pela aplicação FastAPI para armazenar e recuperar arquivos.

---

## MongoDB

O MongoDB está disponível na porta:

```
mongodb://localhost:27017
```

Quando a aplicação é executada através do Docker Compose, a comunicação entre os containers utiliza o nome do serviço:

```
mongodb://mongo:27017
```

conforme definido no arquivo `.env`.

---

# Estrutura dos containers

O ambiente Docker é composto por três serviços:

* **api**: aplicação FastAPI.
* **mongo**: banco de dados MongoDB.
* **minio**: armazenamento de documentos.

Todos os serviços se comunicam pela rede interna do Docker Compose utilizando os nomes dos serviços (`api`, `mongo` e `minio`), sem utilizar `localhost` internamente.

---

# Persistência dos dados

O projeto utiliza volumes Docker para garantir a persistência dos dados.

* **mongo-data**: armazena os dados do MongoDB.
* **minio-data**: armazena os arquivos enviados ao MinIO.

Assim, mesmo após reiniciar ou remover os containers, os dados permanecem armazenados.

---

# Arquivos enviados

Os documentos enviados pela API são armazenados fisicamente no MinIO.

O MongoDB armazena apenas os metadados dos documentos, conforme especificado nos requisitos do projeto.

Os arquivos físicos são identificados pelo próprio identificador do documento, permitindo que o nome original seja alterado sem impactar o armazenamento.
