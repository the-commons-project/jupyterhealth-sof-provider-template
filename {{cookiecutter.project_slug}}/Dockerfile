FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY provider_app ./provider_app
COPY dashboard.ipynb jupyter_server_config.py voila.json ./

ENV JUPYTER_CONFIG_DIR=/app
EXPOSE 8888

CMD ["jupyter", "server", "--ip=0.0.0.0", "--port=8888", "--no-browser", \
     "--config=/app/jupyter_server_config.py"]
