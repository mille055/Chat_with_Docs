
FROM python:3.8

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app 

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

# Run app.py when the container launches
CMD ["streamlit", "run", "app.py"]