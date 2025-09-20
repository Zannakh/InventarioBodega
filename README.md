# 📦 Prueba Inventario (Django + MySQL)

Sistema de gestión de inventario desarrollado en **Django 5.2** con conexión a **MySQL/MariaDB**.  
Permite administrar productos, proveedores, bodegas, categorías y movimientos de stock con validaciones y un histórico de operaciones.

---

## 🚀 Requisitos

- ✅ Python **3.13+**
- ✅ Django **5.2**
- ✅ MySQL / MariaDB (se puede usar PostgreSQL con mínimos cambios)
- ✅ pipenv o venv (recomendado)

---

## ⚙️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Zannakh/InventarioBodega
   cd Prueba_Inventario
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**  
   Crear un archivo **`.env`** en la raíz del proyecto con el siguiente contenido:

   ```env
   DB_NAME=inventario_db
   DB_USER=root
   DB_PASSWORD=tu_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   SECRET_KEY=django-inventario-secret-key
   DEBUG=True
   ```

---

## 🗄️ Migraciones

1. Crear migraciones:
   ```bash
   python manage.py makemigrations inventario_core
   ```

2. Aplicar migraciones:
   ```bash
   python manage.py migrate
   ```

3. Crear superusuario:
   ```bash
   python manage.py createsuperuser
   ```

---

## ▶️ Ejecución

Iniciar el servidor:
```bash
python manage.py runserver
```

Abrir en navegador:  
👉 [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📋 Funcionalidades

- 🛠️ **CRUD completo** de:
  - Productos  
  - Categorías  
  - Proveedores  
  - Bodegas  

- 🔄 **Movimientos de stock**
  - Entradas  
  - Salidas  

- 🚫 **Validación automática**: el stock nunca puede quedar en negativo.  
- 📜 **Histórico de movimientos** (log) para cada producto.  
- 🎨 **Interfaz admin personalizada** con filtros y búsqueda avanzada.  

---

## 🧪 Pruebas

- ✔️ Registrar una **entrada** y verificar que aumenta el stock.  
- ❌ Intentar registrar una **salida mayor al stock disponible** → muestra advertencia clara.  
- 📊 Revisar **histórico de movimientos** desde el admin.  
- 🔎 Crear productos y verificar que los movimientos actualizan el stock en tiempo real.  

---

## 👤 Autor

Proyecto académico desarrollado por **Felipe Larrañaga**  
📍 INACAP – Estudiante Técnico Analista Programador 2025
