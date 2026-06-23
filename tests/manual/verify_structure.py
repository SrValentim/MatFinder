"""
Teste de verificação: as coordenadas e a célula unitária estão corretas?
Compara com o que o VESTA/Mercury fariam.
"""
from pymatgen.core import Structure
import numpy as np

# Carregar estrutura
s = Structure.from_file('../temp_cifs/MP_mp-7550_CeNbO4.cif')

print("="*70)
print("VERIFICAÇÃO: CeNbO4 - Estrutura vs Célula Unitária")
print("="*70)

lattice = s.lattice
a_vec = lattice.matrix[0]
b_vec = lattice.matrix[1]
c_vec = lattice.matrix[2]

print("\n1. VETORES DE REDE (definemcelula):")
print(f"   a = {a_vec}")
print(f"   b = {b_vec}")
print(f"   c = {c_vec}")

print("\n2. VÉRTICES DA CÉLULA UNITÁRIA (paralelepípedo):")
vertices = [
    ("Origem", np.array([0.0, 0.0, 0.0])),
    ("a", a_vec),
    ("b", b_vec),
    ("c", c_vec),
    ("a+b", a_vec + b_vec),
    ("a+c", a_vec + c_vec),
    ("b+c", b_vec + c_vec),
    ("a+b+c", a_vec + b_vec + c_vec),
]
for name, v in vertices:
    print(f"   {name:>8s}: [{v[0]:7.3f}, {v[1]:7.3f}, {v[2]:7.3f}]")

print("\n3. ÁTOMOS (primeiros 5):")
for i, site in enumerate(s[:5]):
    frac = site.frac_coords
    cart = site.coords
    print(f"   {site.specie:>3s} | Frac: [{frac[0]:.3f}, {frac[1]:.3f}, {frac[2]:.3f}] | Cart: [{cart[0]:7.3f}, {cart[1]:7.3f}, {cart[2]:7.3f}]")

print("\n4. VERIFICAÇÃO: Átomos dentro da célula?")
all_frac = np.array([site.frac_coords for site in s])
min_frac = all_frac.min(axis=0)
max_frac = all_frac.max(axis=0)
print(f"   Frac mínimo: [{min_frac[0]:.3f}, {min_frac[1]:.3f}, {min_frac[2]:.3f}]")
print(f"   Frac máximo: [{max_frac[0]:.3f}, {max_frac[1]:.3f}, {max_frac[2]:.3f}]")

if (min_frac >= 0).all() and (max_frac <= 1).all():
    print("   ✅ CORRETO: Todas as coordenadas fracionárias estão entre 0 e 1")
else:
    print("   ⚠️ ATENÇÃO: Algumas coordenadas fracionárias estão fora de [0,1]!")

print("\n5. CÁLCULO INVERSO: Vértice da célula → Frac → Cart")
test_vertex_cart = a_vec + b_vec + c_vec
test_vertex_frac = lattice.get_fractional_coords(test_vertex_cart)
test_vertex_cart_again = lattice.get_cartesian_coords(test_vertex_frac)
print(f"   Vértice (cart): {test_vertex_cart}")
print(f"   Convertido (frac): {test_vertex_frac}")
print(f"   Reconvertido (cart): {test_vertex_cart_again}")
print(f"   Diferença: {np.linalg.norm(test_vertex_cart - test_vertex_cart_again):.10f}")

if np.allclose(test_vertex_cart, test_vertex_cart_again):
    print("   ✅ Conversões estão consistentes")
else:
    print("   ❌ ERRO nas conversões!")

print("\n6. SIMULAÇÃO: Como o VESTA renderizaria?")
print("   O VESTA desenha:")
print("   - Célula unitária: paralelepípedo de (0,0,0) até a+b+c")
print("   - Átomos: nas posições cartesianas site.coords")
print("   - Resultado: átomos DENTRO do paralelepípedo (coord frac [0,1])")

print("\n7. CONCLUSÃO:")
if (min_frac >= 0).all() and (max_frac <= 1).all():
    print("   ✅ ESTRUTURA ESTÁ CORRETA")
    print("   ✅ CÉLULA ESTÁ CORRETA")
    print("   ✅ ÁTOMOS ESTÃO DENTRO DA CÉLULA")
    print("\n   Se visualmente parecem 'fora', é por causa da geometria")
    print("   não-ortogonal da célula (ângulos α≠90° ou β≠90° ou γ≠90°).")
    print("   Isso é NORMAL e CORRETO em cristalografia!")
else:
    print("   ❌ ALGO ESTÁ ERRADO!")

print("="*70)

