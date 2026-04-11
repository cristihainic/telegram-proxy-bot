FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/proxybot
WORKDIR /proxybot
COPY . /proxybot/
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        pip install ".[dev]"; \
    else \
        pip install .; \
    fi && \
    rm -rf build/
EXPOSE 80

CMD ["python", "bot/app.py"]
