# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# RapidOCR downloads its models into its package directory on first use;
# fetching them here keeps them in the image instead of each new container.
RUN python -c "from rapidocr import RapidOCR; RapidOCR()"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]