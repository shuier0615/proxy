FROM python:3.9-slim

# Install system packages with Aliyun mirror
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils && echo "deb http://mirrors.aliyun.com/debian/ bookworm main non-free non-free-firmware" > /etc/apt/sources.list && echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main" >> /etc/apt/sources.list && echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main non-free non-free-firmware" >> /etc/apt/sources.list && apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Set pip configuration to use multiple mirrors via environment variables
ENV PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_EXTRA_INDEX_URL=https://mirrors.aliyun.com/pypi/simple

COPY requirements.txt /app/requirements.txt

WORKDIR /app
COPY . .
# Install Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/logs

EXPOSE 5000

CMD ["python", "main.py"]