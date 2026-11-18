import subprocess
subprocess.run(['npx','esbuild','app.js','--bundle','--minify','--format=iife','--outfile=app.min.js','--log-level=warning'],check=True)
js=open('app.min.js').read().replace('</script','<\\/script')
import html as H
py=open('../rabboni/rabboni_flix.py').read()
rab=open('rabboni.html').read().replace('/*PYCODE*/',H.escape(py))
import base64, io
from PIL import Image
def img(p):
    im=Image.open(p).convert('RGB'); im.thumbnail((640,640)); buf=io.BytesIO(); im.save(buf,'JPEG',quality=86); return base64.b64encode(buf.getvalue()).decode()
pcb=open('pcb.html').read().replace('/*IMG_TOP*/',img('../pcb/preview/render_top.png')).replace('/*IMG_BOT*/',img('../pcb/preview/render_bottom.png'))
html=open('template.html').read().replace('/*RABBONI*/',rab).replace('/*PCB*/',pcb).replace('/*APP*/',js)
open('index.html','w').write(html); print(len(html))
