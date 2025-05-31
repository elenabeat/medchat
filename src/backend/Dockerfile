FROM huggingface/transformers-pytorch-gpu:latest

# Non-interactive so that installations do not ask for input
ENV debian_frontend=noninteractive

# Set the working directory
WORKDIR /app

# Copy python requirements and pip install
COPY requirements.txt requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flash-attn --no-build-isolation

# Copy the rest of the files
COPY . .

EXPOSE 5050

# Run the python script
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050"]