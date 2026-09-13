# Cierre del módulo RAG

Abre esta carpeta de proyecto en VS Code. Los guiones PDF y Markdown están en material_clase.

## Ejecutar en la terminal integrada

```bash
source .venv/bin/activate
python -m unittest -v
./iniciar_clase.sh
```

El lanzador muestra la traza, la respuesta y las fuentes; guarda work/demo_final.json.
Requiere conexión a OpenAI y consume API. El reranker se ejecuta localmente.

## Orden para explicar

1. 16_retrieval_avanzado.py: recuperación sin respuesta generada.
2. retrieval_advanced.py: reescritura, BM25, vectores, RRF y reranker.
3. agente_rag.py: contrato, herramientas, ciclo, evidencia y referencias.
4. tools.py: estado y SLA simulados.
5. 17_agente_rag.py: CLI, traza y exportación.
6. test_agente_rag.py: siete pruebas del agente dentro de las 25 pruebas locales.

## Material

- Guion_Final_Agente_RAG.pdf: 120 minutos, con alternativas de 90 y 60.
- Guion_Final_Agente_RAG.md: editable y comandos copiables.
- Guion_Anterior_Retrieval_Avanzado.pdf: referencia anterior.
- ejecuciones_verificadas/: ensayos registrados; no presentarlos como respuestas en vivo.

Los documentos son sintéticos; estado y SLA no consultan SAP real.
El agente no ejecuta pagos ni reinicia sistemas. --history es contexto explícito,
no memoria persistente. Las citas se validan por ID; su fidelidad requiere revisión.
No compartas .env. Las respuestas del modelo pueden variar entre ejecuciones.
