FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
RUN groupadd --gid 1000 survey && useradd --uid 1000 --gid survey --create-home survey
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=survey:survey src ./src
COPY --chown=survey:survey config ./config
ENV PYTHONPATH=/app/src
USER survey
ENTRYPOINT ["python", "-m", "agentic_survey.cli"]
CMD ["--help"]
