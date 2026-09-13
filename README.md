# Sesiones del módulo 2: Context Engineering y Retrieval Avanzado

Material práctico para ejecutar en VS Code y Python. La sesión 06 continúa el recorrido de parsing, OCR, chunking y búsqueda vectorial con BM25, Hybrid Search, RRF, reranking, Query Rewriting, Multi-Query y HyDE.

## Empezar

```bash
git clone https://github.com/jpcorona/sesiones-modulo-2.git
cd sesiones-modulo-2
python -m venv .venv
```

Activa el entorno:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`

```bash
python -m pip install -r requirements.txt
```

Usa Python 3.11 o superior. Copia `.env.example` como `.env` y completa tu propia clave de OpenAI. No compartas ese archivo.

## Primera búsqueda sin llamadas a OpenAI

El repositorio incluye un índice de demostración con 11 chunks de cinco PDFs sintéticos.

```bash
python 09_busqueda_bm25.py --query "F110-031" --top-k 5
```

BM25 utiliza el índice local y no necesita una clave. Las búsquedas vectoriales y las transformaciones generativas sí utilizan OpenAI. El reranker se descarga de Hugging Face y luego se ejecuta localmente.

## Preparación y recorrido de clase

Consulta [la guía completa de ejecución](README.txt) para la secuencia de 120 minutos y todos los comandos.

- `00b_generar_docs_retrieval.py`: genera los tres PDFs adicionales.
- `07_indexar_documentos.py`: reconstruye el índice; vuelve a procesar todos los PDFs y utiliza OpenAI.
- `08_consultar_indice.py`: baseline vectorial.
- `09_busqueda_bm25.py` a `16_retrieval_avanzado.py`: demostraciones progresivas.
- `retrieval_advanced.py`: funciones compartidas para explicar por bloques.

El índice incluido fue generado previamente. Para búsqueda vectorial, usa el mismo modelo de embeddings con que se creó; el formato JSON educativo no guarda el nombre del modelo. Si no conoces ese dato o cambias de modelo, reconstruye el índice con tu configuración antes de consultar. BM25 no requiere esa reconstrucción.

```bash
python -c "from retrieval_advanced import load_reranker; load_reranker(); print('reranker OK')"
python 16_retrieval_avanzado.py --query "Error F110-031 SAP" --candidate-k 20 --top-k 5
```

## Pruebas

```bash
python -m unittest -v
```

Las pruebas no hacen llamadas a OpenAI ni descargan modelos. Los documentos SAP son ejemplos sintéticos para enseñanza, no documentación operativa oficial.

## Cierre: agente RAG con herramientas

La demo final conecta el retrieval avanzado con la generación de respuestas y las
herramientas simuladas de estado y SLA. El modelo decide cuáles consultar.

```bash
python 17_agente_rag.py --query "Que indica el boletin sobre F110-031?" --trace
python 17_agente_rag.py --query "Incidente de criticidad alta en ERP con error F110-031. Consulta estado y SLA, y explica que revisar segun la documentacion." --trace --json-output work/demo_final.json
```

`agente_rag.py` devuelve respuesta, fuentes con página y chunk_id, eventos y latencia.
`--history` recibe contexto explícito; no hay memoria persistente entre comandos.
`--top-k`, `--candidate-k` y `--no-rewrite` permiten comparar la recuperación.
La traza puede contener consultas y texto documental: usa los datos sintéticos de clase.
Los IDs de cita se validan; esto no verifica que cada afirmación esté respaldada.
El agente permite tres rondas de herramientas y reserva una llamada final sin ellas;
si una cita tiene un ID inválido, permite una corrección adicional sin herramientas.
No existen acciones de escritura ni conexión operativa a SAP. Las consultas al modelo
son reales y consumen API. Ejecuta `python -m unittest -v` para los contratos sin red.
