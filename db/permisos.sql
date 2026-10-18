-- ==============================================================================
-- Usuario de aplicación con permisos mínimos (TT-2027-A183)
-- ==============================================================================
-- La aplicación no se conecta como 'postgres' (superusuario), sino con un rol
-- que solo puede leer y escribir datos en las tablas del sistema.
--
-- Lo ejecuta db/crear_base.ps1, que pasa las variables desde el archivo .env:
--   psql -d monitoreo_red -v app_user=... -v app_password=... -f db/permisos.sql
-- ==============================================================================

-- Crea el rol solo si no existe (psql \gexec ejecuta el texto generado).
SELECT format('CREATE ROLE %I LOGIN', :'app_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user')
\gexec

-- Sincroniza la contraseña con la del .env en cada ejecución.
ALTER ROLE :"app_user" WITH LOGIN PASSWORD :'app_password';

GRANT CONNECT ON DATABASE monitoreo_red TO :"app_user";
GRANT USAGE ON SCHEMA public TO :"app_user";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"app_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"app_user";

-- Las tablas que se creen después también quedan accesibles para la aplicación.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO :"app_user";
