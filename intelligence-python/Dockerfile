FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY idt_intelligence ./idt_intelligence
RUN pip install --no-cache-dir ".[server]"
ENV IDT_LLM=mock
EXPOSE 8000
CMD ["idt-intelligence", "serve", "--host", "0.0.0.0", "--port", "8000"]
