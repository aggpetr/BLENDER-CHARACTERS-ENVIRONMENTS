import bpy, sys, json, collections
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
g = bpy.data.node_groups['GN_EdoHouse']
iface = []
for it in g.interface.items_tree:
    if it.item_type == 'SOCKET' and it.in_out == 'INPUT':
        d = getattr(it, 'default_value', None)
        try: d = list(d)
        except TypeError: pass
        iface.append(dict(name=it.name, id=it.identifier, type=it.socket_type, default=d,
                          min=getattr(it,'min_value',None), max=getattr(it,'max_value',None), panel=it.parent.name if it.parent and it.parent.name else ''))
print("INPUTS:", len(iface))
for i in iface: print(" ", i['panel'], '|', i['name'], i['type'], i['default'], i['min'], i['max'])
print("OUTPUTS:", [it.name+':'+it.socket_type for it in g.interface.items_tree if it.item_type=='SOCKET' and it.in_out=='OUTPUT'])

objs = [o for o in bpy.data.objects if any(m.type=='NODES' and m.node_group==g for m in o.modifiers)]
rows = []
for o in objs:
    m = next(m for m in o.modifiers if m.type=='NODES' and m.node_group==g)
    r = dict(obj=o.name, coll=[c.name for c in o.users_collection], loc=[round(v,2) for v in o.location], rot=round(o.rotation_euler.z,3), scale=[round(v,2) for v in o.scale], mod_inputs={})
    for i in iface:
        try:
            e = m.properties.inputs[i['id']]
            v = e['value'] if 'value' in list(e.keys()) else None
        except Exception as ex:
            continue
        try: v = list(v)
        except TypeError: pass
        if hasattr(v,'name'): v = v.name
        r['mod_inputs'][i['name']] = v
    rows.append(r)
json.dump(dict(iface=iface, rows=rows), open(sys.argv[-2], 'w'), default=str, indent=1)
print("houses:", len(rows))
# distinct values per input
vals = collections.defaultdict(collections.Counter)
for r in rows:
    for k,v in r['mod_inputs'].items(): vals[k][json.dumps(v, default=str)] += 1
print("-- parameters that vary across houses (distinct count, top values)")
for k,c in sorted(vals.items(), key=lambda kv: -len(kv[1])):
    print(f"  {k}: {len(c)} distinct; ", dict(c.most_common(6)))
