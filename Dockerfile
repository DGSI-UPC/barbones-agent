# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN python -m pip install --upgrade pip && \
    echo "---- Contents of requirements.txt during build ----" && \
    cat requirements.txt && \
    echo "--------------------------------------------------" && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "---- Verifying bs4 installation during build ----" && \
    python -c "from bs4 import BeautifulSoup; print('SUCCESS: bs4.BeautifulSoup imported successfully during build.')" && \
    echo "--------------------------------------------------"

# Copy the current directory contents into the container at /app
COPY tools.py .

# Run tools.py when the container launches
CMD ["python", "tools.py"]
