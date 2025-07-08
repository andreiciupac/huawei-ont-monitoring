# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install the libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your Python script files into the container
COPY . .

# The command to run when the container starts
CMD ["python3", "main.py"]