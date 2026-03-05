# Arquitectura del Bot de Trading Cuantitativo Autónomo (NiN v1)

**Estado:** Implementación de Fases 1, 2 y 3 Completada (Testing en Testnet).
**Orquestador:** n8n (Local)
**Motor Cognitivo:** Ollama (Local - RTX 5090)
**Exchange:** Binance (Testnet)

## Resumen Ejecutivo
El Bot de Trading Cuantitativo Autónomo es una convergencia de orquestación determinista (n8n) e inteligencia artificial generativa probabilística (LLM). Su propósito es ejecutar operaciones financieras aislando las decisiones cognitivas del procesamiento matemático para mitigar alucinaciones y riesgos de capital.

## Fases de Ejecución (Pipeline)

### Fase 1: Ingesta Sensorial
La etapa de recopilación de datos de mercado. Todas las llamadas suceden en paralelo antes de converger.
*   **Datos Cuantitativos:** API de CoinGecko (Precio actual, variación en 24 horas, volumen de BTC).
*   **Sentimiento Cualitativo:** API de Alternative.me (Índice de Miedo y Codicia).
*   **Narrativa de Entorno:** API de CryptoPanic (5 titulares recientes más relevantes).
*   *Consolidación:* Un nodo `Code` unifica los datos en un solo JSON estructurado para inyectarlo al prompt.

### Fase 2: Motor Cognitivo
El cerebro de la operación, estrictamente aislado de la red mediante ejecución local en la GPU.
*   **Inferencia:** Endpoint de chat de Ollama.
*   **Prompting Institucional:** El System Prompt fuerza a la IA a actuar como un trader cuantitativo institucional en un fondo de cobertura, evaluando los tres ejes de datos.
*   **Output Restringido (JSON Schema):** La IA tiene prohibido emitir texto libre. Solo puede devolver:
    *   `accion`: "COMPRAR", "VENDER" o "ESPERAR".
    *   `razonamiento`: Breve justificación en español.
    *   `confianza`: Un valor del 0 al 100.
    *   `riesgo`: Porcentaje sugerido de riesgo.

### Fase 3: Las Manos (Ejecución de Riesgo)
El puente criptográfico hacia el mercado.
*   **Enrutador Numérico (Switch):** Filtra la decisión de la IA. Si la acción es "ESPERAR" o contiene errores de formato, el flujo termina sin contacto externo.
*   **Filtro de Convicción:** Barrera estricta. Si la orden es de compra/venta pero la `confianza` de la IA es menor a 80/100, la orden se rechaza preventivamente.
*   **Sandbox Criptográfico (HMAC SHA-256):** Nodo de Node.js que toma el timestamp del servidor y construye la firma cifrada necesaria para la autenticación en exchanges profesionales, protegiendo las llaves secretas.
*   **Disparo (HTTP Request):** Envío asíncrono hacia Binance Testnet.

## Reglas de Construcción y Supervivencia (Antigravity)
1.  **Segregación Matemática:** Las matemáticas (Cálculo de RSI, TAMAÑO DEL LOTE) jamas ocurren en la mente de la IA. Se procesan estáticamente mediante nodos `Code` tradicionales en n8n.
2.  **Aislamiento de Entorno:** Ninguna orden vuela hacia Mainnet sin la alteración explícita del nodo Ejecutor. Todo opera en Testnet hasta validar un Sharpe Ratio positivo en >100 trades de prueba.
3.  **Memoria Distribuida:** El contexto del bot y sus resultados se inyectan en el Knowledge Graph para ser consultados y analizados en el futuro.
