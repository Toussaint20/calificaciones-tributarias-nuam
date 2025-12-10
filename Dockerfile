# 1. IMAGEN BASE: Usamos Python 3.12 
FROM python:3.12-slim

# 2. VARIABLES DE ENTORNO
# Evita que Python genere archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Hace que los logs de Python se vean inmediatamente en la consola (útil para debug)
ENV PYTHONUNBUFFERED=1

# 3. DIRECTORIO DE TRABAJO
# Creamos una carpeta '/app' dentro del contenedor y nos movemos ahí
WORKDIR /app

# 4. DEPENDENCIAS DEL SISTEMA
# Instalamos las librerías de Linux necesarias para que funcione psycopg2 (Postgres)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. DEPENDENCIAS DE PYTHON
# Copiamos el archivo de requerimientos al contenedor
COPY requirements.txt /app/
# Instalamos las librerías
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6. CÓDIGO FUENTE
# Copiamos todo el resto de tu proyecto al contenedor
COPY . /app/

# 7. PUERTO
# Le decimos a Docker que este contenedor usará el puerto 8000
EXPOSE 8000

# 8. COMANDO DE INICIO
# Este es el comando que se ejecuta al levantar el contenedor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]