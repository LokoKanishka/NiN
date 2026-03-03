#!/bin/bash
API_KEY=$(grep N8N_API_KEY /home/lucy-ubuntu/Escritorio/NIN/.env | cut -d '=' -f2)
curl -X POST "http://172.24.0.4:5678/api/v1/workflows" \
     -H "X-N8N-API-KEY: $API_KEY" \
     -H "Content-Type: application/json" \
     -d @/home/lucy-ubuntu/Escritorio/NIN/Flujo_Descargar_Libro_N8N.json
