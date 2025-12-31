# Stage 1: Base (runtime dependencies only)
FROM python:3.10-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libportaudio2 \
    libasound2 \
    libpulse0 \
    pulseaudio-utils \
    xclip \
    libcairo2 \
    libgirepository-1.0-1 \
    gir1.2-gtk-3.0 \
    gir1.2-notify-0.7 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Builder (with build tools)
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    cmake \
    git \
    libcairo2-dev \
    libgirepository1.0-dev \
    libportaudio2 \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Runtime
FROM base AS runtime

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN mkdir -p src/logs src/data_memory/user src/data_memory/cache \
    src/data_memory/emotional_states src/data_memory/proactive src/sessions

RUN useradd -m -s /bin/bash luna && \
    chown -R luna:luna /app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TERM=xterm-256color

ENTRYPOINT ["python", "main.py"]
CMD ["--skip-onboarding"]
