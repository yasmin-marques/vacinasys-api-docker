FROM python:3.12-slim

WORKDIR /app

# Instala o uv
RUN pip install uv

# Copia os arquivos de dependências primeiro
COPY pyproject.toml uv.lock ./

# Instala as dependências
RUN uv sync --frozen

# Copia o restante do projeto
COPY . .

# Expõe a porta da API
EXPOSE 8000

# Inicializa a aplicação
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]