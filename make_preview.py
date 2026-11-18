"""Optional illustrative design mock (NOT a screenshot of a running Qt app)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math

ROOT=Path(__file__).parent
W,H=1360,860
bg=Image.new('RGB',(W,H),(8,11,21))
aurora=Image.new('RGBA',(W,H),(0,0,0,0))
g=ImageDraw.Draw(aurora)
for xy,c in [((160,80,520,510),(105,58,215,95)),((980,-100,1450,440),(128,245,19,80)),((410,580,1050,1140),(33,107,228,70))]:
 g.ellipse(xy,fill=c)
aurora=aurora.filter(ImageFilter.GaussianBlur(145))
bg=Image.alpha_composite(bg.convert('RGBA'),aurora)
ly=Image.new('RGBA',(W,H),(0,0,0,0))
d=ImageDraw.Draw(ly)
inter='/usr/share/fonts/opentype/inter/Inter-Regular.otf'
semi='/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
bold='/usr/share/fonts/opentype/inter/Inter-Bold.otf'
font=lambda size,weight='regular': ImageFont.truetype({'regular':inter,'semibold':semi,'bold':bold}[weight],size)

def txt(x,y,s,sz=16,col='#e9efff',weight='regular'):
 d.text((x,y),s,font=font(sz,weight),fill=col,anchor='lt')

def panel(x,y,x2,y2,r=25):
 d.rounded_rectangle((x+3,y+13,x2+3,y2+15),radius=r,fill=(0,0,0,56))
 d.rounded_rectangle((x,y,x2,y2),radius=r,fill=(27,33,54,215),outline=(194,210,248,52),width=2)

def btn(x,y,w,h,text,kind='normal'):
 fill={'normal':(78,91,122,79),'accent':(195,255,40,255),'danger':(93,34,55,156)}[kind]
 fg='#101809' if kind=='accent' else ('#ff9cae' if kind=='danger' else '#dce4f5')
 d.rounded_rectangle((x,y,x+w,y+h),radius=13,fill=fill,outline=(215,232,252,41))
 bb=d.textbbox((0,0),text,font=font(15,'semibold'))
 tw,th=bb[2]-bb[0],bb[3]-bb[1]
 d.text((x+(w-tw)//2,y+(h-th)//2-2),text,font=font(15,'semibold'),fill=fg)

# brand
icon=Image.open(ROOT/'assets/icon.png').convert('RGBA').resize((70,70),Image.Resampling.LANCZOS)
ly.alpha_composite(icon,(38,21))
txt(122,29,'GIF',32,'#f6f8ff','bold')
txt(186,29,'Ripper',32,'#c4ff28','bold')
txt(122,71,'CAPTURE   /   FRAME EDITOR   /   EXPORT',11,'#93a4bb','semibold')
btn(760,36,170,48,'↗  Otevřít GIF')
btn(945,36,205,48,'●  Nahrát celou obrazovku','danger')
btn(1165,36,155,48,'↓  Export GIF','accent')
d.line((25,111,1335,111),fill=(255,255,255,30),width=1)

panel(25,129,956,613)
panel(973,129,1335,613)
txt(51,152,'◈   PŘEHRÁVAČ  /  PREVIEW',13,'#aab6d0','semibold')
d.rounded_rectangle((756,147,927,180),radius=15,fill=(115,130,155,35))
txt(769,156,'ukazka.gif',13,'#c8d3e8','semibold')
d.rounded_rectangle((43,192,938,532),radius=20,fill=(8,11,20,255),outline=(188,211,245,20))
# hero artwork prominently on dark stage
brand=Image.open(ROOT/'assets/brand.png').convert('RGBA')
brand.thumbnail((375,332),Image.Resampling.LANCZOS)
ly.alpha_composite(brand,(43+(895-brand.width)//2,192+(340-brand.height)//2))
btn(48,545,63,46,'Ⅰ◀')
btn(121,545,63,46,'◀')
btn(193,545,143,46,'▶  Přehrát','accent')
btn(345,545,55,46,'■')
btn(410,545,60,46,'▶Ⅰ')
txt(727,557,'00:00.200 / 00:02.000',14,'#d9e2ef','semibold')

# Illustrative mock only: final placement is determined by the Qt layout.
txt(998,153,'✂  STŘIH  /  EDITOR',14,'#acb8d1','semibold')
d.rounded_rectangle((996,194,1311,230),radius=11,fill=(63,71,98,87))
txt(1010,207,'VÝBĚR ÚSEKU',12,'#d3e0ef','semibold')
txt(1008,246,'ZAČÁTEK  /  OD',11,'#c4ff28','semibold')
txt(1168,246,'KONEC  /  DO',11,'#ffb0c1','semibold')
d.rounded_rectangle((1006,271,1144,313),radius=11,fill='#101B2C',outline='#67B8FF',width=2)
d.rounded_rectangle((1160,271,1303,313),radius=11,fill='#101B2C',outline='#B5A2FF',width=2)
txt(1020,280,'03',17,'#ffffff','bold')
txt(1174,280,'07',17,'#ffffff','bold')
def colored_btn(x,y,w,h,label,bg,border,fg):
 d.rounded_rectangle((x,y,x+w,y+h),radius=12,fill=bg,outline=border,width=3)
 d.text((x+w/2,y+h/2-2),label,font=font(13,'semibold'),fill=fg,anchor='mm')
colored_btn(1006,328,140,41,'↤ Nastavit OD','#183C5F','#67B8FF','#F2FAFF')
colored_btn(1158,328,145,41,'Nastavit DO ↦','#312B59','#B5A2FF','#F5F1FF')
colored_btn(1006,381,297,45,'✂ VYSTŘIHNOUT ÚSEK','#67263D','#FF6389','#FFF0F4')
txt(1009,445,'RYCHLÝ STŘIH',12,'#aab6d0','semibold')
colored_btn(1006,472,297,40,'↤ Odstranit před snímkem','#50371F','#FFBF6B','#FFF4E5')
colored_btn(1006,519,297,40,'Odstranit za snímkem ↦','#50371F','#FFBF6B','#FFF4E5')
txt(1009,577,'FPS',12,'#aab6d0','semibold')
colored_btn(1173,565,130,38,'12 FPS','#1B342D','#A8EE68','#E7FFD7')

panel(25,629,1335,807)
txt(47,653,'▤  ČASOVÁ OSA  /  FRAMES',13,'#b8c8d9','semibold')
d.rounded_rectangle((1142,645,1311,679),radius=15,fill=(83,99,122,70))
txt(1158,654,'24 SNÍMKŮ',13,'#d4dde9','semibold')
d.rounded_rectangle((41,689,1317,786),radius=13,fill=(10,14,25,236))
from PIL import ImageSequence
frames=[]
im=Image.open(ROOT/'demo/ukazka.gif')
for i in range(getattr(im,'n_frames',1)):
 try: im.seek(i);frames.append(im.convert('RGB').copy())
 except EOFError:break
for j in range(11):
 x=55+j*114
 rr=(x,697,x+105,754)
 d.rounded_rectangle(rr,radius=8,fill=(46,57,80,230))
 fr=frames[round(j*(len(frames)-1)/10)]
 fr.thumbnail((102,55),Image.Resampling.LANCZOS)
 ly.paste(fr,(x+(105-fr.width)//2,697+(57-fr.height)//2))
 txt(x+7,758,str(j*2+1),11,'#8796ac')
d.rounded_rectangle((293,772,735,783),radius=5,fill=(192,255,50,75))
d.line((300,685,300,787),fill='#c4ff28',width=3)
d.line((736,685,736,787),fill='#ff94ae',width=3)
d.line((500,685,500,787),fill='#f4f9ff',width=3)
txt(25,830,'●  Připraveno. Otevři GIF nebo spusť nahrávání.',12,'#9faec2')
txt(932,830,'GIFRIPPER 3.0  •  UKÁZKA',11,'#66768c','semibold')
colored_btn(1169,818,166,34,'☀ Světlý režim','#293A55','#465673','#E6F0FC')
result=Image.alpha_composite(bg,ly)
result.convert('RGB').save(ROOT/'design-preview.png',quality=90,optimize=True)
