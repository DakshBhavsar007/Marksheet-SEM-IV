import json

f = open('new_datamarksheet.js', 'r', encoding='utf-8')
c = f.read()
f.close()
s = c.find('[')
e = c.rfind(']') + 1
data = json.loads(c[s:e])

has_p24 = [d for d in data if d.get('python24') is not None]
print(f"Students with python24: {len(has_p24)}")

sy4 = [d for d in data if d.get('dept') == 'SY4']
print(f"SY4 with python24: {len([d for d in sy4 if d.get('python24') is not None])}")

daksh = [d for d in data if '24002171410007' == d.get('enrollment')]
if daksh:
    d = daksh[0]
    print(f"Daksh: python24={d.get('python24')}, python2={d.get('python2')}, total={d.get('total')}")
else:
    print("Daksh not found")

print("Sample SY4:")
for d in sy4[:5]:
    name = d['name'][:35]
    print(f"  {name:35s} python24={d.get('python24')} python2={d.get('python2')} total={d.get('total')}")

# Verify enrollment-mark mapping for a few known entries from PDF
print("\nCross-check with PDF:")
checks = {
    '24002170110154': 24.5,  # RAHUL LUMBHANI - rank 1
    '24002171410030': 24.0,  # PATEL VED - rank 2
    '24002170110133': 24.0,  # PATEL VRAJ
}
for enr, expected in checks.items():
    match = [d for d in data if d.get('enrollment') == enr]
    if match:
        actual = match[0].get('python24')
        status = 'OK' if actual == expected else f'MISMATCH (expected {expected})'
        print(f"  {enr}: python24={actual} {status} name={match[0]['name']}")
