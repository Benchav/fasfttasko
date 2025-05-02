# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del proyecto al contenedor
COPY . /app

# Instala las dependencias necesarias desde el requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expón el puerto en el que correrá la app
EXPOSE 8000

# Comando para iniciar el servidor con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT", "--workers", "4"]
