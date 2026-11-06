# ARC-AGI-3 candidate task es01 (Extreme Sneeze).
# Author: Team Turducken agents, under Mark Barney's direction
# Date: October 2026
# PURPOSE: es01, Extreme Sneeze: spread an alien infection through a city, hopping between infected hosts.
# SRP/DRY check: Pass -- one game class; the sprite functions above it only draw.
# Updated: 06-November-2026, Claude Fable 5.1 -- dead code removed (unused OX/OY, build_index, _before, _effect and a
#   stray local); the loose sprite-book string is now a comment. No change to play.

from copy import deepcopy
from collections import deque
from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite

CELL = 6
W, H = 10, 9
DIRS = {1:(0,-1), 2:(0,1), 3:(-1,0), 4:(1,0)}

def _cross(width, row, gates):
    return [(x,row) for x in range(width) if x not in gates]


def _partitions(height, columns):
    return [(x,y) for x,gates in columns for y in range(height) if y not in gates]


LEVELS_SPEC = [
 dict(size=(7,6), alien=(1,3), people=[(3,3),(5,3),(6,5)], doctors=[], walls=[], build=[], goal=2),
 dict(size=(20,10), alien=(1,4), people=[(3,4),(2,1),(8,4),(12,1),(17,2),(17,8)], doctors=[], walls=_partitions(10,[(6,{1,2,4})]), vents=[(6,4)], anchored=[(8,4),(17,8)], build=[]),
 dict(size=(18,12), alien=(1,4), people=[(3,4),(6,2),(9,4),(14,5),(16,9)], hostile=[(1,9)], doctors=[], walls=_partitions(12,[(7,{4}),(12,{2,3,7,8})]), vents=[(7,4)], anchored=[(9,4)], build=[]),
 dict(size=(19,13), alien=(1,5), people=[(3,5),(6,3),(9,3),(15,5),(17,10)], hostile=[(2,8),(9,10)], doctors=[(14,8)], walls=_partitions(13,[(7,{2,3,8,9}),(13,{4,5,9,10})]), build=[(7,3),(13,5),(13,9)]),
 dict(size=(20,14), alien=(2,6), people=[(4,6),(6,3),(10,4),(14,8),(15,3),(18,11)], hostile=[(3,8),(9,9),(16,8)], doctors=[(12,10)], walls=_partitions(14,[(7,{3,4,9,10}),(13,{8})])+_cross(20,7,{3,4,8,9,15,16}), vents=[(13,8)], anchored=[(14,8)], build=[(7,4),(7,9)]),
 dict(size=(21,15), alien=(2,7), people=[(4,7),(6,4),(10,3),(15,4),(19,12)], hostile=[(3,9),(10,11),(16,10)], doctors=[(14,12)], walls=_partitions(15,[(7,{3,4,10,11}),(13,{4,5,9,10}),(18,{2,3,11,12})]), build=[(7,4),(13,9),(18,11)]),
 dict(size=(22,15), alien=(3,7), people=[(4,7),(6,3),(10,3),(16,3),(20,12)], hostile=[(2,6),(3,9),(12,7),(3,14)], doctors=[(16,10)], walls=_partitions(15,[(7,{3,4,7,9,10}),(14,{4,5,10,11}),(19,{2,3,11,12})]), build=[(7,4),(14,10),(19,11)]),
 dict(size=(24,16), alien=(2,8), people=[(4,8),(6,3),(10,4),(16,3),(21,13)], hostile=[(3,10),(6,11),(10,12),(17,10)], doctors=[(15,12),(21,6)], walls=_partitions(16,[(7,{3,4,10,11}),(14,{4,5,10,11}),(20,{2,3,11,12})])+_cross(24,7,{2,3,9,10,16,17,22,23}), build=[(7,4),(14,10),(20,11)])
]

# Six-pixel creatures and scenery. Sprites contain no game rules; -1 leaves the floor visible.


def block(colour: int, cell: int = 4) -> list[list[int]]:
    return [[colour] * cell for _ in range(cell)]

def figure(body: int, mark: int | None = None, cell: int = 4) -> list[list[int]]:
    px = [[-1] * cell for _ in range(cell)]
    mid = cell // 2
    for x in range(1, cell - 1):
        px[0][x] = body
    for y in range(1, cell - 1):
        for x in range(cell):
            px[y][x] = body
    px[cell - 1][0] = px[cell - 1][mid] = -1
    for x in range(cell):
        if px[cell - 1][x] != -1:
            px[cell - 1][x] = body
    px[cell - 1][1] = body
    px[cell - 1][cell - 1] = body
    if mark is not None and cell >= 4:
        px[mid][mid] = mark
    return px

def ease_out(t: float) -> float:
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return 1 - (1 - t) * (1 - t)

def tween(a: int, b: int, step: int, span: int) -> int:
    if span <= 0:
        return b
    return int(round(a + (b - a) * ease_out(step / span)))


def _direction_mark(px, heading, colour):
    dx, dy = heading
    if dx > 0:
        px[2][5] = colour
    elif dx < 0:
        px[2][0] = colour
    elif dy < 0:
        px[0][3] = colour
    else:
        px[5][3] = colour
    return px


def alien_face(heading, damage=0):
    p = [
        [-1, 14, -1, -1, 14, -1],
        [-1, 14, 14, 14, 14, -1],
        [14,  5,  0,  0,  5, 14],
        [14, 14,  6,  6, 14, 14],
        [-1, 14, 14, 14, 14, -1],
        [14, -1, 14, 14, -1, 14],
    ]
    dx,dy=heading
    if dx>0: p[2][5]=11
    elif dx<0: p[2][0]=11
    elif dy<0: p[1][3]=11
    else: p[4][3]=11
    order = [(1,0),(4,0),(0,5),(5,5),(0,2),(5,2),(1,1),(4,1),
             (1,4),(4,4),(2,5),(3,5),(0,3),(5,3),(2,1),(3,1),
             (1,3),(4,3),(2,4),(3,4),(2,3),(3,3),(1,2),(4,2),(2,2),(3,2)]
    for x,y in order[:damage]: p[y][x] = -1
    return p


def exposure_mark(p,exposure):
    if exposure>=1:p[2][2]=14
    if exposure>=2:p[2][3]=14
    return p

def human_face(heading,infected,controlled,exposure=0,variant=0):
    p=figure(9,cell=6)
    skin=14 if infected else 12
    hair=(13,5,15)[variant%3]
    outfit=(9,12,15)[variant%3]
    p[0]=[-1,hair,hair,hair,hair,-1]
    p[1]=[-1,skin,5,skin,5,-1]
    p[2]=[-1,skin,skin,skin,skin,-1]
    p[3]=[outfit,outfit,10,10,outfit,outfit]
    p[4]=[-1,outfit,10,10,outfit,-1]
    p[5]=[-1,4,-1,-1,4,-1]
    if not infected:exposure_mark(p,exposure)
    if infected:
        p[1][2]=p[1][4]=6
        p[3][2]=p[3][3]=14
    if controlled:
        p[0][0]=p[0][5]=6
        p[5][0]=p[5][5]=6
        p[0][2]=p[0][3]=14
        p[4][2]=p[4][3]=6
    return _direction_mark(p,heading,11 if controlled else 0)

def doctor_face(heading,exposure=0,intent=False):
    p=figure(0,cell=6)
    p[0]=[-1,0,0,0,0,-1]
    p[1]=[-1,12,5,12,5,-1]
    p[2]=[-1,12,12,12,12,-1]
    p[3]=[0,0,10,10,0,0]
    p[4]=[-1,0,9,9,0,-1]
    p[5]=[-1,9,-1,-1,9,-1]
    exposure_mark(p,exposure)
    if intent:
        p[0][0]=p[0][5]=10
    return _direction_mark(p,heading,11)

def hostile_face(heading,windup=False,exposure=0):
    p=[[-1,13,13,13,13,-1], [8,12,5,12,5,8], [8,12,12,12,12,8],
       [-1,13,8,8,13,-1],[-1,13,13,13,13,-1],[-1,4,-1,-1,4,-1]]
    exposure_mark(p,exposure)
    if windup:
        p[0][0]=p[0][5]=11
        p[1][0]=p[1][5]=11
    return _direction_mark(p,heading,8)


def medical_wall():
    p = block(0, 6)
    p[0] = [1, 0, 0, 0, 0, 1]
    p[1] = [0, 10, 10, 10, 10, 0]
    p[2] = [0, 10, 0, 0, 10, 0]
    p[3] = [0, 10, 0, 0, 10, 0]
    p[4] = [0, 10, 10, 10, 10, 0]
    p[5] = [1, 0, 0, 0, 0, 1]
    return p


def impact_ring():
    return [[8 if ((y in (0,7) and x in (2,3,4,5)) or
                   (y in (1,6) and x in (1,6)) or
                   (y in (2,3,4,5) and x in (0,7))) else -1
             for x in range(8)] for y in range(8)]


def vent_wall():
    return [[2,2,2,2,2,2], [2,10,4,4,10,2], [2,10,4,4,10,2],
            [2,10,4,4,10,2], [2,10,4,4,10,2], [2,2,2,2,2,2]]


def room_wall():
    p = block(3, 6)
    p[0] = [2, 2, 2, 2, 2, 2]
    p[1] = [3, 3, 3, 4, 3, 3]
    p[2] = [4, 4, 4, 4, 4, 4]
    p[3] = [3, 4, 3, 3, 3, 3]
    p[4] = [3, 4, 3, 3, 3, 3]
    p[5] = [4, 4, 4, 4, 4, 4]
    return p


def droplet():
    return [
        [-1, -1, 14, -1, -1, -1],
        [-1, 14,  0, 14, -1, -1],
        [14, 14, 14, 14, 14, -1],
        [-1, 14, 14, 14, -1, -1],
        [-1, -1, 14, -1, -1, 10],
        [-1, -1, -1, -1, 10, -1],
    ]


class Es01(ARCBaseGame):
    def __init__(self):
        self._dynamic = []
        self._phase = 0
        super().__init__(game_id='es01',
            levels=[Level(sprites=[], grid_size=(64,64), data={'index': i})
                    for i in range(len(LEVELS_SPEC))],
            camera=Camera(width=64, height=64, background=5, letter_box=5),
            available_actions=[1,2,3,4,5,6], win_score=len(LEVELS_SPEC))

    def on_set_level(self, level):
        spec = LEVELS_SPEC[self.level_index]
        self.alien = {'pos':spec['alien'], 'dir':(1,0), 'damage':0}
        self.people = [dict(pos=p, infected=False, exposure=0, doctor=False, anchored=p in spec.get('anchored',()), dir=(1,0))
                       for p in spec['people']]
        self.people += [dict(pos=p, infected=False, exposure=0, doctor=False, hostile=True, windup=False, dir=(-1,0))
                        for p in spec.get('hostile',[])]
        self.people += [dict(pos=p, infected=False, exposure=0, doctor=True, dir=(-1,0))
                        for p in spec['doctors']]
        self.control = None
        if self.level_index > 0:
            self.control = 0
            self.people[0]['infected'] = True
            self.people[0]['exposure'] = 3
        self.walls = set(spec['walls'])
        self.vents = set(spec.get('vents',[]))
        self.medical = {}
        self.tick = 0
        self.supply = 3
        self.cough_pending = None
        self.width, self.height = spec.get('size',(W,H))
        self.ox = max(1,(64-self.width*CELL)//2)
        self.oy = max(1,(64-self.height*CELL)//2)
        self.camera.x = self.camera.y = 0
        self._phase = 0
        self._frames = []
        self._events = []
        self._dynamic = []
        self._result_won = False
        self._result_lost = False
        self._build_floor()
        self._draw()

    def _sprite(self, pixels, x, y, name, layer=1):
        s = Sprite(pixels=pixels, x=x, y=y, name=name, layer=layer)
        self.current_level.add_sprite(s)
        return s

    def _build_floor(self):
        self.scene = ('street','market','market','clinic','clinic',
                      'transit','transit','transit')[self.level_index]
        width,height=self.width*CELL,self.height*CELL
        base=3 if self.scene=='clinic' else 4
        floor=block(base,width)[:height]
        for y in range(self.height):
            for x in range(self.width):
                px,py=x*CELL,y*CELL
                if self.scene=='clinic':
                    floor[py][px+2]=floor[py][px+3]=2
                    if (x+2*y)%8==0: floor[py+5][px]=10
                elif self.scene=='market':
                    floor[py][px+2]=floor[py][px+3]=3
                    if (x+2*y)%4==0:
                        floor[py+4][px+1]=floor[py+4][px+2]=13
                        floor[py+5][px+1]=13
                elif self.scene=='transit':
                    floor[py][px+2]=floor[py][px+3]=3
                    if y%5==0:
                        for dx in range(CELL): floor[py+4][px+dx]=5
                        if x%2==0:
                            floor[py+5][px+1]=floor[py+5][px+2]=11
                else:
                    floor[py][px+2]=floor[py][px+3]=3
                    if y==2 and x%2==0:
                        floor[py+5][px+1]=floor[py+5][px+2]=1
                    if y==4 and x%2==1:
                        floor[py+1][px+3]=floor[py+1][px+4]=11
        self._sprite(floor,self.ox,self.oy,'floor',0)
        left,right=self.ox-1,self.ox+width
        top,bottom=self.oy-1,self.oy+height
        trim={'street':2,'market':13,'clinic':10,'transit':11}[self.scene]
        self._sprite([[trim]*(width+2)],left,top,'frame_top',1)
        self._sprite([[trim]*(width+2)],left,bottom,'frame_bottom',1)
        self._sprite([[trim] for _ in range(height)],left,self.oy,'frame_left',1)
        self._sprite([[trim] for _ in range(height)],right,self.oy,'frame_right',1)
        for x,y in ((left,top),(right,top),(left,bottom),(right,bottom)):
            self._sprite([[10]],x,y,f'corner_{x}_{y}',2)

    def _clear_dynamic(self):
        for sprite in self._dynamic:
            self.current_level.remove_sprite(sprite)
        self._dynamic = []

    def _put(self, pixels, pos, name, layer=2):
        x,y=pos
        self._dynamic.append(self._sprite(pixels, self.ox+round(x*CELL), self.oy+round(y*CELL), name, layer))

    def _draw(self, positions=None, effects=(), beam=None):
        self._clear_dynamic()
        if self.scene == 'market':
            wall = [[12,12,13,13,12,12], [12,12,13,13,12,12],
                    [3,3,3,3,3,3], [3,13,13,13,13,3],
                    [3,13,12,13,13,3], [4,4,4,4,4,4]]
        elif self.scene == 'clinic':
            wall = [[2,2,2,2,2,2], [3,3,10,10,3,3],
                    [3,3,9,9,3,3], [3,3,9,9,3,3],
                    [3,3,10,10,3,3], [4,4,4,4,4,4]]
        elif self.scene == 'transit':
            wall = [[2,2,2,2,2,2], [3,3,3,3,3,3],
                    [11,11,3,3,11,11], [3,3,4,4,3,3],
                    [3,3,4,4,3,3], [4,4,4,4,4,4]]
        else: wall = room_wall()
        for x,y in sorted(self.walls): self._put(wall,(x,y),f'wall_{x}_{y}')
        for x,y in sorted(self.vents): self._put(vent_wall(),(x,y),f'vent_{x}_{y}')
        for (x,y),strength in sorted(self.medical.items()):
            face=medical_wall()
            if strength == 1:
                face[2][2] = face[3][3] = 8
            self._put(face,(x,y),f'medical_{x}_{y}',3)
        for doctor in self.people:
            b=doctor.get('build_target') if doctor.get('doctor') and not doctor['infected'] else None
            if b and b not in self.medical:
                marker=[[-1]*6 for _ in range(6)]
                marker[0][0]=marker[0][5]=marker[5][0]=marker[5][5]=10
                self._put(marker,b,'next_barricade',1)
        apos = positions.get('alien',self.alien['pos']) if positions else self.alien['pos']
        self._put(alien_face(self.alien['dir'],self.alien['damage']), apos, 'alien', 4)
        sx=self.ox+round(apos[0]*CELL)-self.camera.x
        sy=self.oy+round(apos[1]*CELL)-self.camera.y
        if sx<0 or sy<0 or sx+CELL>64 or sy+CELL>64:
            ex=max(1,min(57,sx)); ey=max(1,min(57,sy))
            self._dynamic.append(self._sprite(alien_face(self.alien['dir'],self.alien['damage']),self.camera.x+ex,self.camera.y+ey,'alien_edge',7))
            if any(isinstance(e[0],str) and e[0]=='impact' for e in effects):
                outline=impact_ring()
                self._dynamic.append(self._sprite(outline,self.camera.x+ex-1,self.camera.y+ey-1,'alien_edge_hit',8))
        for i,p in enumerate(self.people):
            pos=positions.get(i,p['pos']) if positions else p['pos']
            if p.get('hostile') and not p['infected']:
                face=hostile_face(p['dir'],p['windup'],p['exposure'])
            elif p['doctor'] and not p['infected']:
                face=doctor_face(p['dir'],p['exposure'],bool(p.get('build_target') or p.get('heal_target') is not None))
            else:
                face=human_face(p['dir'],p['infected'],self.control==i,p['exposure'],i)
                if p.get('cough'):
                    face[0][0]=face[0][5]=14
            self._put(face,pos,f'person_{i}',4)
            if self.control==i and self.level_index>0:
                x,y=pos
                spore=[[6 if j<self.supply else 3,-1] for j in range(3)]
                self._dynamic.append(self._sprite(spore,self.ox+round(x*CELL)-2,self.oy+round(y*CELL),f'spores_{i}',5))
        for i,pos in enumerate(effects):
            if isinstance(pos[0],str) and pos[0]=='impact':
                mark=impact_ring()
                x,y=pos[1]
                self._dynamic.append(self._sprite(mark,self.ox+round(x*CELL)-1,self.oy+round(y*CELL)-1,f'impact_{i}',6))
            elif isinstance(pos[0],str) and pos[0]=='refuse':
                mark=[[-1]*6 for _ in range(6)]
                mark[0][0]=mark[0][5]=mark[5][0]=mark[5][5]=8
                self._put(mark,pos[1],f'refused_{i}',5)
            elif isinstance(pos[0],str) and pos[0]=='wipe':
                width=pos[1]
                face=[[14]*width for _ in range(64)]
                if width<64:
                    for row in face: row[-1]=0
                self._dynamic.append(self._sprite(face,self.camera.x,self.camera.y,'level_wipe',20))
            else:
                self._put(droplet(),pos,f'droplet_{i}',5)
        if beam:
            (x0,y0),(x1,y1)=beam[:2]
            colour=beam[2] if len(beam)>2 else 10
            x0,y0=self.ox+x0*CELL+3, self.oy+y0*CELL+3
            x1,y1=self.ox+x1*CELL+3, self.oy+y1*CELL+3
            steps=max(abs(x1-x0),abs(y1-y0))
            for n in range(2,steps,3):
                x=x0+(x1-x0)*n//steps; y=y0+(y1-y0)*n//steps
                self._dynamic.append(self._sprite([[colour]],x,y,f'beam_{n}',5))

    def _occupied(self, pos, except_alien=False):
        return ((not except_alien and self.alien['pos']==pos) or
                any(p['pos']==pos for p in self.people))

    def _blocked(self,pos,except_alien=False):
        x,y=pos
        return not (0<=x<self.width and 0<=y<self.height) or pos in self.walls or pos in self.vents or pos in self.medical or self._occupied(pos,except_alien)

    def _snapshot(self):
        return (deepcopy(self.people), deepcopy(self.medical), self.control, deepcopy(self.alien), self.supply)

    def _draw_snapshot(self, snapshot, effects=(), beam=None, positions=None):
        current=(self.people,self.medical,self.control,self.alien,self.supply)
        self.people,self.medical,self.control,self.alien,self.supply=deepcopy(snapshot)
        self._follow(positions)
        self._draw(positions=positions,effects=effects,beam=beam)
        self.people,self.medical,self.control,self.alien,self.supply=current

    def _follow(self, positions=None):
        actor = self.alien if self.control is None else self.people[self.control]
        key = 'alien' if self.control is None else self.control
        x,y = positions.get(key, actor['pos']) if positions else actor['pos']
        self.camera.x = max(0,min(max(0,self.ox+self.width*CELL+1-64),round(self.ox+x*CELL+3-32)))
        self.camera.y = max(0,min(max(0,self.oy+self.height*CELL+1-64),round(self.oy+y*CELL+3-32)))

    def _spray(self, origin, heading, strength, chain=True):
        queue=[(origin, heading, strength, chain)]
        effects=[]
        while queue:
            prior=self._snapshot()
            wave=[]
            (x,y),(dx,dy),power,can_chain=queue.pop(0)
            side=(-dy,dx)
            touched_walls=set()
            for sideways in (-1,0,1):
                vx,vy=dx+side[0]*sideways,dy+side[1]*sideways
                previous=(x,y)
                for n in range(1,4):
                    pos=(x+vx*n,y+vy*n)
                    if not (0<=pos[0]<self.width and 0<=pos[1]<self.height): break
                    if vx and vy:
                        corners=((previous[0]+vx,previous[1]),(previous[0],previous[1]+vy))
                        if all(c in self.walls or c in self.medical for c in corners): break
                    if pos in self.walls: break
                    if pos in self.medical:
                        if power==3 and pos not in touched_walls:
                            self.medical[pos]-=1
                            touched_walls.add(pos)
                            if self.medical[pos]<=0: del self.medical[pos]
                        wave.append(pos);effects.append(pos);break
                    wave.append(pos);effects.append(pos)
                    hit=next((i for i,p in enumerate(self.people) if p['pos']==pos),None)
                    if hit is not None:
                        p=self.people[hit]
                        if not p['infected']:
                            p['exposure']=min(3,p['exposure']+power)
                            if p['exposure']>=3:
                                p['infected']=True
                                p['dir']=heading
                                self.supply=min(3,self.supply+1)
                                if self.control is None: self.control=hit
                                elif can_chain: queue.append((pos,heading,3,True))
                        break
                    previous=pos
            self._events.append((prior,wave,None))
            self._events.append((self._snapshot(),[],None))
        return effects

    def _alien_turn(self):
        if self.control is None: return []
        ax,ay=self.alien['pos']
        hx,hy=self.people[self.control]['pos']
        if self.tick % 2 and abs(ax-hx)+abs(ay-hy)<=3: return []
        tether=4
        available=[p for p in self.people if not p['infected']]
        if not available: return []
        available.sort(key=lambda p:(abs(p['pos'][0]-ax)+abs(p['pos'][1]-ay),p['pos'][1],p['pos'][0]))
        for target in available:
            if abs(ax-hx)+abs(ay-hy)>tether: break
            tx,ty=target['pos']
            if ax==tx or ay==ty:
                d=((tx>ax)-(tx<ax),(ty>ay)-(ty<ay))
                distance=abs(tx-ax)+abs(ty-ay)
                if distance<=3 and all((ax+d[0]*n,ay+d[1]*n) not in self.walls and (ax+d[0]*n,ay+d[1]*n) not in self.medical and not any(p['pos']==(ax+d[0]*n,ay+d[1]*n) for p in self.people) for n in range(1,distance)):
                    self.alien['dir']=d
                    return self._spray((ax,ay),d,1)
        targets={p['pos'] for p in available}
        if abs(ax-hx)+abs(ay-hy)>=tether:
            targets={(hx,hy)}
        blocked=self.walls | self.vents | set(self.medical) | {p['pos'] for p in self.people}
        start=(ax,ay)
        queue=deque([start]); first={start:None}; choice=None
        while queue and choice is None:
            cell=queue.popleft()
            if cell!=start and any((cell[0]+d[0],cell[1]+d[1]) in targets for d in DIRS.values()):
                choice=first[cell]; break
            for direction in DIRS.values():
                dest=(cell[0]+direction[0],cell[1]+direction[1])
                if (0<=dest[0]<self.width and 0<=dest[1]<self.height and
                        (abs(dest[0]-hx)+abs(dest[1]-hy)<=tether or abs(ax-hx)+abs(ay-hy)>=tether) and
                        dest not in blocked and dest not in first):
                    first[dest]=direction if cell==start else first[cell]
                    queue.append(dest)
        if choice:
            self.alien['pos']=(ax+choice[0],ay+choice[1])
            self.alien['dir']=choice
        return []

    def _infected_turn(self):
        if self.control is None or self.tick % 4: return
        pending=self.cough_pending
        if pending is not None:
            self.cough_pending=None
            p=self.people[pending]
            if p['infected'] and pending!=self.control:
                p['cough']=False
                self._spray(p['pos'],p['dir'],1,False)
            return
        cases=[(i,p) for i,p in enumerate(self.people) if p['infected'] and i!=self.control]
        targets=[p for p in self.people if not p['infected']]
        if not cases or not targets: return
        i,p=cases[(self.tick//4)%len(cases)]
        target=min(targets,key=lambda q:abs(q['pos'][0]-p['pos'][0])+abs(q['pos'][1]-p['pos'][1]))
        dx=target['pos'][0]-p['pos'][0];dy=target['pos'][1]-p['pos'][1]
        p['dir']=((1 if dx>0 else -1),0) if abs(dx)>=abs(dy) else (0,(1 if dy>0 else -1))
        p['cough']=True
        self.cough_pending=i
        self._events.append((self._snapshot(),[],None))

    def _hostile_turn(self):
        if self.level_index==0 or self.tick % 3: return
        ax,ay=self.alien['pos']
        for p in self.people:
            if not p.get('hostile') or p['infected']: continue
            x,y=p['pos']
            distance=abs(x-ax)+abs(y-ay)
            direction=((ax>x)-(ax<x),(ay>y)-(ay<y))
            line=(x==ax or y==ay) and 0<distance<=10
            if line:
                line=all((x+direction[0]*n,y+direction[1]*n) not in self.walls and
                         (x+direction[0]*n,y+direction[1]*n) not in self.medical and
                         not any(q is not p and q['pos']==(x+direction[0]*n,y+direction[1]*n) for q in self.people)
                         for n in range(1,distance))
            if line:
                if not p['windup']:
                    p['windup']=True
                    p['dir']=direction
                    self._events.append((self._snapshot(),[],(p['pos'],self.alien['pos'],8)))
                else:
                    before=self._snapshot()
                    self._events.extend([(before,[('impact',self.alien['pos'])],(p['pos'],self.alien['pos'],8))]*2)
                    p['windup']=False
                    self.alien['damage']+=1
                    self._events.append((self._snapshot(),[],None))
                    if self.alien['damage']>=26:
                        self._result_lost=True
                        return
                continue
            p['windup']=False
            directions=sorted(DIRS.values(),key=lambda d:abs(x+d[0]-ax)+abs(y+d[1]-ay))
            for dx,dy in directions:
                dest=(x+dx,y+dy)
                if not self._blocked(dest):
                    p['pos']=dest
                    p['dir']=(dx,dy)
                    break

    def _civilian_turn(self):
        if self.level_index==0: return
        for i,p in enumerate(self.people):
            if i==self.control or p.get('hostile') or p.get('doctor') or p.get('cough') or p.get('anchored'): continue
            if (self.tick+i*2)%8: continue
            axis=(1,0) if i%2 else (0,1)
            sign=p.get('walk_sign',1)
            x,y=p['pos']; dest=(x+axis[0]*sign,y+axis[1]*sign)
            if self._blocked(dest):
                sign=-sign
                dest=(x+axis[0]*sign,y+axis[1]*sign)
            p['walk_sign']=sign
            if not self._blocked(dest):
                p['pos']=dest
                p['dir']=(axis[0]*sign,axis[1]*sign)

    def _doctor_step_towards(self, doctor, goals):
        start=doctor['pos']; blocked=self.walls|self.vents|set(self.medical)|{self.alien['pos']}
        blocked|={p['pos'] for p in self.people if p is not doctor}
        queue=deque([start]); first={start:None}
        while queue:
            cell=queue.popleft()
            if any(abs(cell[0]-x)+abs(cell[1]-y)==1 for x,y in goals):
                return first[cell]
            for d in DIRS.values():
                nxt=(cell[0]+d[0],cell[1]+d[1])
                if (0<=nxt[0]<self.width and 0<=nxt[1]<self.height and
                        nxt not in blocked and nxt not in first):
                    first[nxt]=d if cell==start else first[cell]
                    queue.append(nxt)
        return None

    def _doctor_turn(self):
        if self.level_index==0 or self.tick%5: return
        spec=LEVELS_SPEC[self.level_index]
        for doctor in self.people:
            if not doctor.get('doctor') or doctor['infected']: continue
            x,y=doctor['pos']
            cases=[(i,p) for i,p in enumerate(self.people) if p['infected']]
            choices=[pos for pos in spec['build'] if pos not in self.walls and pos not in self.vents and
                     pos not in self.medical and not self._occupied(pos)]
            nearest=min(cases,key=lambda v:(abs(v[1]['pos'][0]-x)+abs(v[1]['pos'][1]-y),v[0])) if cases else None
            case_near=nearest and abs(nearest[1]['pos'][0]-x)+abs(nearest[1]['pos'][1]-y)<=3
            if nearest and (case_near or not choices):
                i,patient=nearest
                px,py=patient['pos']; dist=abs(px-x)+abs(py-y)
                doctor['build_target']=None
                if dist==1:
                    if doctor.get('heal_primed')!=i:
                        doctor['heal_primed']=i
                        doctor['heal_target']=i
                        self._events.append((self._snapshot(),[],(doctor['pos'],patient['pos'])))
                    else:
                        before=self._snapshot()
                        self._events.extend([(before,[],(doctor['pos'],patient['pos']))]*2)
                        patient['infected']=False;patient['exposure']=0;patient['cough']=False
                        if self.cough_pending==i:self.cough_pending=None
                        if self.control==i:self.control=None
                        doctor['heal_target']=None
                        doctor['heal_primed']=None
                        self._events.append((self._snapshot(),[],None))
                    continue
                doctor['heal_target']=i
                doctor['heal_primed']=None
                direction=self._doctor_step_towards(doctor,{patient['pos']})
                if direction:
                    doctor['pos']=(x+direction[0],y+direction[1]);doctor['dir']=direction
                continue
            doctor['heal_target']=None
            doctor['heal_primed']=None
            if not choices:
                doctor['build_target']=None
                continue
            ax,ay=self.alien['pos']
            target=doctor.get('build_target')
            if target not in choices:
                target=min(choices,key=lambda q:(abs(q[0]-ax)+abs(q[1]-ay)+abs(q[0]-x)+abs(q[1]-y), abs(q[0]-x)+abs(q[1]-y)))
            doctor['build_target']=target
            dist=abs(target[0]-x)+abs(target[1]-y)
            if dist==1:
                self.medical[target]=2
                doctor['build_target']=None
                self._events.append((self._snapshot(),[],(doctor['pos'],target)))
            else:
                direction=self._doctor_step_towards(doctor,{target})
                if direction:
                    doctor['pos']=(x+direction[0],y+direction[1]);doctor['dir']=direction

    def _switch_host(self, selected, origin):
        self.control = selected
        if self.cough_pending == selected:
            self.cough_pending = None
            self.people[selected]['cough'] = False
        self._events.append((self._snapshot(), [], (origin, self.people[selected]['pos'], 14)))

    def _host_beyond_grille(self, grille, direction):
        dx, dy = direction
        for distance in (1, 2):
            pos = (grille[0] + dx * distance, grille[1] + dy * distance)
            if not (0 <= pos[0] < self.width and 0 <= pos[1] < self.height):
                break
            if pos in self.walls or pos in self.medical or pos in self.vents:
                break
            person = next((i for i, p in enumerate(self.people) if p['pos'] == pos), None)
            if person is not None:
                return person if self.people[person]['infected'] else None
        return None

    def step(self):
        if self.action.id==GameAction.RESET:
            self.complete_action()
            return
        if self._phase:
            if self._frames:
                snapshot,effects,beam,positions=self._frames.pop(0)
                self._draw_snapshot(snapshot,effects,beam,positions)
                return
            self._phase=0
            self._draw()
            if self._result_lost:
                self.lose()
            elif self._result_won:
                self.next_level()
            self.complete_action()
            return
        action=self.action.id.value if hasattr(self.action.id,'value') else self.action.id
        if action not in (1,2,3,4,5,6):
            self.complete_action()
            return
        self.tick += 1
        self._events=[]
        start_alien=self.alien['pos']
        start_people=[p['pos'] for p in self.people]
        actor=self.alien if self.control is None else self.people[self.control]
        if action==6:
            available=[i for i,p in enumerate(self.people) if p['infected'] and
                       0<=self.ox+p['pos'][0]*CELL-self.camera.x<64 and
                       0<=self.oy+p['pos'][1]*CELL-self.camera.y<64]
            selected=None
            data=self.action.data or {}
            x=(data.get('x',-100)+self.camera.x-self.ox)//CELL
            y=(data.get('y',-100)+self.camera.y-self.oy)//CELL
            selected=next((i for i in available if self.people[i]['pos']==(x,y)),None)
            if selected is not None:
                if selected != self.control:
                    self._switch_host(selected, actor['pos'])
            else:
                self._events.append((self._snapshot(),[('refuse',actor['pos'])],None))
        elif action in DIRS:
            direction=DIRS[action]
            actor['dir']=direction
            x,y=actor['pos']
            pos=(x+direction[0],y+direction[1])
            if pos in self.vents and self.control is not None:
                selected = self._host_beyond_grille(pos, direction)
                if selected is not None:
                    self._switch_host(selected, actor['pos'])
                else:
                    self._events.append((self._snapshot(), [('refuse', pos)], None))
            elif not self._blocked(pos, actor is self.alien): actor['pos']=pos
        else:
            if self.control is None or self.supply>0:
                if self.control is not None and self.level_index>0:self.supply-=1
                self._spray(actor['pos'],actor['dir'],1 if self.control is None else 3)
            else:
                self._events.append((self._snapshot(),[('refuse',actor['pos'])],None))
        motion_snapshot=self._snapshot()
        if self.level_index>0:
            self._alien_turn()
            self._infected_turn()
            self._hostile_turn()
            self._civilian_turn()
            self._doctor_turn()
        target=LEVELS_SPEC[self.level_index].get('goal',len(self.people))
        self._result_won=not self._result_lost and sum(p['infected'] for p in self.people)>=target
        motion=[]
        ends=[p['pos'] for p in self.people]
        if start_alien!=self.alien['pos'] or start_people!=ends:
            for frame in (1,2):
                positions={}
                for key,old,new in [('alien',start_alien,self.alien['pos'])]+[(i,start_people[i],ends[i]) for i in range(len(ends))]:
                    if old!=new:
                        positions[key]=(tween(old[0]*CELL,new[0]*CELL,frame,3)/CELL,
                                        tween(old[1]*CELL,new[1]*CELL,frame,3)/CELL)
                motion.append((motion_snapshot,[],None,positions))
        self._frames=motion+[(snap,effects,beam,None) for snap,effects,beam in self._events]+[(self._snapshot(),[],None,None)]*2
        if self._result_won:
            self._frames.extend((self._snapshot(),[('wipe', width)],None,None)
                                for width in (8,16,24,32,40,48,56,64,64))
        self._phase=1
        snapshot,effects,beam,positions=self._frames.pop(0)
        self._draw_snapshot(snapshot,effects,beam,positions)
