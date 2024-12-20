# Python image to use.
FROM python:3.12

# Update sistem dan install Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# copy the requirements file used for dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the working directory contents into the container at /app
COPY . .

# Run main.py when the container launches
# CMD uvicorn main:app --host 0.0.0.0 --port $PORT
ENTRYPOINT ["python3", "main.py"]