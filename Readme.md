#  3D Indoor Reconstruction Pipeline  
### MASt3R-SLAM + SpatialLM + Herramientas Personalizadas (resize / painting / viz)

Este repositorio integra un pipeline completo para reconstrucción 3D a partir de video en interiores, obteniendo:

- Una **nube de puntos densa** generada por **MASt3R-SLAM**  
- Detección de **paredes, ventanas, puertas y estructura 3D** usando **SpatialLM**  
- Post-procesamiento personalizado (rescale, coloreo, visualización final)  

Todo automatizado en `main.py`.

---

## 📁 Estructura del repositorio

```
├── main.py
├── requirements.txt
│
├── src/
│   ├── resize.py
│   ├── walls_to_surface.py
│   └── viz_total.py 
│   └── recon.py # Modificación archivo del modelo SLAM3R para que devuelva formato ply
│
│
├── slam3r/                     # EL USUARIO DEBE CLONAR AQUÍ
│   └── recon.py                # Debe ser reemplazado por la versión modificada
│
└── spatiallm/                  # EL USUARIO DEBE CLONAR AQUÍ
    ├── run_inference.py
    └── checkpoints/
```

---

## 🔧 Instalación

### 1. Crear entorno, instalar dependencias y ejecutar pipeline

```
conda create -n recon3d python=3.10 -y
conda activate recon3d
pip install -r requirements.txt
python main.py

```

---

## 📥 Clonar SLAM3R y SpatialLM dentro del repositorio

### 1. Clonar SLAM3R:

```
git clone https://github.com/naver/mast3r-slam.git slam3r
```

### 2. Clonar SpatialLM:

```
git clone https://github.com/Yinjiayudong/SpatialLM.git spatiallm
```

---

## ⚠️ Modificación obligatoria de `slam3r/recon.py`

Debe reemplazarse por la versión modificada incluida en este repositorio dentro de src/recon.py.

### Cambios realizados en recon.py:

1. Guardar la nube como `.ply` usando Open3D:
```
o3d.io.write_point_cloud(args.output, pcd)
```
2. Deshabilitar visualización interactiva.  
3. Ajustes para mantener resolución estable compatible con `resize.py`.  
4. Evitar cálculos costosos de normales.  
5. Exponer parámetros esenciales como flags CLI.

---

## ▶️ Ejecución del pipeline completo

```
python main.py --video ruta/del/video.mp4
```

Salida esperada:

```
outputs/
 ├── raw_slam3r.ply
 ├── resized.ply
 ├── detections.json
 └── colored_output.ply
```

---

## Alternativa: Uso de Gradio (`app.py`) para generar la nube

Si SLAM3R no produce buenos resultados (p. ej., demasiados puntos, ruido, mala densidad),  
se puede usar **la aplicación Gradio incluida en SLAM3R**:

```
python slam3r/app.py
```

Allí se puede ajustar:

- Resolución
- Densidad de puntos
- Submuestreo
- Parámetros para reducir carga computacional

Esto ayuda a obtener una nube más ligera o más limpia.

---

##  Diagrama del Pipeline

```
 VIDEO → SLAM3R → raw.ply → resize.py → resized.ply → SpatialLM → detections.txt
        → walls_to_surface.py → colored_output.ply → viz_total.py → visualización final
```



---

## 📊 Metricas de evaluacion de SPATIALLM

Basadas en los resultados oficiales:

## 🧱 Layout — F1 @ 0.25 IoU (2D)

| Objeto | Llama-1B | Qwen-0.5B |
|--------|----------|-----------|
| wall   | 68.9     | 68.2      |
| door   | 49.1     | 47.4      |
| window | 47.0     | 51.4      |

---

## 🛋️ Objetos — F1 @ 0.25 IoU (3D/2D)

| Objeto          | Llama-1B | Qwen-0.5B |
|-----------------|----------|-----------|
| curtain         | 34.9     | 37.0      |
| nightstand      | 62.8     | 67.0      |
| chandelier      | 53.5     | 36.8      |
| wardrobe        | 29.4     | 39.6      |
| bed             | 96.8     | 95.2      |
| sofa            | 66.9     | 69.1      |
| chair           | 20.8     | 32.3      |
| cabinet         | 15.2     | 11.2      |
| dining table    | 40.7     | 24.2      |
| plants          | 29.5     | 26.3      |
| tv cabinet      | 34.4     | 27.3      |
| coffee table    | 56.4     | 64.9      |
| side table      | 14.6     | 9.7       |
| air conditioner | 16.7     | 24.0      |
| dresser         | 46.7     | 46.7      |
| stool           | 17.6     | 30.8      |
| refrigerator    | 0.0      | 16.7      |
| painting        | 34.9     | 38.2      |
| carpet          | 40.3     | 24.1      |
| tv              | 16.0     | 18.0      |

## 📜 Licencias

Este repositorio integra código perteneciente a:

- SLAM3R
- SpatialLM 

Los derechos corresponden a sus autores originales.

---

## Comentario final

Este pipeline fue integrado y simplificado para ofrecer una experiencia completa de reconstrucción indoor 3D de extremo a extremo. 
