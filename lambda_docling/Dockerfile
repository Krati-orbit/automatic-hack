# AWS Lambda Container Image for Docling Document Processor
FROM public.ecr.aws/lambda/python:3.11

# Install system libraries needed by Docling, Cairo, and PDF parsers
RUN yum update -y && \
    yum install -y \
    gcc \
    gcc-c++ \
    make \
    glib2-devel \
    pango \
    cairo \
    libffi-devel \
    poppler-utils \
    tar \
    gzip && \
    yum clean all

WORKDIR ${LAMBDA_TASK_ROOT}

# Install CPU-only PyTorch to minimize image footprint and optimize memory
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install Docling and PDF processing requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler code
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Set Lambda execution handler
CMD [ "handler.handler" ]
