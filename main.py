import pygame, random, json, os

# --- AUDIO FIX ---
os.environ["SDL_AUDIODRIVER"]="dummy"
pygame.init()
try: pygame.mixer.init()
except: pass

# --- SCREEN ---
WIDTH, HEIGHT=520,720
screen=pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("BlockBlast ULTRA FINAL")
clock=pygame.time.Clock()

# --- COLORS ---
BG=(20,20,30); GRID_BG=(35,35,50); GRID_LINE=(60,60,80)
WHITE=(255,255,255); YELLOW=(255,215,100); RED=(255,80,80)
GREEN=(100,255,140)

COLORS=[(255,120,120),(120,180,255),(255,210,120),(140,255,180),(200,140,255)]

GRID_SIZE=10; CELL=42; OFFSET_Y=60

font=pygame.font.SysFont("arial",26,True)
font_small=pygame.font.SysFont("arial",16)
font_big=pygame.font.SysFont("arial",40,True)

# --- SAVE ---
def load():
    if os.path.exists("progress.json"):
        try:
            with open("progress.json") as f:
                d=json.load(f)
                d.setdefault("coins",0)
                d.setdefault("skins",[])
                d.setdefault("inventory",{})
                return d
        except: pass
    return {"coins":0,"skins":[],"inventory":{}}

def save():
    with open("progress.json","w") as f:
        json.dump(progress,f)

progress=load()
coins=progress["coins"]
owned_skins=progress["skins"]
inventory=progress["inventory"]

# --- GRID ---
grid=[[0]*GRID_SIZE for _ in range(GRID_SIZE)]
score=0

# --- SHAPES ---
SHAPES=[[(0,0)],[(0,0),(1,0)],[(0,0),(0,1)],
[(0,0),(1,0),(0,1)],[(0,0),(1,0),(2,0)],
[(0,0),(0,1),(0,2)],[(0,0),(1,0),(2,0),(1,1)]]

# --- BLOCKS ---
def new_block():
    return {"shape":random.choice(SHAPES),
            "color":random.choice(owned_skins if owned_skins else COLORS)}

def gen_blocks(): return [new_block(),new_block(),new_block()]
blocks=gen_blocks()
selected=None
drag=(0,0)

# --- SHOP ---
shop_open=False
shop_btn=pygame.Rect(440,10,60,40)

shop_scroll=0
SCROLL_SPEED=25

shop_items=[]
for i in range(20):
    shop_items.append({
        "name":f"Skin {i+1}",
        "color":(random.randint(80,255),random.randint(80,255),random.randint(80,255)),
        "price":50*(i+1),
        "type":"skin"
    })

shop_items += [
{"name":"Revival","price":150,"type":"power"},
{"name":"Clear Row","price":120,"type":"power"},
{"name":"Clear Col","price":120,"type":"power"},
{"name":"Double Coins","price":130,"type":"power"},
]

# --- PARTICLES ---
particles=[]
def spawn_particles(x,y,color):
    for _ in range(8):
        particles.append({"x":x,"y":y,"vx":random.uniform(-2,2),"vy":random.uniform(-2,2),"life":20,"color":color})

def draw_particles():
    for p in particles[:]:
        p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["life"]-=1
        pygame.draw.circle(screen,p["color"],(int(p["x"]),int(p["y"])),3)
        if p["life"]<=0: particles.remove(p)

# --- GAME ---
def draw_grid():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            r=pygame.Rect(x*CELL,y*CELL+OFFSET_Y,CELL,CELL)
            pygame.draw.rect(screen,GRID_BG,r)
            pygame.draw.rect(screen,GRID_LINE,r,1)
            if grid[y][x]:
                pygame.draw.rect(screen,grid[y][x],r.inflate(-6,-6),border_radius=6)

def draw_blocks():
    for i,b in enumerate(blocks):
        if not b: continue
        if selected and selected[0]==i: continue
        
        base_x=40+i*140
        base_y=650
        
        for c in b["shape"]:
            pygame.draw.rect(screen,b["color"],
                (base_x+c[0]*22,base_y+c[1]*22,20,20),border_radius=6)

def draw_drag():
    if not selected: return
    b=selected[1]
    for c in b["shape"]:
        pygame.draw.rect(screen,b["color"],
            (drag[0]+c[0]*24,drag[1]+c[1]*24,22,22),border_radius=6)

def ghost(block,gx,gy):
    for c in block["shape"]:
        x=gx+c[0]; y=gy+c[1]
        if 0<=x<GRID_SIZE and 0<=y<GRID_SIZE:
            r=pygame.Rect(x*CELL,y*CELL+OFFSET_Y,CELL,CELL)
            pygame.draw.rect(screen,WHITE,r.inflate(-10,-10),2)

def can_place(b,gx,gy):
    for c in b["shape"]:
        x=gx+c[0]; y=gy+c[1]
        if x<0 or y<0 or x>=GRID_SIZE or y>=GRID_SIZE: return False
        if grid[y][x]!=0: return False
    return True

def place(b,gx,gy):
    global score,coins
    for c in b["shape"]:
        x=gx+c[0]; y=gy+c[1]
        grid[y][x]=b["color"]
        spawn_particles(x*CELL+20,y*CELL+OFFSET_Y+20,b["color"])
    score+=len(b["shape"])
    coins+=len(b["shape"])

# 🔥 FIX: Linien löschen wieder drin
def clear_lines():
    global score, coins
    
    cleared = 0

    for y in range(GRID_SIZE):
        if all(grid[y][x] for x in range(GRID_SIZE)):
            for x in range(GRID_SIZE):
                grid[y][x] = 0
            cleared += 1

    for x in range(GRID_SIZE):
        if all(grid[y][x] for y in range(GRID_SIZE)):
            for y in range(GRID_SIZE):
                grid[y][x] = 0
            cleared += 1

    if cleared > 0:
        score += cleared * 50
        coins += cleared * 10

# --- MAIN ---
running=True
while running:
    mx,my=pygame.mouse.get_pos()
    drag=(mx-10,my-10)
    
    screen.fill(BG)
    
    draw_grid()
    draw_particles()
    draw_blocks()
    draw_drag()
    
    if selected:
        gx,gy=mx//CELL,(my-OFFSET_Y)//CELL
        if can_place(selected[1],gx,gy):
            ghost(selected[1],gx,gy)
    
    # SHOP BUTTON 🛒
    pygame.draw.rect(screen,(100,120,180),shop_btn,border_radius=10)
    pygame.draw.rect(screen,(180,200,255),shop_btn,2,border_radius=10)
    screen.blit(font_small.render("🛒",True,WHITE),(shop_btn.x+18,shop_btn.y+8))
    
    # UI
    screen.blit(font.render(f"Score: {score}",True,WHITE),(10,10))
    screen.blit(font_small.render(f"Coins: {coins}",True,YELLOW),(10,45))
    
    # SHOP
    if shop_open:
        pygame.draw.rect(screen,(40,40,70),(60,100,400,500),border_radius=12)
        
        y=140+shop_scroll
        for item in shop_items:
            r=pygame.Rect(80,y,360,50)
            
            if 100<y<600:
                pygame.draw.rect(screen,(70,70,110),r,border_radius=8)
                
                owned=(item.get("color") in owned_skins) if item["type"]=="skin" else False
                txt=item["name"]+" "
                txt+= "OWNED" if owned else str(item["price"])+"$"
                
                screen.blit(font_small.render(txt,True,WHITE),(r.x+10,r.y+15))
                item["rect"]=r
            else:
                item["rect"]=None
            
            y+=60
    
    # EVENTS
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            progress["coins"]=coins
            progress["skins"]=owned_skins
            progress["inventory"]=inventory
            save()
            pygame.quit(); exit()
        
        if e.type==pygame.MOUSEWHEEL and shop_open:
            shop_scroll += e.y * SCROLL_SPEED
            max_scroll=0
            min_scroll=-max(0,len(shop_items)*60-400)
            shop_scroll=max(min(shop_scroll,max_scroll),min_scroll)
        
        if e.type==pygame.MOUSEBUTTONDOWN:
            if shop_btn.collidepoint(mx,my):
                shop_open=not shop_open
            
            elif shop_open:
                for item in shop_items:
                    if item["rect"] and item["rect"].collidepoint(mx,my):
                        if coins>=item["price"]:
                            coins-=item["price"]
                            if item["type"]=="skin":
                                owned_skins.append(item["color"])
                            else:
                                inventory[item["name"]]=inventory.get(item["name"],0)+1
            
            elif not shop_open:
                for i,b in enumerate(blocks):
                    if b:
                        bx=40+i*140; by=650
                        if bx<mx<bx+100 and by<my<by+100:
                            selected=(i,b)
        
        if e.type==pygame.MOUSEBUTTONUP and selected:
            i,b=selected
            gx,gy=mx//CELL,(my-OFFSET_Y)//CELL
            if can_place(b,gx,gy):
                place(b,gx,gy)
                clear_lines()   # 🔥 WICHTIG
                blocks[i]=None
            selected=None
    
    if all(b is None for b in blocks):
        blocks=gen_blocks()
    
    pygame.display.flip()
    clock.tick(60)
