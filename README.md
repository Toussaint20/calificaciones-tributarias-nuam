Sistema Mantenedor Tributario NUAM
Este proyecto consiste en una plataforma web para la gestión, carga masiva, auditoría y exposición (API) de calificaciones tributarias.

El sistema ha sido contenerizado utilizando Docker para garantizar una ejecución consistente en cualquier entorno, eliminando problemas de dependencias o configuración local.

Requisitos Previos
Para ejecutar este proyecto, solo necesita tener instalado:

Docker Desktop (o Docker Engine + Docker Compose).

No es necesario instalar Python ni PostgreSQL localmente.

Instalación y Despliegue Rápido
Siga estos 4 pasos para levantar el sistema completo (Base de datos + Aplicación Web + API):

1. Descomprimir y abrir la terminal
Ubíquese en la carpeta raíz del proyecto (donde se encuentra el archivo docker-compose.yml).

2. Construir y levantar los contenedores
Ejecute el siguiente comando para descargar dependencias e iniciar el servidor: docker-compose up -d --build

Este proceso puede tardar unos minutos la primera vez mientras descarga las imágenes.

3. Aplicar migraciones y crear superusuario
Prepare la base de datos y cree su cuenta de administrador:

Crear las tablas en la base de datos
docker-compose exec web python manage.py migrate

Crear su usuario administrador (siga las instrucciones en pantalla)
docker-compose exec web python manage.py createsuperuser

4. Carga de Datos Iniciales (Seed Data)
IMPORTANTE: Ejecute estos comandos para configurar los perfiles de usuario y los parámetros tributarios necesarios para el funcionamiento del sistema.

Crear grupos de permisos (Auditor, Corredor, Analista)
docker-compose exec web python manage.py create_groups

Cargar catálogo de factores y conceptos tributarios
docker-compose exec web python manage.py seed_factores

Acceso al Sistema
Una vez desplegado, puede acceder a los distintos módulos en su navegador:

Aplicación Web (Login): http://localhost:8000/

Documentación API (Swagger): http://localhost:8000/api/docs/

Panel de Administración Django: http://localhost:8000/admin/

Credenciales y Seguridad (MFA)
El sistema cuenta con Autenticación de Dos Factores (2FA) obligatoria para todos los usuarios, cumpliendo con estándares de seguridad bancaria.

Al iniciar sesión por primera vez con su usuario, será redirigido a una pantalla de configuración.

Escanee el código QR con Google Authenticator (o similar).

Ingrese el código de 6 dígitos para vincular su dispositivo.

En futuros accesos, el sistema solicitará el código temporal después de la contraseña.

🛠 Características Técnicas
Backend: Python 3.12, Django 5.

Base de Datos: PostgreSQL 15.

API: Django Rest Framework (DRF) + Token Authentication.

Frontend: Django Templates + Bootstrap 5.

Infraestructura: Docker & Docker Compose.