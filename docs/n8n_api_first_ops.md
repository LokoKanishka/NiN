# n8n API-First Operations (Control Plane)

## Control Plane Canónico Elegido
Se ha adoptado **CLI Canónica (vía `docker exec`) + JSON Export/Import** como la vía principal y exclusiva para operar n8n de forma reproducible y auditable en el entorno de producción de BitNin.

## Por qué NO usar Browser/Mouse
La intervención dentro de n8n mediante Interfaz Gráfica (UI) y automatización visual (mouse tools) ha sido formalmente deprecada por los siguientes motivos críticos:
1. **Fragilidad extrema:** Los flujos se rompen por cambios sutiles en las coordenadas o renderizado del canvas.
2. **Lentitud operativa:** Requiere espera sincrónica de UI, rendering y modals interactivos.
3. **Falta de auditabilidad:** Los clicks no generan un "diff" atómico de configuración (qué parámetro exacto mutó).
4. **Propensión a fallos concurrentes:** Promueve ediciones in-place accidentales y solapadas.

## Comandos Básicos
Todo control de estado sobre n8n se delega al script consolidado `scripts/n8n_ctl.sh`:

- **Listar todos los IDs y nombres:**
  ```bash
  ./scripts/n8n_ctl.sh list
  ```
- **Exportar workflow (Lectura):**
  ```bash
  ./scripts/n8n_ctl.sh export <WORKFLOW_ID> ./backup_local.json
  ```
- **Importar / Actualizar workflow (Escritura):**
  ```bash
  ./scripts/n8n_ctl.sh import ./workflow_modificado.json
  ```

## Cómo intervenir el Workflow Narrativo de BitNin sin UI
Para efectuar *fixes* (e.g. errores de parseo JSON en nodos de Ollama), el flujo estricto es:
1. Obtener el workflow exportándolo en texto plano:
   `./scripts/n8n_ctl.sh export BAsjJe74dnlGcyrZ ./workflow_narrativo.json`
2. Utilizar herramientas clásicas (`jq`, reemplazo regex/texto multilínea) para realizar la modificación de forma predictiva sobre el JSON. 
3. Importar la configuración actualizada de vuelta al motor:
   `./scripts/n8n_ctl.sh import ./workflow_narrativo.json`
4. Validar la configuración exportando nuevamente y ejecutando un trigger real de prueba.

## Fallback Permitido (Último Recurso)
El acceso a la UI de n8n mediante subagentes de browser queda **estrictamente reservado como acción de último recurso**.
Sólo podrá invocarse si la CLI o el contenedor se encuentran en estado de falla total (e.g., base de datos SQLite corrupta que impide el arranque de los workers CLI de n8n) y debe ir precedido de una justificación explícita registrada en el log de auditoría.
