# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Install base dependencies
RUN apt-get update && apt-get install -y \
   	curl \
    gnupg \
    software-properties-common \
    wget \
    lsb-release

# Install grpcurl for debugging
RUN curl -L https://github.com/fullstorydev/grpcurl/releases/download/v1.8.7/grpcurl_1.8.7_linux_x86_64.tar.gz  | tar -xz -C /usr/local/bin

# Install Terraform
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
RUN wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
RUN gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint
RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list
RUN apt update
RUN apt-get install -y terraform

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy poetry files first (for layer caching)
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install

# Copy the core Python files and modules
COPY worker.py starter.py ./
COPY shared/ ./shared/
COPY workflows/ ./workflows/

# Copy Terraform configurations
COPY terraform/ ./terraform/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the worker
CMD ["poetry", "run", "python", "worker.py"]