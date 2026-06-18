FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt ./requirements.txt
COPY task_requirements.tx[t]* ./task_requirements.txt
RUN touch task_requirements.txt

RUN pip install --upgrade pip --quiet \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && if [ -s task_requirements.txt ]; then \
    pip install --no-cache-dir --prefix=/install -r task_requirements.txt; \
    fi


FROM python:3.11-slim AS runtime

RUN useradd --no-create-home --shell /sbin/nologin --uid 1001 executor

WORKDIR /opt

COPY --from=builder /install /usr/local


COPY --chown=executor:executor . ./executor

USER executor

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt

CMD ["python", "-m", "executor.main"]
