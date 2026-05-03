FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY bitcointrader ./bitcointrader
COPY website ./website

RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["python", "-m", "bitcointrader.main", "--host", "0.0.0.0", "--port", "8080"]
