FROM python:3.12.9-slim
ENV APP_HOME=/app
WORKDIR $APP_HOME
COPY pyproject.toml $APP_HOME/pyproject.toml
COPY poetry.lock $APP_HOME/poetry.lock
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --only main --no-root
COPY . .
EXPOSE 3000
CMD ["python", "main.py"]