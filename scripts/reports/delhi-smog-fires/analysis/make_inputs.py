# Build the two boundary inputs the fire classification needs, so the analysis runs without the rest of the repository:
#   inputs/in_states_box.json  states of India that touch the study box, from geoBoundaries gbOpen IND ADM1 (boundaryID IND-ADM1-1811400,
#                              release commit 9469f09, source: DataMeet India community / Election Commission of India, CC BY 2.5 IN)
#   inputs/borders.json        HamariHawa's country outlines for India and Pakistan (copy of data/places/borders.json)
# python3 make_inputs.py <geoBoundaries-IND-ADM1.geojson> <borders.json>
import json, os, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); BOX = (73.0, 27.0, 79.5, 32.6)
src = sys.argv[1]; d = json.load(open(src)); out = {}
for f in d['features']:
    g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]; keep = []
    for p in polys:
        xs = [c[0] for c in p[0]]; ys = [c[1] for c in p[0]]
        if min(xs) < BOX[2] and max(xs) > BOX[0] and min(ys) < BOX[3] and max(ys) > BOX[1]: keep.append([[[round(x, 5), round(y, 5)] for x, y in ring] for ring in p])
    if keep: out[f['properties']['shapeISO']] = dict(name=f['properties']['shapeName'], polygons=keep)
meta = dict(source='geoBoundaries gbOpen IND ADM1', boundaryID='IND-ADM1-1811400', commit='9469f09', represents=2011, licence='CC BY 2.5 IN (DataMeet India community, Election Commission of India)',
            url='https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/ADM1/geoBoundaries-IND-ADM1.geojson', sha256=hashlib.sha256(open(src, 'rb').read()).hexdigest(), box=BOX)
json.dump(dict(meta=meta, states=out), open(os.path.join(HERE, 'inputs', 'in_states_box.json'), 'w'))
json.dump(json.load(open(sys.argv[2])), open(os.path.join(HERE, 'inputs', 'borders.json'), 'w'))
print({k: v['name'] for k, v in out.items()})
