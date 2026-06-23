"""
Análise detalhada do Carbono hexagonal (grafite) - COD_1000065
Investigação de ligações fantasmas
"""
from pymatgen.core import Structure
import numpy as np

# Carregar estrutura
s = Structure.from_file('C:/Users/Raynner/Downloads/COD_1000065_C.cif')

print("="*70)
print("ANÁLISE: GRAFITE (Carbono Hexagonal) - COD_1000065")
print("="*70)

# Informações básicas
print(f"\n📊 INFORMAÇÕES BÁSICAS:")
print(f"  Fórmula: {s.composition}")
print(f"  Átomos na célula unitária: {len(s)}")
print(f"  Sistema cristalino: {s.lattice.lattice_type}")

# Parâmetros de rede
lat = s.lattice
print(f"\n📐 PARÂMETROS DE REDE:")
print(f"  a = {lat.a:.4f} Å")
print(f"  b = {lat.b:.4f} Å")
print(f"  c = {lat.c:.4f} Å (distância entre camadas)")
print(f"  α = {lat.alpha:.2f}°")
print(f"  β = {lat.beta:.2f}°")
print(f"  γ = {lat.gamma:.2f}° (HEXAGONAL!)")

# Posições dos átomos
print(f"\n🔍 POSIÇÕES DOS ÁTOMOS (cartesianas):")
for i, site in enumerate(s):
    print(f"  C{i}: [{site.coords[0]:7.4f}, {site.coords[1]:7.4f}, {site.coords[2]:7.4f}] Å")

# Posições fracionárias
print(f"\n🔍 POSIÇÕES DOS ÁTOMOS (fracionárias):")
for i, site in enumerate(s):
    frac = site.frac_coords
    print(f"  C{i}: [{frac[0]:7.4f}, {frac[1]:7.4f}, {frac[2]:7.4f}]")

# Análise de distâncias DENTRO da célula unitária
print(f"\n📏 DISTÂNCIAS ENTRE ÁTOMOS (célula unitária):")
dists = []
for i in range(len(s)):
    for j in range(i+1, len(s)):
        d = np.linalg.norm(s[i].coords - s[j].coords)
        dists.append((i, j, d))
        tipo = "INTRA-CAMADA" if d < 2.0 else "INTER-CAMADAS"
        print(f"  C{i}-C{j}: {d:.4f} Å  [{tipo}]")

dists_sorted = sorted(dists, key=lambda x: x[2])

print(f"\n📊 ESTATÍSTICAS:")
print(f"  Menor distância: {dists_sorted[0][2]:.4f} Å (C{dists_sorted[0][0]}-C{dists_sorted[0][1]})")
print(f"  Maior distância: {dists_sorted[-1][2]:.4f} Å (C{dists_sorted[-1][0]}-C{dists_sorted[-1][1]})")

# Distâncias teóricas do grafite
print(f"\n📚 VALORES TEÓRICOS (GRAFITE):")
print(f"  Ligação C-C (intra-camada): ~1.42 Å ✅ DEVE EXISTIR")
print(f"  Distância entre camadas: ~3.35 Å ❌ NÃO DEVE TER LIGAÇÃO")

# Análise com vizinhos (incluindo células adjacentes)
print(f"\n🔬 ANÁLISE DE VIZINHOS (incluindo células adjacentes):")
max_dist = 4.0  # Analisar até 4 Å
for i, site in enumerate(s):
    neighbors = s.get_neighbors(site, max_dist)
    print(f"\n  C{i} ({site.frac_coords}):")
    
    intra_layer = []
    inter_layer = []
    
    for neighbor, dist in neighbors:
        if dist < 2.0:  # Ligações covalentes na mesma camada
            intra_layer.append((neighbor.specie.symbol, dist))
        else:  # Entre camadas
            inter_layer.append((neighbor.specie.symbol, dist))
    
    print(f"    Vizinhos na mesma camada (< 2.0 Å): {len(intra_layer)}")
    for elem, d in sorted(intra_layer, key=lambda x: x[1])[:5]:
        print(f"      {elem}: {d:.4f} Å ✅ CORRETO")
    
    print(f"    Vizinhos entre camadas (> 2.0 Å): {len(inter_layer)}")
    for elem, d in sorted(inter_layer, key=lambda x: x[1])[:3]:
        print(f"      {elem}: {d:.4f} Å ❌ NÃO DEVERIA TER LIGAÇÃO!")

# VERIFICAÇÃO CRÍTICA
print(f"\n" + "="*70)
print("🚨 VERIFICAÇÃO CRÍTICA: LIGAÇÕES FANTASMAS")
print("="*70)

# Raio covalente do Carbono sp2 (grafite): ~0.71 Å
# Ligação C-C no grafite: 2 × 0.71 = 1.42 Å
# Margem de segurança: 1.42 × 1.2 = 1.70 Å

MAX_BOND_DIST_GRAPHITE = 1.70  # Å

print(f"\n✅ Distância máxima para ligação C-C (grafite): {MAX_BOND_DIST_GRAPHITE} Å")
print(f"   (Raio covalente × 2 × margem de segurança)")

# Verificar quantas ligações seriam criadas COM O ALGORITMO ATUAL
print(f"\n🔴 PROBLEMA: Algoritmo atual usa max_bond_dist = 3.5 Å (MUITO ALTO!)")
print(f"   Isso cria ligações ENTRE CAMADAS (3.35 Å) que NÃO EXISTEM!")

# Simular algoritmo atual
wrong_bonds = []
correct_bonds = []
current_max = 3.5  # O que está no código atual

for i in range(len(s)):
    neighbors = s.get_neighbors(s[i], current_max)
    for neighbor, dist in neighbors:
        j = s.index(neighbor)
        if j > i:  # Evitar duplicatas
            if dist > MAX_BOND_DIST_GRAPHITE:
                wrong_bonds.append((i, j, dist))
            else:
                correct_bonds.append((i, j, dist))

print(f"\n📊 RESULTADOS COM ALGORITMO ATUAL (max_dist = 3.5 Å):")
print(f"  ✅ Ligações corretas (< {MAX_BOND_DIST_GRAPHITE} Å): {len(correct_bonds)}")
print(f"  ❌ Ligações FANTASMAS (> {MAX_BOND_DIST_GRAPHITE} Å): {len(wrong_bonds)}")

if wrong_bonds:
    print(f"\n❌ LIGAÇÕES FANTASMAS DETECTADAS:")
    for i, j, d in wrong_bonds:
        print(f"  C{i}-C{j}: {d:.4f} Å  [ENTRE CAMADAS - ERRO!]")

print(f"\n" + "="*70)
print("💡 SOLUÇÃO RECOMENDADA:")
print("="*70)
print(f"""
1. PROBLEMA IDENTIFICADO:
   - max_bond_distance = 3.5 Å é GENÉRICO demais
   - Funciona para óxidos, mas NÃO para grafite/grafeno
   
2. SOLUÇÃO:
   - Usar distâncias ESPECÍFICAS por elemento e hibridização
   - Carbono sp2 (grafite): max = 1.7 Å
   - Carbono sp3 (diamante): max = 1.6 Å
   - Carbono-Oxigênio: max = 1.8 Å
   - Metal-Oxigênio: max = 2.5-3.5 Å
   
3. IMPLEMENTAÇÃO:
   - Criar dicionário de distâncias máximas por PAR de elementos
   - Considerar tipo de ligação (simples, dupla, metálica)
   - Usar raios covalentes da literatura
""")

print("="*70)

