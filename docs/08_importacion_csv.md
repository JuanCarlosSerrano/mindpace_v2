# Importacion CSV MindPace v1

## Objetivo
Definir un CSV oficial para importar entrenamientos reales de forma segura y estable.

## Columnas obligatorias
```csv
fecha,distancia_km,tiempo_seg
```

## Columnas recomendadas
```csv
fecha,distancia_km,tiempo_seg,tipo,fc_media,ritmo_medio,sensacion,comentario
```

## Ejemplo
```csv
fecha,distancia_km,tiempo_seg,tipo,fc_media,ritmo_medio,sensacion,comentario
2026-01-15,12.0,2850,rodaje,158,237,7,Rodaje comodo
2026-01-17,8.5,2100,series,165,247,6,Series controladas
```
Ejemplo en archivo: `docs/examples/mindpace_csv_v1_example.csv`.

## Reglas por columna
| Columna | Regla |
| --- | --- |
| fecha | YYYY-MM-DD |
| distancia_km | > 0 |
| tiempo_seg | > 0 |
| tipo | opcional, rodaje/series/tempo/umbral |
| fc_media | opcional, 80-210 |
| ritmo_medio | opcional, seg/km (120-600) |
| sensacion | opcional, 1-10 |
| comentario | libre |

## Errores comunes
- Fecha invalida (formato incorrecto).
- Distancia o tiempo en cero.
- Duplicados dentro del CSV (fecha + distancia + tiempo).
- Sensacion fuera de 1-10.
- fc_media fuera de 80-210.
- tipo_sesion invalido (valores permitidos: rodaje/series/tempo/umbral).

## Uso del importador
```bash
python3 -m src.import.csv_import --csv /ruta/entrenos.csv --atleta 1
python3 -m src.import.csv_import --csv /ruta/entrenos.csv --plan 2
python3 -m src.import.csv_import --csv /ruta/entrenos.csv --plan 2 --strict
```

## Deteccion de duplicados
Primero se descartan duplicados dentro del CSV.
Despues se evita insertar si ya existe un realizado con:
- origen + actividad_id_externa, o
- fecha + distancia_km + tiempo_seg

## Modo estricto
Con `--strict` el importador detiene el proceso al primer error encontrado.

## Inferencia de tipo
Si `tipo`/`tipo_sesion` no se informa, el importador intentara inferirlo desde
`comentario` (rodaje/easy, series/intervalos, tempo, umbral/threshold).
