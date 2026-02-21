from pymatgen.core import Structure
import numpy as np

# Carregar estrutura
s = Structure.from_file('temp_cifs/MP_mp-7550_CeNbO4.cif')

print("="*60)
print("INFORMAÇÕES DA ESTRUTURA CeNbO4")
print("="*60)

# Parâmetros de rede
lat = s.lattice
print(f"\nParâmetros de rede:")
print(f"  a = {lat.a:.4f} Å")
print(f"  b = {lat.b:.4f} Å")
print(f"  c = {lat.c:.4f} Å")
print(f"  α = {lat.alpha:.2f}°")
print(f"  β = {lat.beta:.2f}°")
print(f"  γ = {lat.gamma:.2f}°")

# Vetores de rede
print(f"\nVetores de rede (cartesianos):")
print(f"  a_vec = {lat.matrix[0]}")
print(f"  b_vec = {lat.matrix[1]}")
print(f"  c_vec = {lat.matrix[2]}")

# Átomos
print(f"\nTotal de átomos: {len(s)}")
print(f"\nPrimeiros 5 átomos:")
for i, site in enumerate(s[:5]):
    print(f"  {i}: {site.specie:>3s}  Cartesian: {site.coords}  Fractional: {site.frac_coords}")

# Verificar limites
all_coords = np.array([site.coords for site in s])
print(f"\nLimites das coordenadas cartesianas:")
print(f"  X: [{all_coords[:, 0].min():.3f}, {all_coords[:, 0].max():.3f}]")
print(f"  Y: [{all_coords[:, 1].min():.3f}, {all_coords[:, 1].max():.3f}]")
print(f"  Z: [{all_coords[:, 2].min():.3f}, {all_coords[:, 2].max():.3f}]")

# Verificar coordenadas fracionárias
all_frac = np.array([site.frac_coords for site in s])
print(f"\nLimites das coordenadas fracionárias:")
print(f"  a: [{all_frac[:, 0].min():.3f}, {all_frac[:, 0].max():.3f}]")
print(f"  b: [{all_frac[:, 1].min():.3f}, {all_frac[:, 1].max():.3f}]")
print(f"  c: [{all_frac[:, 2].min():.3f}, {all_frac[:, 2].max():.3f}]")

# Verificar se célula unitária deveria começar em (0,0,0)
print(f"\nVértices da célula unitária (coordenadas fracionárias → cartesianas):")
vertices_frac = [[0,0,0], [1,0,0], [0,1,0], [0,0,1]]
for vf in vertices_frac:
    vc = lat.get_cartesian_coords(vf)
    print(f"  {vf} → {vc}")

print("="*60)

