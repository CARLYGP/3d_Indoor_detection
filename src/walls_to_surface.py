# walls_to_surface.py
import argparse, os, re
import numpy as np
import open3d as o3d

# spatiallm y rerun solo hacen falta en el modo 'boxes' y con --view; se importan ahí.

EPS = 1e-4

# ---------------------------- parsing ----------------------------
WALL_RE = re.compile(
    r"^\s*\w+\s*=\s*Wall\(\s*([-\d\.eE]+),([-\d\.eE]+),([-\d\.eE]+)\s*,\s*([-\d\.eE]+),([-\d\.eE]+),([-\d\.eE]+)\s*,\s*([-\d\.eE]+)\s*,\s*([-\d\.eE]+)\s*\)"
)

def file_has_wall_lines(txt: str) -> bool:
    for ln in txt.splitlines():
        if WALL_RE.match(ln):
            return True
    return False

def parse_walls_from_txt(txt: str):
    walls = []
    for ln in txt.splitlines():
        m = WALL_RE.match(ln)
        if m:
            x1,y1,z1,x2,y2,z2,h,yaw = map(float, m.groups())
            walls.append({
                "p1": np.array([x1,y1,z1], float),
                "p2": np.array([x2,y2,z2], float),
                "height": float(h),
                "yaw": float(yaw),
            })
    return walls

def boxes_from_layout_txt(txt: str):
    from spatiallm import Layout
    layout = Layout(txt)
    return layout.to_boxes()

# ---------------------------- geom utils ----------------------------
def create_box_mesh(size_xyz, color=(0.65,0.65,0.65)):
    sx,sy,sz = [max(EPS, float(v)) for v in size_xyz]
    m = o3d.geometry.TriangleMesh.create_box(width=sx, height=sy, depth=sz)
    m.compute_vertex_normals()
    m.paint_uniform_color(color)
    m.translate(-np.array([sx,sy,sz])*0.5)   # centrar
    return m

def wall_mesh_from_endpoints(p1, p2, height, thickness=0.12, color=(0.65,0.65,0.65)):
    """
    Construye un panel EXACTO a partir de los extremos de la pared:
    - y_local = dirección horizontal p1->p2 (longitud)
    - z_local = up
    - x_local = z × y (normal)
    - tamaño = (espesor, longitud, altura)
    Esto elimina los pequeños desfases entre paneles.
    """
    p1 = np.asarray(p1,float); p2 = np.asarray(p2,float)
    up = np.array([0,0,1.0], float)

    # dirección horizontal y longitud
    dir_vec = p2 - p1
    dir_vec[2] = 0.0
    L = float(np.linalg.norm(dir_vec))
    if L < EPS:
        dir_vec = np.array([1.0, 0.0, 0.0]); L = EPS
    else:
        dir_vec /= L

    z_axis = up
    x_axis = np.cross(z_axis, dir_vec); n = np.linalg.norm(x_axis)
    if n < EPS:
        x_axis = np.array([1.0,0.0,0.0]); n = 1.0
    x_axis /= n
    y_axis = np.cross(x_axis, z_axis); y_axis /= (np.linalg.norm(y_axis)+1e-12)

    R = np.stack([x_axis, y_axis, z_axis], axis=1)
    size = (max(EPS, thickness), max(EPS, L), max(EPS, height))

    box = create_box_mesh(size, color=color)

    # centro del panel: mitad del segmento y a media altura
    base_z = (p1[2] + p2[2]) * 0.5
    center = (p1 + p2) * 0.5
    center[2] = base_z + size[2]*0.5

    box.rotate(R, center=(0,0,0))
    box.translate(center)
    return box

def oriented_panel_from_box(center, scale, R, thickness_m=None, color=(0.65,0.65,0.65)):
    """
    Modo 'boxes' (compatibilidad): ajusta un box delgado al aabb orientado.
    Se fuerza la altura a Z y el espesor a la dimensión mínima.
    """
    scale  = np.asarray(scale, float).reshape(3)
    center = np.asarray(center, float).reshape(3)
    R_in   = np.asarray(R, float).reshape(3,3)

    # hallar cuál axis local es altura (más alineado a Z)
    cols = [R_in[:,0], R_in[:,1], R_in[:,2]]
    dots = [abs(float(np.dot(c/ (np.linalg.norm(c)+1e-12), np.array([0,0,1.])))) for c in cols]
    h_axis = int(np.argmax(dots))
    # ordenar dims por indices locales relativos a R_in
    dims = list(range(3))
    dims.remove(h_axis)
    # mid y thick según escala
    rem = np.array([scale[dims[0]], scale[dims[1]]])
    if rem[0] < rem[1]:
        t_idx, m_idx = dims[0], dims[1]
    else:
        t_idx, m_idx = dims[1], dims[0]

    thickness = float(thickness_m) if thickness_m is not None else max(EPS, float(scale[t_idx]))
    length    = float(scale[m_idx])
    height    = float(scale[h_axis])

    # Construir en local (x=espesor, y=longitud, z=altura) y permutar ejes a R_in
    box = create_box_mesh((thickness, length, height), color=color)

    P = np.zeros((3,3))
    eye = np.eye(3)
    P[:,0] = eye[:, t_idx]
    P[:,1] = eye[:, m_idx]
    P[:,2] = eye[:, h_axis]

    R_final = R_in @ P
    box.rotate(R_final, center=(0,0,0))
    box.translate(center)
    return box

def merge_meshes(meshes):
    out = o3d.geometry.TriangleMesh()
    for m in meshes: out += m
    out.remove_duplicated_vertices()
    out.remove_duplicated_triangles()
    out.remove_degenerate_triangles()
    out.remove_non_manifold_edges()
    out.merge_close_vertices(1e-4)
    out.compute_vertex_normals()
    return out

def log_mesh_rr(mesh: o3d.geometry.TriangleMesh, path: str, label="mesh"):
    import rerun as rr
    verts = np.asarray(mesh.vertices, dtype=np.float32)
    tris  = np.asarray(mesh.triangles, dtype=np.uint32)
    rr.log(path, rr.Mesh3D(vertex_positions=verts, triangle_indices=tris))
    rr.log(path, rr.TextLog(label))

# ---------------------------- main ----------------------------
def main():
    ap = argparse.ArgumentParser("Walls -> Solid Surface (genera paneles SIN huecos)")
    ap.add_argument("--layout_txt", required=True, help="RGB1_spatiallm.txt")
    ap.add_argument("--mesh_out", default="walls_solid.obj", help="OBJ/PLY/GLB de salida")
    ap.add_argument("--thickness", type=float, default=0.12, help="Espesor fijo (m)")
    ap.add_argument("--convex_hull", action="store_true", help="Además, genera hull de esquinas")
    ap.add_argument("--source", choices=["auto","walls","boxes"], default="auto",
                    help="De dónde construir paredes: 'walls' (líneas Wall), 'boxes' (to_boxes), o 'auto'")
    ap.add_argument("--view", action="store_true", help="Visualizar en Rerun")
    ap.add_argument("--open", action="store_true", help="Abrir el Viewer de Rerun")
    args = ap.parse_args()

    with open(args.layout_txt, "r", encoding="utf-8") as f:
        txt = f.read()

    # Selección de fuente
    src = args.source
    if src == "auto":
        src = "walls" if file_has_wall_lines(txt) else "boxes"
    print(f"[info] Fuente seleccionada: {src}")

    meshes = []
    corner_points = []

    if src == "walls":
        walls = parse_walls_from_txt(txt)
        if not walls:
            print("[warn] No se hallaron líneas Wall(...). Cambiando a 'boxes'.")
            src = "boxes"
        else:
            for w in walls:
                m = wall_mesh_from_endpoints(w["p1"], w["p2"], w["height"], thickness=args.thickness)
                meshes.append(m)
                # esquinas del paralelepípedo original (para hull)
                # usamos el panel final para robustez
                pts = np.asarray(m.vertices)
                corner_points.append(pts[np.random.choice(len(pts), size=min(50, len(pts)), replace=False)])

    if src == "boxes":
        boxes = boxes_from_layout_txt(txt)
        wall_boxes = [b for b in boxes if str(b.get("class","")).lower().startswith("wall")]
        if not wall_boxes:
            print("No se encontraron cajas 'wall'."); return
        for b in wall_boxes:
            c = np.asarray(b["center"], float).reshape(3)
            s = np.asarray(b["scale"],  float).reshape(3)
            R = np.asarray(b["rotation"], float).reshape(3,3)
            m = oriented_panel_from_box(c, s, R, thickness_m=args.thickness)
            meshes.append(m)
            # esquinas del aabb orientado
            half = 0.5*s
            local = np.array([
                [+half[0], +half[1], +half[2]],
                [+half[0], +half[1], -half[2]],
                [+half[0], -half[1], +half[2]],
                [+half[0], -half[1], -half[2]],
                [-half[0], +half[1], +half[2]],
                [-half[0], +half[1], -half[2]],
                [-half[0], -half[1], +half[2]],
                [-half[0], -half[1], -half[2]],
            ])
            world = (local @ R.T) + c
            corner_points.append(world)

    if not meshes:
        print("[err] No se generaron paneles."); return

    walls_mesh = merge_meshes(meshes)
    out = args.mesh_out
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    o3d.io.write_triangle_mesh(out, walls_mesh)
    print(f"[OK] Malla de paredes guardada en: {out}")

    if args.convex_hull and len(corner_points) > 0:
        pts = np.vstack(corner_points).astype(np.float64)
        pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts))
        hull, _ = pcd.compute_convex_hull()
        hull.compute_vertex_normals()
        hull_path = os.path.splitext(out)[0] + "_hull.obj"
        o3d.io.write_triangle_mesh(hull_path, hull)
        print(f"[OK] Envolvente convexa guardada en: {hull_path}")

    if args.view:
        import rerun as rr
        import rerun.blueprint as rrb
        blueprint = rrb.Blueprint(
            rrb.Spatial3DView(name="3D", origin="/world", background=[255,255,255]),
            collapse_panels=True,
        )
        rr.init("walls_surface", spawn=False, default_blueprint=blueprint)
        if args.open:
            rr.spawn()
        rr.log("world", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
        log_mesh_rr(walls_mesh, "world/walls", label="walls (solid)")
        rrd = os.path.splitext(out)[0] + ".rrd"
        rr.save(rrd)
        print(f"[OK] RRD guardado: {rrd}")

if __name__ == "__main__":
    main()
