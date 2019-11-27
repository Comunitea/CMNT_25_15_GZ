# Buildout base para proyectos con Odoo y PostgreSQL
Odoo 11.0 en el base, PostgreSQL 12.1 y Supervisord 3.0
- Buildout crea cron para iniciar Supervisord después de reiniciar (esto no lo he probado)
- Supervisor ejecuta PostgreSQL, más info http://supervisord.org/
- También ejecuta la instancia de PostgreSQL
- Si existe un archivo dump.sql, el sistema generará la base de datos con ese dump
- Si existe  un archivo frozen.cfg es el que se debeía usar ya que contiene las revisiones aprobadas
- PostgreSQL se compila y corre bajo el usuario user (no es necesario loguearse como root), se habilita al autentificación "trust" para conexiones locales. Más info en more http://www.postgresql.org/docs/9.4/static/auth-methods.html
- Existen plantillas para los archivo de configuración de Postgres que se pueden modificar para cada proyecto.


# Uso (adaptado)
En caso de no haberse hecho antes en la máquina en la que se vaya a realizar, instalar las dependencias que mar Anybox
- Añadir el repo a /etc/apt/sources.list:
```
$ deb http://apt.anybox.fr/openerp common main
```
- Para firmar el repositorio
```
$ wget http://apt.anybox.fr/openerp/pool/main/a/anybox-keyring/anybox-keyring_0.2_all.deb
$ sudo dpkg -i anybox-keyring_0.2_all.deb
```
- Actualizar e instalar
```
$ sudo apt-get update
$ sudo apt-get install openerp-server-system-build-deps python3-dev python3-pip
```
- Para poder compilar e instalar postgres (debemos valorar si queremos hacerlo siempre), es necesario instalar el siguiente paquete (no es la solución ideal, debería poder hacerlo el propio buildout, pero de momento queda así)
```
$ sudo apt-get install libreadline-dev
$ sudo apt-get install libcups2-dev
```
- Crear un virtualenv dentro de la carpeta del respositorio. Esto podría ser opcional, obligatorio para desarrollo o servidor de pruebas, tal vez podríamos no hacerlo para un despliegue en producción. Si no está instalado, instalar el paquete de virtualenv. Es necesario tener la versión que se instala con easy_install o con pip, desinstalar el paquete python-virtualenv si fuera necesario e instalarlo con easy_install
```
$ sudo pip3 install virtualenv
$ virtualenv -p python3 sandbox
```
- Ahora procedemos a ehecutar el buildout en nuestro entorno virtual
```
$ sandbox/bin/python bootstrap.py -c [archivo_buildout]
$ bin/buildout -c [archivo_buildout]
```

- Puede que de error, hay que lanzar el supervisor y volver a hacer bin/buildout:
```
$ bin/supervisord
$ bin/buildout -c [archivo_buildout]
```
- Conectarse al supervisor con localhost:9001
- Si fuera necesario hacer update all, se puede parar desde el supervisor y en la consola hacer:
```
$ cd bin
$ ./upgrade_odoo
```
- odoo se lanza en el puerto 8069 (se pude configurar en otro)



## Configurar Odoo
Archivo de configuración: etc/odoo.cfg, si sequieren cambiar opciones en  odoo.cfg, no se debe editar el fichero,
si no añadirlas a la sección [odoo] del buildout.cfg
y establecer esas opciones .'add_option' = value, donde 'add_option'  y ejecutar buildout otra vez.

Por ejmplo: cambiar el nivel de logging de Odoo
```
'buildout.cfg'
...
[odoo]
options.log_handler = [':ERROR']
...
```

Si se quiere ejecutar más de una instancia de OpenERP, se deben cambiar los puertos,
please change ports:
```
odoo_xmlrpc_port = 8069  (8069 default odoo)
supervisor_port = 9001      (9001 default supervisord)
postgres_port = 5432        (5432 default postgres)
```

# Contributors

## Creators

Rastislav Kober, http://www.kybi.sk
