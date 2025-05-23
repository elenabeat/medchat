FROM huggingface/transformers-pytorch-gpu:latest

# Non-interactive so that installations do not ask for input
ENV debian_frontend=noninteractive

# Set the working directory
WORKDIR /app

# requirements first for layering
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the files
COPY . .

EXPOSE 8080

# Run the python script
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]