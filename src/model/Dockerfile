FROM huggingface/transformers-pytorch-gpu:latest

# Non-interactive so that installations do not ask for input
ENV debian_frontend=noninteractive

# Set the working directory
WORKDIR /app


# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install flash-attn --no-build-isolation

# Copy the rest of the files
COPY . .

EXPOSE 9090

# Run the python script
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9090"]