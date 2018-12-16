fn = '/etc/ImageMagick-6/policy.xml'

data = open(fn).read()

data = data.replace('none', 'read|write')

with open(fn, 'w') as f:
    f.write(data)

print(data)
