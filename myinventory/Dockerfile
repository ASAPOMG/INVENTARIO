# Usar una imagen base oficial de Python
FROM python:3.12-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos requeridos para instalar las dependencias
COPY requirements.txt requirements.txt

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos de la aplicación
COPY . .

# Exponer el puerto en el que la aplicación correrá
EXPOSE 8000

# Configurar la variable de entorno para la configuración de producción de Django
ENV DJANGO_SETTINGS_MODULE=myinventory.settings

# Comando para iniciar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myinventory.wsgi:application"]
