import subprocess
subprocess.run(['npx','esbuild','app.js','--bundle','--minify','--format=iife','--outfile=app.min.js','--log-level=warning'],check=True)
js=open('app.min.js').read().replace('</script','<\\/script')
import html as H
py=open('../rabboni/rabboni_flix.py').read()
rab=open('rabboni.html').read().replace('/*PYCODE*/',H.escape(py))
html=open('template.html').read().replace('/*RABBONI*/',rab).replace('/*APP*/',js)
open('index.html','w').write(html); print(len(html))
