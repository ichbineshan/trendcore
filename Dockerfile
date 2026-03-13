FROM ubuntu:24.04

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV TZ=UTC

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get dist-upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    wget \
    software-properties-common \
    gnupg \
    ca-certificates \
    tzdata \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    pkg-config \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && cd /usr/local/bin \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl \
    git \
    bash \
    build-essential \
    gcc \
    g++ \
    libc6-dev \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    postgresql-client \
    libpython3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/trend-analysis

# Create and activate virtual environment
RUN python3 -m venv /srv/trend-analysis/venv
ENV PATH="/srv/trend-analysis/venv/bin:$PATH"
ENV VIRTUAL_ENV="/srv/trend-analysis/venv"

COPY ./requirements/requirements.txt .

# Install Python packages in virtual environment
RUN pip install setuptools wheel && pip install --no-cache-dir -r ./requirements.txt

COPY . .
RUN git rev-parse HEAD > gitsha 2>/dev/null || echo "no-git" > gitsha

WORKDIR /srv/trend-analysis

EXPOSE 80
RUN chmod +x ci-test.sh

ENTRYPOINT ["python3", "entrypoint.py"]
