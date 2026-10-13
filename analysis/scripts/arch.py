import bpy, sys, json, collections, re, statistics
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
H = json.load(open(sys.argv[-2]))['rows']; st = {x['obj']:x for x in json.load(open(sys.argv[-3]))}
keys=['Bays X','Bays Y','Floors','Roof','Shopfront','Engawa','Balcony','Lanterns','Gate','Fence']
A = collections.defaultdict(list)
for r in H:
    a = r['obj'].split('_',2)[-1] if r['obj'].count('_')>=2 else r['obj'].split('_',1)[-1]
    A[a].append(r)
print("archetype | n | param signatures (count) | median tris | median dims")
for a,rs in sorted(A.items(), key=lambda kv:-len(kv[1])):
    sig = collections.Counter(tuple(r['mod_inputs'][k] for k in keys) for r in rs)
    tr = [st[r['obj']]['tris'] for r in rs]; dm=[st[r['obj']]['dim'] for r in rs]
    sg = "; ".join(f"{n}x[{s[0]}x{s[1]} F{s[2]} R{s[3]} "+"".join(l for l,v in zip('SEBLG',s[4:9]) if v)+f" Fe{s[9]}]" for s,n in sig.most_common(3))
    print(f"{a} | {len(rs)} | {sg} | {int(statistics.median(tr))} | {[round(statistics.median(d[i] for d in dm),1) for i in range(3)]}")
print("\n-- edo_village_tools.py outline")
t = bpy.data.texts['edo_village_tools.py'].as_string()
print(t[:1200])
print("... defs/classes:", re.findall(r'^(?:def|class) (\w+)', t, re.M)[:60])
print("\n-- edo_lights_sync.py head"); print(bpy.data.texts['edo_lights_sync.py'].as_string()[:700])
