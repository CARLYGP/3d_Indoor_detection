import os
import argparse
import subprocess
import sys

# =======================================================
# IMPORTS LOCALES (tu carpeta src/)
# =======================================================
from src.resize import resize_pointcloud
from src.walls_to_surface import color_surfaces
from src.viz_total import visualize_all

# =======================================================
# FUNCIONES AUXILIARES
# =======================================================

def check_exists(path, description):
    """Valida que una ruta exista."""
    if not os.path.exists(path):
        print(f"\n ERROR: No se encontró {description}: {path}\n")
        sys.exit(1)


# =======================================================
# PASO 1 — EJECUTAR SLAM3R
# =======================================================

def run_slam3r(input_video, output_ply):
    """
    Ejecuta la reconstrucción de MASt3R-SLAM (slam3r modificado).
    Asume que slam3r/ contiene el proyecto clonado dentro del repo.
    """
    slam3r_script = "slam3r/recon.py"

    check_exists(slam3r_script, "slam3r/recon.py")

    print("\n Ejecutando SLAM3R (MASt3R-SLAM)...\n")

    cmd = [
        "python",
        slam3r_script,
        "--input", input_video,
        "--output", output_ply,
        "--format", "ply"
    ]

    subprocess.run(cmd, check=True)

    print("\n SLAM3R terminó correctamente.")
    print(f" Nube guardada en: {output_ply}")


# =======================================================
# PASO 2 — RESIZE.PY
# =======================================================

def run_resize(input_ply, output_ply):
    print("\n Ajustando nube de puntos (resize.py)...\n")
    resize_pointcloud(input_ply, output_ply)
    print(f" Resize completado → {output_ply}")


# =======================================================
# PASO 3 — SPATIALLM PREDICT
# =======================================================

def run_spatiallm(input_ply, output_json):
    """
    Llama SpatialLM para detecciones 3D.
    Asume que spatiallm/ está clonado dentro del repo.
    """
    spatiallm_script = "spatiallm/run_inference.py"
    check_exists(spatiallm_script, "SpatialLM run_inference.py")

    print("\n Ejecutando SpatialLM para detección 3D...\n")

    cmd = [
        "python",
        spatiallm_script,
        "--input", input_ply,
        "--output", output_json,
        "--task", "layout"
    ]

    subprocess.run(cmd, check=True)

    print(" SpatialLM terminó correctamente.")
    print(f" Detecciones guardadas en: {output_json}")


# =======================================================
# PASO 4 — WALLS TO SURFACE (COLOREA SUPERFICIES)
# =======================================================

def run_paint_surfaces(ply_input, json_det, ply_output):
    print("\n Coloreando paredes detectadas (walls_to_surface.py)...\n")
    color_surfaces(ply_input, json_det, ply_output)
    print(f" Paredes pintadas → {ply_output}")


# =======================================================
# PASO 5 — VISUALIZACIÓN
# =======================================================

def run_visualizer(colored_ply, detections_json):
    print("\n Visualizando nube + detecciones (viz_total.py)...\n")
    visualize_all(colored_ply, detections_json)
    print("\n Visualización completada.\n")


# =======================================================
# MAIN PIPELINE
# =======================================================

def main():
    parser = argparse.ArgumentParser(description="Pipeline completo SLAM3R → SpatialLM → Viz")

    parser.add_argument("--video", required=True, help="Video de entrada para SLAM3R")
    parser.add_argument("--tmp_dir", default="outputs", help="Carpeta de salida")

    args = parser.parse_args()

    # Crear carpeta outputs
    os.makedirs(args.tmp_dir, exist_ok=True)

    # Rutas internas
    slam3r_raw = os.path.join(args.tmp_dir, "raw_slam3r.ply")
    resized_ply = os.path.join(args.tmp_dir, "resized.ply")
    detections_json = os.path.join(args.tmp_dir, "detections.json")
    painted_ply = os.path.join(args.tmp_dir, "colored_output.ply")

    # ---------- PIPELINE ----------
    run_slam3r(args.video, slam3r_raw)
    run_resize(slam3r_raw, resized_ply)
    run_spatiallm(resized_ply, detections_json)
    run_paint_surfaces(resized_ply, detections_json, painted_ply)
    run_visualizer(painted_ply, detections_json)

    print("\n PIPELINE FINALIZADO EXITOSAMENTE 🎉")
    print(f" Nube final: {painted_ply}")
    print(f" Detecciones: {detections_json}\n")


if __name__ == "__main__":
    main()
