import subprocess
subprocess.run(['npx','esbuild','app.js','--bundle','--minify','--format=iife','--outfile=app.min.js','--log-level=warning'],check=True)
js=open('app.min.js').read().replace('</script','<\\/script')
import html as H
import base64, io
from PIL import Image
def img(p):
    im=Image.open(p).convert('RGB'); im.thumbnail((640,640)); buf=io.BytesIO(); im.save(buf,'JPEG',quality=86); return base64.b64encode(buf.getvalue()).decode()
pcb=open('pcb.html').read().replace('/*IMG_TOP*/',img('../pcb/preview/render_top.png')).replace('/*IMG_BOT*/',img('../pcb/preview/render_bottom.png'))
onb=open('onboard.html').read().replace('/*IMG_TOP*/',img('../pcb2/preview/render_top.png')).replace('/*IMG_ASM*/',img('../pcb2/fab/fz-flix-onboard-assembly.png'))
html=open('template.html').read().replace('/*PCB*/',pcb).replace('/*ONBOARD*/',onb).replace('/*APP*/',js)
open('index.html','w').write(html); print(len(html))
