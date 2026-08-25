FROM python:3.11-slim
RUN pip install --no-cache-dir requests beautifulsoup4 pandas numpy pytest
RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /home/sandbox