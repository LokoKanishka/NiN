# Instrucciones del Orquestador Antigravity (Meta-Nivel)

## Bot de Trading Algorítmico (n8n + RTX 5090)

### 1. Ejecución Silenciosa
*   Las herramientas de orquestación MCP deben ejecutarse SIN comentarios intermedios ni respuestas verborrágicas.
*   El objetivo es la velocidad de ensamblado del flujo en n8n.

### 2. Paralelización Estricta
*   Las ramas de adquisición de datos (Fase 1) DEBEN construirse y ejecutarse en paralelo (ej. CoinGecko, CryptoPanic, Alternative.me simultáneamente).
*   No encadenar peticiones HTTP independientes.

### 3. Configuración Explícita y Validación
*   **PROHIBIDO confiar en los valores por defecto de los nodos.**
*   Todos los parámetros (URLs, headers, métodos, expresiones TERNARIAS JSON) deben configurarse explícitamente.
*   **Patrón Obligatorio de Construcción:**
    1.  `validate_node(mode='minimal')`
    2.  (...agregar variables...)
    3.  `validate_workflow` antes de implementar o activar.

### 4. Enrutamiento Condicional
*   Cualquier nodo que tome decisiones (ej. `Switch`, `IF`) DEBE configurar explícitamente el parámetro `branch` (true/false) en sus conexiones.
*   La omisión de este paso provoca cruces críticos de señales en el entorno de trading.
