# BitNin Signal Math Map

Este documento explica matemáticamente cómo el analista de BitNin (`bitnin_analyst/builder.py`) infiere su "Señal Compuesta" (`composite_signal`) y aplica salvaguardas (Guardrails) de seguridad. No hay "caja negra"; todo se computa linealmente sobre parámetros estrictos antes y después de interactuar con el LLM.

## 1. Fórmula de Convergencia (`composite_signal`)

La **Señal de Convergencia** (`convergence_score`) es el resultado de un modelo estadístico de suma ponderada diseñado para evitar que la máquina confíe ciegamente en un solo vector. 

Entradas (Inputs):
- `m_score` (Fuerza del Mercado): $P_m = 0.3$
- `n_score` (Soporte Narrativo): $P_n = 0.4$
- `mem_score` (Relevancia de Memoria RAG): $P_{mem} = 0.3$

Fórmula:
$Convergence = (m\_score \times 0.3) + (n\_score \times 0.4) + (mem\_score \times 0.3)$

### Desglose de Factores:
* **`m_score` (Market Strength):** 
  - Base: `0.5` si hay ruptura de rango (Breakout), caso contrario `0.3`.
  - Acelerador: Se suma el retorno absoluto de 1 día ponderado (`abs(return_1d) * 5`), con un tope máximo adicional de `0.5`. (Es decir, tope empírico alrededor de 1.0).
* **`n_score` (Narrative Support):** 
  - Extracción empírica de GDELT: el promedio de `relevance_btc` de los artículos recientes, ajustado logísticamente si hay muy pocos artículos (`min(1.0, count / 3)`). Tope `1.0`.
* **`mem_score` (Memory Relevance):** 
  - El score puro del vector RAG más alto extraído de Qdrant (`episodies_results`). Oscila en `[0.0, 1.0]`.

## 2. Clasificación de Umbrales (States)

El `convergence_score` final ubica la foto actual en un estado categórico:

- **`HIGH`** (Alta convergencia): Si `convergence > 0.7`. (Ocurre cuando el mercado rompe con fuerza, _y además_ hay base narrativa sustentable, _y además_ el pasado recuerda este patrón).
- **`DIVERGENT`** (Señal mixta o cruzada): Si `0.4 < convergence <= 0.7`.
- **`LOW`** (Ruido predominante): Si `convergence <= 0.4`.

## 3. Tipología Causal (Heurística Estricta)

Para describir el sesgo de la matriz, el sistema rotula un `causal_typology`:
- `narrativa_ausente`: Si la métrica narrativa general `n_score < 0.15`.
- `mercado_fuerte_narrativa_debil`: Si mercado alto (`m_score > 0.6`) pero humo narrativo ( `n_score < 0.4`). (Películas de ballenas o manipulación técnica).
- `narrativa_fuerte_mercado_debil`: Mucho ruido y FUD institucional (`n_score > 0.5`) pero precio estancado (`m_score < 0.4`).
- `ruido_predominante`: Convergence global bajo (`< 0.4`).

## 4. Guardrails Matemáticos (Salvaguardas Duras)

El sistema interviene activamente cortando alas a los output del LLM si desobedecen la prudencia matemática.

### Pre-LLM Guardrail (Ataja antes de consultar)
Si las condiciones son indignas de procesamiento, la salida es instantáneamente `insufficient_evidence` y la acción es `no_trade`.
- Cobertura de mercado pobre: `data_coverage_score < 0.75` (faltan velas).
- Ausencia analógica: Aparecen menos de `2` episodios análogos en memoria.
- Calidad analógica basura: El análogo `top_1` obtenido de Qdrant tiene un Cosine Similarity `< 0.5`.
- Ceguera narrativa: `narrative_coverage_score < 0.15`.

### Post-LLM Guardrail (Ataja la sobreconfianza o alucinación direccional)
Si el LLM propone operar (`long`, `short`, `hedge`, `reduce`), el código evalúa la intención contra el estado físico:
1. **Confianza estricta**: Si el campo `confidence < 0.55`, degrada forzosamente a `no_trade` (y añade nota de auditoría "downgraded to no_trade").
2. **Respaldo narrativo crudo**: Si `narrative_coverage_score < 0.15`, degrada forzosamente a `no_trade`. (El sistema se niega a operar a ciegas en lo informativo).
3. **Pobreza referencial condicional**: Si extrae menos de 2 episodios del RAG, o extrae solo 2 **pero** el LLM muestra un confidence pálido `< 0.7`, el guardrail prohíbe operar por falta de sustento analógico histórico concluyente (`too_few_analogues_for_directional_action`).

_**Nota sobre posible sesgo de diseño:**_ La formulación del `m_score` (`abs(return) * 5`) asume que un retorno del ~10% satura la influencia del mercado. Valores masivos de volatilidad no ponderan más arriba del `0.5` adicional, lo cual previene hiperactividad espasmódica. Adicionalmente, el recorte narrativo fuerte a `0.15` en Fase 29R fue intencionalmente endurecido ("Refinado v1") para aumentar el escepticismo de la máquina.
