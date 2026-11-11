"""
Pipeline completo: video -> SLAM3R -> alineación PCA -> SpatialLM -> paredes 3D -> visualización.

    python main.py --video sala.mp4

SLAM3R y SpatialLM piden versiones de PyTorch distintas, así que lo normal es tenerlos en
dos entornos. Cada modelo se ejecuta como proceso aparte con el intérprete que se indique
(--slam3r_python / --spatiallm_python); por defecto, el mismo Python que corre este script.
"""
import argparse
import filecmp
import os
import shlex
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(RAIZ, "src")
sys.path.insert(0, RAIZ)


# =======================================================
# AUXILIARES
# =======================================================

def fallar(mensaje):
    print(f"\n ERROR: {mensaje}\n")
    sys.exit(1)


def check_exists(path, description):
    """Valida que una ruta exista."""
    if not os.path.exists(path):
        fallar(f"No se encontró {description}: {path}")


def ejecutar(cmd, cwd=None, env=None):
    print(" $", " ".join(shlex.quote(c) for c in cmd))
    resultado = subprocess.run(cmd, cwd=cwd, env=env)
    if resultado.returncode != 0:
        fallar(f"El paso terminó con código {resultado.returncode}.")


def entorno_con(*rutas):
    """Copia del entorno con rutas extra en PYTHONPATH (p. ej. el clon de SpatialLM)."""
    env = os.environ.copy()
    extra = [os.path.abspath(r) for r in rutas]
    if env.get("PYTHONPATH"):
        extra.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(extra)
    return env


# =======================================================
# PASO 1 — SLAM3R: video -> nube de puntos
# =======================================================

def preparar_recon(slam3r_dir):
    """SLAM3R original exige --dataset o --img_dir; src/recon.py acepta también --video_path."""
    destino = os.path.join(slam3r_dir, "recon.py")
    propio = os.path.join(SRC, "recon.py")
    check_exists(destino, "recon.py de SLAM3R (¿clonaste SLAM3R en slam3r/?)")
    if not filecmp.cmp(propio, destino, shallow=False):
        respaldo = os.path.join(slam3r_dir, "recon_original.py")
        if not os.path.exists(respaldo):
            shutil.copy2(destino, respaldo)
        shutil.copy2(propio, destino)
        print(f" Se instaló src/recon.py en {destino} (el original quedó en recon_original.py)")


def run_slam3r(video, out_dir, slam3r_dir, python, extra_args, nombre="escena"):
    print("\n[1/5] Reconstruyendo la nube de puntos con SLAM3R...\n")
    preparar_recon(slam3r_dir)

    # El lector de SLAM3R decide el tipo de entrada por la extensión (.mp4) y toma cualquier
    # ruta con ':' como URL, así que se le pasa la ruta relativa a su carpeta.
    if not video.lower().endswith(".mp4"):
        fallar("SLAM3R solo reconoce videos .mp4; convierte el video antes (p. ej. con ffmpeg).")
    try:
        video_rel = os.path.relpath(os.path.abspath(video), slam3r_dir)
    except ValueError:  # Windows: video y SLAM3R en unidades distintas
        fallar("El video debe estar en la misma unidad de disco que la carpeta de SLAM3R.")

    save_dir = os.path.join(out_dir, "slam3r")
    ejecutar(
        [python, "recon.py", "--video_path", video_rel, "--test_name", nombre, "--save_dir", save_dir] + extra_args,
        cwd=slam3r_dir,
    )

    # SLAM3R guarda la nube en <save_dir>/<test_name>/<test_name>_online_recon.ply
    ply = os.path.join(save_dir, nombre, f"{nombre}_online_recon.ply")
    check_exists(ply, "la nube que debía guardar SLAM3R")
    print(f" Nube guardada en: {ply}")
    return ply


# =======================================================
# PASO 2 — ALINEACIÓN PCA
# =======================================================

def run_resize(input_ply, output_ply, altura, invertir):
    print("\n[2/5] Alineando la nube (PCA, escala, piso en Z=0)...\n")
    from src.resize import align_pointcloud

    align_pointcloud(input_ply, output_ply, room_height=altura, flip=invertir)
    print(f" Nube alineada -> {output_ply}")


# =======================================================
# PASO 3 — SPATIALLM: nube -> paredes, puertas y objetos
# =======================================================

def run_spatiallm(input_ply, output_txt, spatiallm_dir, python, modelo):
    print("\n[3/5] Detectando la estructura y los objetos con SpatialLM...\n")
    check_exists(os.path.join(spatiallm_dir, "inference.py"), "inference.py de SpatialLM (¿clonaste SpatialLM en spatiallm/?)")

    # inference.py busca code_template.txt en su carpeta, por eso corre desde ahí.
    ejecutar(
        [python, "inference.py", "--point_cloud", input_ply, "--output", output_txt, "--model_path", modelo],
        cwd=spatiallm_dir,
        env=entorno_con(spatiallm_dir),
    )
    check_exists(output_txt, "el archivo de detecciones de SpatialLM")
    print(f" Detecciones guardadas en: {output_txt}")


# =======================================================
# PASO 4 — PAREDES COMO SUPERFICIE
# =======================================================

def run_walls(detections_txt, mesh_out, spatiallm_dir, python):
    print("\n[4/5] Convirtiendo las paredes en paneles 3D...\n")
    ejecutar(
        [python, os.path.join(SRC, "walls_to_surface.py"), "--layout_txt", detections_txt, "--mesh_out", mesh_out],
        env=entorno_con(spatiallm_dir),
    )
    check_exists(mesh_out, "la malla de paredes")


# =======================================================
# PASO 5 — VISUALIZACIÓN (Rerun)
# =======================================================

def run_visualizer(cloud_ply, detections_txt, mesh, rrd_out, spatiallm_dir, python, abrir):
    print("\n[5/5] Armando la escena final (nube + paredes + objetos)...\n")
    cmd = [python, os.path.join(SRC, "viz_total.py"), "-p", cloud_ply, "-l", detections_txt, "--surface", mesh]
    cmd += ["--spawn"] if abrir else ["--save", rrd_out]
    ejecutar(cmd, env=entorno_con(spatiallm_dir))
    if not abrir:
        print(f" Escena guardada en: {rrd_out}  (ábrela con: rerun {rrd_out})")


# =======================================================
# MAIN
# =======================================================

def main():
    ap = argparse.ArgumentParser(description="Pipeline completo SLAM3R -> PCA -> SpatialLM -> paredes -> Rerun")
    ap.add_argument("--video", help="Video .mp4 de la habitación")
    ap.add_argument("--nube", help="Saltar SLAM3R y partir de una nube .ply ya reconstruida")
    ap.add_argument("--tmp_dir", default="outputs", help="Carpeta de salida (por defecto outputs/)")

    ap.add_argument("--slam3r_dir", default=os.path.join(RAIZ, "slam3r"), help="Clon de SLAM3R")
    ap.add_argument("--spatiallm_dir", default=os.path.join(RAIZ, "spatiallm"), help="Clon de SpatialLM")
    ap.add_argument("--slam3r_python", default=sys.executable, help="Python del entorno de SLAM3R")
    ap.add_argument("--spatiallm_python", default=sys.executable, help="Python del entorno de SpatialLM")
    ap.add_argument("--slam3r_args", default="", help='Opciones extra para SLAM3R, p. ej. "--keyframe_stride 5"')
    ap.add_argument("--modelo", default="manycore-research/SpatialLM1.1-Qwen-0.5B", help="Modelo de SpatialLM (Hugging Face o ruta local)")

    ap.add_argument("--altura", type=float, default=2.5, help="Altura real de la sala en metros")
    ap.add_argument("--invertir", action="store_true", help="Voltear la nube si queda de cabeza")
    ap.add_argument("--ver", action="store_true", help="Abrir el visor de Rerun al final en vez de guardar un .rrd")
    args = ap.parse_args()

    if not args.video and not args.nube:
        ap.error("indica --video (pipeline completo) o --nube (a partir de una nube ya reconstruida)")

    out_dir = os.path.abspath(args.tmp_dir)
    os.makedirs(out_dir, exist_ok=True)
    slam3r_dir = os.path.abspath(args.slam3r_dir)
    spatiallm_dir = os.path.abspath(args.spatiallm_dir)

    aligned_ply = os.path.join(out_dir, "nube_alineada.ply")
    detections_txt = os.path.join(out_dir, "detections.txt")
    walls_mesh = os.path.join(out_dir, "paredes.ply")
    rrd = os.path.join(out_dir, "escena.rrd")

    # Validar todo antes de lanzar SLAM3R, que es el paso más largo.
    check_exists(os.path.join(spatiallm_dir, "inference.py"), "inference.py de SpatialLM (¿clonaste SpatialLM en spatiallm/?)")
    if not args.nube:
        check_exists(os.path.join(slam3r_dir, "recon.py"), "recon.py de SLAM3R (¿clonaste SLAM3R en slam3r/?)")

    # ---------- PIPELINE ----------
    if args.nube:
        check_exists(args.nube, "la nube de entrada")
        raw_ply = os.path.abspath(args.nube)
    else:
        check_exists(args.video, "el video de entrada")
        raw_ply = run_slam3r(args.video, out_dir, slam3r_dir, args.slam3r_python, shlex.split(args.slam3r_args))

    run_resize(raw_ply, aligned_ply, args.altura, args.invertir)
    run_spatiallm(aligned_ply, detections_txt, spatiallm_dir, args.spatiallm_python, args.modelo)
    run_walls(detections_txt, walls_mesh, spatiallm_dir, args.spatiallm_python)
    run_visualizer(aligned_ply, detections_txt, walls_mesh, rrd, spatiallm_dir, args.spatiallm_python, args.ver)

    print("\n PIPELINE FINALIZADO")
    print(f" Nube alineada:  {aligned_ply}")
    print(f" Detecciones:    {detections_txt}")
    print(f" Paredes:        {walls_mesh}\n")


if __name__ == "__main__":
    main()
