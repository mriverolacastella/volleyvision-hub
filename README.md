# VolleyVision Hub V2.0

Versión reconstruida con motor de datos más estable para archivos DataVolley `.dvw`.

## Cómo ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Archivos importantes

- `app.py`: interfaz principal Streamlit.
- `dvw_parser.py`: parser y motor de métricas.
- `requirements.txt`: dependencias.

## Incluye

- Carga de uno o varios partidos `.dvw`.
- Validación básica de archivo.
- Match Report.
- Formaciones iniciales por set.
- Ataque, saque, recepción, bloqueo y distribución.
- Match Plan automático.
- Exportación Excel por módulos.

Creado por Marc Riverola Castellà.
