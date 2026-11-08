# 1. Start from official lightweight Python Linux
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy all your project files into the container
COPY . .

# 5. Tell Docker to open port 8000
EXPOSE 8000

# 6. The command to run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]