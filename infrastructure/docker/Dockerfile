FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
# g++ is required at runtime, not just build time: PyTensor JIT-compiles its
# C backend on first NUTS sample. Without it every Bayesian BWM solve falls
# back to a much slower pure-Python path (measured: ~550s for a 2-agent,
# 1000-tune/1500-draw run instead of the expected tens of seconds).
RUN apt-get update && apt-get install --no-install-recommends -y g++ && rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 1000 survey && useradd --uid 1000 --gid survey --create-home survey
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=survey:survey src ./src
COPY --chown=survey:survey config ./config
ENV PYTHONPATH=/app/src
USER survey
ENTRYPOINT ["python", "-m", "symphysis.cli"]
CMD ["--help"]
