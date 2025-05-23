FROM python:3.11-slim

# Non-interactive so that installations do not ask for input
ENV debian_frontend=noninteractive

# Set the working directory
WORKDIR /app

# Copy python requirements and pip install
COPY requirements.txt requirements.txt 
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the files
COPY . .

EXPOSE 5050

# Run the python script
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5050"]