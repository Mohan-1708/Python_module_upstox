# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port your Flask app runs on
EXPOSE 8000

# The command to run your application (assumes your file is main.py and flask object is named app)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]
