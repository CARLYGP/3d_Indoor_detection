"""Convierte docs/resultados/detections.txt (salida de SpatialLM) en src/datos.json para el video de Remotion.

El archivo es la salida real del pipeline sobre la sala del informe, transcrita de la figura del paper.
Uso (desde la raíz del repo):  python docs/video/exportar.py
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TXT = AQUI.parent / "resultados" / "detections.txt"


def main():
    paredes, puertas, cajas, lineas = [], [], [], []
    for linea in TXT.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        lineas.append(linea)
        nombre, tipo, args = re.match(r"(\w+)=(\w+)\((.*)\)", linea).groups()
        partes = args.split(",")
        if tipo == "Wall":
            x1, y1, z1, x2, y2, z2, alto, _ = map(float, partes)
            if abs(x1 - x2) + abs(y1 - y2) < 1e-6:
                continue  # pared de longitud cero (wall_2): no se dibuja
            paredes.append({"id": nombre, "a": [x1, y1], "b": [x2, y2], "z": z1, "h": alto})
        elif tipo == "Door":
            x, y, z, ancho, alto = map(float, partes[1:])
            puertas.append({"id": nombre, "pared": partes[0], "c": [x, y, z], "w": ancho, "h": alto})
        elif tipo == "Bbox":
            x, y, z, giro, sx, sy, sz = map(float, partes[1:])
            cajas.append({"id": nombre, "clase": partes[0], "c": [x, y, z], "giro": giro, "s": [sx, sy, sz]})
    n_paredes = sum(1 for l in lineas if "=Wall(" in l)
    datos = {"paredes": paredes, "puertas": puertas, "cajas": cajas, "lineas": lineas, "nParedes": n_paredes}
    (AQUI / "src" / "datos.json").write_text(json.dumps(datos, indent=1), encoding="utf-8")
    print(f"{n_paredes} paredes ({len(paredes)} con longitud), {len(puertas)} puerta, {len(cajas)} objetos")


if __name__ == "__main__":
    main()
