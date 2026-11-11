"""
Alinea la nube de SLAM3R para SpatialLM: piso horizontal, eje Z hacia arriba,
escala aproximada en metros y piso en Z = 0.

Uso suelto:
    python src/resize.py nube_slam3r.ply nube_alineada.ply --altura 2.5
"""
import argparse

import numpy as np
import open3d as o3d


def refine_floor(pts, max_tilt_deg=25.0):
    """
    PCA deja el eje vertical solo aproximado (los muebles y la forma de la sala lo sesgan
    unos grados). Se ajusta el plano del piso con RANSAC entre los puntos más bajos y se gira
    la nube para que su normal quede exactamente en +Z.
    """
    z = pts[:, 2]
    rango = z.max() - z.min()
    bajos = pts[z < z.min() + 0.2 * rango]
    if len(bajos) < 100:
        return pts

    try:
        o3d.utility.random.seed(0)  # resultado reproducible
    except AttributeError:
        pass
    nube = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(bajos))
    (a, b, c, _), inliers = nube.segment_plane(distance_threshold=0.01 * rango, ransac_n=3, num_iterations=2000)
    n = np.array([a, b, c]) / np.linalg.norm([a, b, c])
    if n[2] < 0:
        n = -n
    inclinacion = np.degrees(np.arccos(np.clip(n[2], -1, 1)))
    if inclinacion > max_tilt_deg or len(inliers) < 0.2 * len(bajos):
        print(f" Aviso: no se encontró un piso confiable (inclinación {inclinacion:.1f}°); se deja la alineación PCA.")
        return pts

    # Rotación de Rodrigues que lleva n a +Z.
    eje = np.cross(n, [0.0, 0.0, 1.0])
    s = np.linalg.norm(eje)
    if s < 1e-9:
        return pts
    eje /= s
    K = np.array([[0, -eje[2], eje[1]], [eje[2], 0, -eje[0]], [-eje[1], eje[0], 0]])
    Rp = np.eye(3) + s * K + (1 - n[2]) * (K @ K)
    print(f" Piso corregido: {inclinacion:.1f}° de inclinación tras PCA")
    return pts @ Rp.T


def align_pointcloud(input_path, output_path, room_height=2.5, flip=False):
    """Lee una nube, la alinea con PCA, la escala y la guarda. Devuelve la ruta de salida."""
    pcd = o3d.io.read_point_cloud(input_path)
    if pcd.is_empty():
        raise RuntimeError(f"No se pudo leer la nube de puntos o está vacía: {input_path}")

    pts = np.asarray(pcd.points)
    colors = np.asarray(pcd.colors) if pcd.has_colors() else None
    print(f" Puntos de entrada: {len(pts):,}")

    # 1. PCA: los dos ejes de mayor varianza quedan en el plano del piso y el de menor
    #    varianza (la altura de la sala) pasa a ser Z.
    centered = pts - pts.mean(axis=0)
    eigenvalues, eigenvectors = np.linalg.eigh(centered.T @ centered)
    R = eigenvectors[:, np.argsort(eigenvalues)[::-1]]

    # Z hacia arriba: SLAM3R usa la convención de cámara (Y hacia abajo), así que se
    # orienta la normal del piso según el eje vertical original.
    if R[:, 2] @ np.array([0.0, -1.0, 0.0]) < 0:
        R[:, 2] *= -1
    if flip:  # cámara sostenida al revés: la sala quedaría de cabeza
        R[:, 2] *= -1
    # Que sea una rotación y no un reflejo: con det = -1 la sala saldría en espejo.
    if np.linalg.det(R) < 0:
        R[:, 0] *= -1

    aligned = centered @ R
    aligned = refine_floor(aligned)

    # 2. Escala: SLAM3R no entrega metros; se lleva la altura de la nube a la de la sala.
    current_height = aligned[:, 2].max() - aligned[:, 2].min()
    if current_height <= 0:
        raise RuntimeError("La nube no tiene altura; revisa la reconstrucción de SLAM3R.")
    scale = room_height / current_height
    aligned *= scale

    # 3. Piso en Z = 0.
    aligned[:, 2] -= aligned[:, 2].min()

    out = o3d.geometry.PointCloud()
    out.points = o3d.utility.Vector3dVector(aligned)
    if colors is not None:
        out.colors = o3d.utility.Vector3dVector(colors)
    if not o3d.io.write_point_cloud(output_path, out):
        raise RuntimeError(f"No se pudo guardar la nube alineada en {output_path}")

    print(f" Escala aplicada: {scale:.4f} | altura final: {aligned[:, 2].max():.2f} m")
    return output_path


def main():
    ap = argparse.ArgumentParser(description="Alineación PCA + escala + piso en Z=0")
    ap.add_argument("entrada", help="Nube de SLAM3R (.ply / .pcd)")
    ap.add_argument("salida", help="Nube alineada (.ply)")
    ap.add_argument("--altura", type=float, default=2.5, help="Altura de la sala en metros (por defecto 2.5)")
    ap.add_argument("--invertir", action="store_true", help="Voltea el eje vertical si la sala queda de cabeza")
    args = ap.parse_args()
    align_pointcloud(args.entrada, args.salida, args.altura, args.invertir)


if __name__ == "__main__":
    main()
