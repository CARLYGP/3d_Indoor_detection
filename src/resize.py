import numpy as np
import open3d as o3d

# ===========================================================
# 1. Load point cloud
# ===========================================================
pcd_path = "recon.pcd"   # <-- cambia tu archivo SLAM3R
pcd = o3d.io.read_point_cloud(pcd_path)

pts = np.asarray(pcd.points)
colors = np.asarray(pcd.colors)

print("Original shape:", pts.shape)


# ===========================================================
# 2. PCA ALIGNMENT (Z-UP)
# ===========================================================

# Center to remove translation bias
pts_centered = pts - pts.mean(axis=0)

# PCA on covariance
H = pts_centered.T @ pts_centered
eigenvalues, eigenvectors = np.linalg.eigh(H)

# Order eigenvectors by variance (descending)
order = np.argsort(eigenvalues)[::-1]
R = eigenvectors[:, order]

# Force z-axis to be vertical (smallest variance direction)
z_axis = order[-1]
z_vec = eigenvectors[:, z_axis]

# If Z points downward, flip it
if z_vec[2] < 0:
    R[:, -1] *= -1

# Apply rotation
aligned_pts = pts_centered @ R

print("Aligned minZ/maxZ:", aligned_pts[:, 2].min(), aligned_pts[:, 2].max())


# ===========================================================
# 3. SCALE to target room height (default 2.5m)
# ===========================================================
min_z = aligned_pts[:, 2].min()
max_z = aligned_pts[:, 2].max()
current_height = max_z - min_z

estimated_height = 2.5  # meters – modify if your room height differs
scale = estimated_height / current_height

print("Scaling factor:", scale)

aligned_pts *= scale


# ===========================================================
# 4. FLOOR FIX — ensure real floor = Z = 0
# ===========================================================
min_z_after_scale = aligned_pts[:, 2].min()

# Shift cloud so floor touches Z=0
aligned_pts[:, 2] -= min_z_after_scale

print("Final minZ/maxZ:", aligned_pts[:, 2].min(), aligned_pts[:, 2].max())


# ===========================================================
# 5. Save final aligned + scaled + floor-corrected cloud
# ===========================================================
aligned_pcd = o3d.geometry.PointCloud()
aligned_pcd.points = o3d.utility.Vector3dVector(aligned_pts)
aligned_pcd.colors = o3d.utility.Vector3dVector(colors)

output_path = "aligned_scaled_floor.ply"
o3d.io.write_point_cloud(output_path, aligned_pcd)

print("Saved:", output_path)
print("✓ Alignment complete")
