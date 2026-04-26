import importlib.util, sys, os
sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location('rec', r'backend/tools/recommendation_tool.py')
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)

r = rec.get_recommendations('dien thoai re hon 18 trieu', reference_price=18525000)
print('status:', r['status'], 'count:', len(r.get('products', [])))
for p in r.get('products', [])[:4]:
    name = p['name'][:40]
    fp = p['final_price']
    print(f'  {name}: {fp:,.0f} VND')

r2 = rec.get_recommendations('thoi')
print('budget (thoi):', r2.get('max_price'))
