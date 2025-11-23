import argparse
import os
import numpy as np
import open3d as o3d
import rerun as rr
import rerun.blueprint as rrb

from spatiallm import Layout

# utils de SpatialLM para nubes (si no están, caemos a Open3D)
try:
    from spatiallm.pcd import load_o3d_pcd, get_points_and_colors
except Exception:
    def load_o3d_pcd(path: str):
        pcd = o3d.io.read_point_cloud(path)
        if pcd is None or pcd.is_empty():
            raise RuntimeError(f"No pude leer point cloud: {path}")
        return pcd

    def get_points_and_colors(pcd: o3d.geometry.PointCloud):
        pts = np.asarray(pcd.points, dtype=np.float32)
        if pcd.has_colors():
            cols = np.asarray(pcd.colors, dtype=np.float32)
        else:
            cols = np.ones_like(pts, dtype=np.float32) * 0.6
        return pts, cols


def parse_class_filter(s: str | None):
    if not s or s.strip().lower() == "all":
        return None
    parts = [p.strip().lower() for p in s.split(",") if p.strip()]
    return set(parts) if parts else None


def load_mesh(path: str):
    m = o3d.io.read_triangle_mesh(path)
    if m is None or m.is_empty():
        raise RuntimeError(f"No pude leer malla: {path}")
    m.compute_vertex_normals()
    return m


def main():
    parser = argparse.ArgumentParser("Visualiza: nube + layout (cajas) + superficie")
    parser.add_argument("-p", "--point_cloud", required=True, help="Ruta a la nube (pcd/ply/las...)")
    parser.add_argument("-l", "--layout", required=True, help="Ruta al layout .txt (RGB1_spatiallm.txt)")

    # Puntos
    parser.add_argument("--radius", type=float, default=0.01, help="Radio de los puntos")
    parser.add_argument("--max_points", type=int, default=1_000_000, help="Máx de puntos a mostrar")

    # Superficie
    parser.add_argument("--surface", type=str, default=None, help="Ruta a la malla de superficie (obj/ply/glb)")
    parser.add_argument("--surface_color", type=float, nargs=3, default=[0.65, 0.65, 0.65], help="RGB superficie (0..1)")
    parser.add_argument("--surface_alpha", type=int, default=255, help="Alpha superficie (0..255; fuera de rango se clampa)")
    parser.add_argument("--surface_scale", type=float, nargs=3, default=[1.0, 1.0, 1.0], help="Escala XYZ para la superficie")
    parser.add_argument("--surface_translate", type=float, nargs=3, default=[0.0, 0.0, 0.0], help="Traslación XYZ para la superficie")

    # Filtro de clases del layout
    parser.add_argument("--classes", type=str, default="all", help='Clases a mostrar: "all" o CSV (ej. "wall,door,window,bbox")')

    # Rerun
    parser.add_argument("--animate", action="store_true", help="Animar la aparición de cajas")
    parser.add_argument("--spawn", action="store_true", help="Abrir viewer de Rerun al iniciar")
    rr.script_add_args(parser)  # flags extra de Rerun
    args = parser.parse_args()

    # --- Layout ---
    with open(args.layout, "r", encoding="utf-8") as f:
        layout_txt = f.read()
    layout = Layout(layout_txt)
    boxes = layout.to_boxes()  # id, class, label, center, scale, rotation (3x3)

    # Filtro por clases
    want = parse_class_filter(args.classes)
    if want is not None:
        boxes = [b for b in boxes
                 if str(b.get("class", "")).lower() in want
                 or str(b.get("label", "")).lower() in want]

    # --- Nube de puntos ---
    pcd = load_o3d_pcd(args.point_cloud)
    points, colors = get_points_and_colors(pcd)
    if points.shape[0] > args.max_points:
        idx = np.random.permutation(points.shape[0])[: args.max_points]
        points = points[idx]
        colors = colors[idx]

    # --- Rerun setup ---
    blueprint = rrb.Blueprint(
        rrb.Spatial3DView(name="3D", origin="/world", background=[255, 255, 255]),
        collapse_panels=True,
    )
    rr.script_setup(args, "viz_total", default_blueprint=blueprint)
    if args.spawn:
        rr.spawn()
    rr.log("world", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)

    # --- Log nube ---
    rr.log(
        "world/points",
        rr.Points3D(
            positions=points.astype(np.float32),
            colors=colors.astype(np.float32),
            radii=float(args.radius),
        ),
        static=True,
    )

    # --- Superficie (opcional) ---
    if args.surface:
        surf = load_mesh(args.surface)

        # Transform opcional (escala/traslación)
        sx, sy, sz = args.surface_scale
        if not np.allclose([sx, sy, sz], [1.0, 1.0, 1.0]):
            surf.scale(sx, center=(0, 0, 0))  # Open3D usa un factor único; aplicamos sx y asumimos uniforme
            # Para no deformar, si sx!=sy!=sz, reescalar por matriz:
            if not np.isclose(sx, sy) or not np.isclose(sx, sz):
                verts = np.asarray(surf.vertices)
                S = np.diag([sx, sy, sz]).astype(np.float64)
                verts = (verts @ S.T)
                surf.vertices = o3d.utility.Vector3dVector(verts)
        tx, ty, tz = args.surface_translate
        if not np.allclose([tx, ty, tz], [0.0, 0.0, 0.0]):
            surf.translate((tx, ty, tz))

        v = np.asarray(surf.vertices, dtype=np.float32)
        f = np.asarray(surf.triangles, dtype=np.uint32)

        # Diagnóstico
        if v.size == 0 or f.size == 0:
            print(f"[surface] ¡Ojo! malla sin vértices o sin caras: {args.surface}")
        else:
            vmin, vmax = v.min(axis=0), v.max(axis=0)
            print(f"[surface] verts={len(v)} tris={len(f)} "
                  f"bbox_min={vmin.tolist()} bbox_max={vmax.tolist()}")
            pmin, pmax = points.min(axis=0), points.max(axis=0)
            print(f"[points ] bbox_min={pmin.tolist()} bbox_max={pmax.tolist()}")
            center_dist = np.linalg.norm(((vmin+vmax)*0.5) - ((pmin+pmax)*0.5))
            if center_dist > 50.0:
                print(f"[warn] Superficie y nube parecen lejos: ~{center_dist:.2f} m")

        rgb = np.clip(np.asarray(args.surface_color, dtype=np.float32), 0.0, 1.0)
        a = int(np.clip(args.surface_alpha, 0, 255))  # clamp

        rr.log(
            "world/surface",
            rr.Mesh3D(
                vertex_positions=v,
                triangle_indices=f,
                albedo_factor=[float(rgb[0]), float(rgb[1]), float(rgb[2]), a],
            ),
        )
        rr.log("world/surface", rr.TextLog(os.path.basename(args.surface)))

    # --- Cajas del layout (no sólidas) ---
    seconds = 0.5
    if args.animate:
        n = len(boxes)
        for ti in range(n + 1):
            rr.set_time_seconds("time_sec", ti * seconds)
            for b in boxes[:ti]:
                rr.log(
                    f"world/pred/{b.get('class','box')}/{b.get('id','box')}",
                    rr.Boxes3D(
                        centers=np.asarray(b["center"], dtype=np.float32),
                        half_sizes=0.5 * np.asarray(b["scale"], dtype=np.float32),
                        labels=str(b.get("label", b.get("id","box"))),
                    ),
                    rr.InstancePoses3D(mat3x3=np.asarray(b["rotation"], dtype=np.float32).reshape(3,3)),
                    static=False,
                )
    else:
        rr.set_time_seconds("time_sec", 0.0)
        for b in boxes:
            rr.log(
                f"world/pred/{b.get('class','box')}/{b.get('id','box')}",
                rr.Boxes3D(
                    centers=np.asarray(b["center"], dtype=np.float32),
                    half_sizes=0.5 * np.asarray(b["scale"], dtype=np.float32),
                    labels=str(b.get("label", b.get("id","box"))),
                ),
                rr.InstancePoses3D(mat3x3=np.asarray(b["rotation"], dtype=np.float32).reshape(3,3)),
                static=True,
            )

    rr.script_teardown(args)


if __name__ == "__main__":
    main()
