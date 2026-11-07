# ARC-AGI-3 candidate task lt04 (Lock Target, redrawn).
# Author: Claude Sonnet 5.5 (art; rules by Team Turducken agents, under Mark Barney's direction)
# Date: 07-November-2026
# PURPOSE: lt04 redraws lt03 (aim late-landing rounds at a walking city of four districts over nine missions). The
#   RULES ARE UNCHANGED: every mission, layout, tool, counter, click area and ending is lt03's, copied as it was. Only the
#   picture is new: every thing on screen is a named sprite (people with faces, cars, ambulances, roofs, trees, props,
#   fires, blasts, a console), each mission is its own season with its own ground, roofs, trees and drifting life, and a
#   lost run, a won mission and every shot have drawn feedback. No letters, digits or words are drawn anywhere.
# SRP/DRY check: Pass -- the Lt04 class holds the rules (lt03's, untouched); everything under THE ART only draws from the
#   rule state and never writes to it.
# CHANGELOG
# 07-November-2026, Claude Sonnet 5.5: first version, the art of lt03 rebuilt as named sprites; rules untouched.
# 07-November-2026, Claude Sonnet 5.5: pass two, critique and redraw: six-by-eight people with real faces, hair styles, caps
#   and cheer or wince on win or loss; nine calmer seasons with their own street styles (boardwalk, plowed, licorice) and
#   junction squares; pitched shingled roofs and tidy rubble; tall ward landmarks and courtyard centrepieces; side-on
#   ambulance with a flashing bar; polished cars; tall dancing flames; layered fireball with rays, debris and smoke;
#   better bomb icon and top-bar faces; a starburst on a win and a lighter red haze on a loss.
# 07-November-2026, Claude Sonnet 5.5: pass three, variety and life: a tree of its own kind in every season, two-frame small
#   props and ground scatter that nod, flicker and twinkle; thin three-wide landmarks used wherever the real gap is only
#   three pixels (wide ones only where five are free), so none lies over a street; a second roof colour and a seasonal
#   roof dressing (snow caps, frosting, bunting, leaves, awnings, solar panels, moonlit skylights); little animals living
#   in the spare corners of every season; cars redrawn with the body colour doing the work; a pixel of air between the
#   top-bar faces when they fit; confetti and five fireworks on a win; a storm cloud, rain and lightning on a loss.
# 07-November-2026, Claude Sonnet 5.5: pass four, final polish: the night city's roofs get a blue outline (black vanished on
#   the black ground); fewer ground specks so roofs and people read first; an unused leftover removed. Rules untouched.

from __future__ import annotations
from copy import deepcopy
from collections import deque
import numpy as np
from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite


def block(colour: int, cell: int = 4) -> list[list[int]]:
    return [[colour] * cell for _ in range(cell)]

def ring(colour: int, cell: int = 4) -> list[list[int]]:
    px = block(colour, cell)
    for y in range(1, cell - 1):
        for x in range(1, cell - 1):
            px[y][x] = -1
    return px

def pixel_art(rows: tuple, colours: dict) -> list[list[int]]:
    return [[-1 if ch == "." else colours[ch] for ch in row] for row in rows]


TOOLS = {
    'heavy': {'delay': 4, 'radius': 5, 'stock': 3},
    'precision': {'delay': 1, 'radius': 1, 'stock': 6},
    'fire': {'delay': 2, 'radius': 2, 'stock': 2},
    'aid': {'delay': 2, 'radius': 7, 'stock': 2},
    'beacon': {'delay': 1, 'radius': 18, 'stock': 2},
}
TOOL_ORDER = ('heavy', 'precision', 'fire', 'aid', 'beacon')
FRAME_COUNT = 6
WORLD_WIDTH, WORLD_HEIGHT = 128, 104
PRACTICE_RECHARGE = 6
RECHARGE_TURNS = 7
AID_SLOW_TURNS = 12
FREEZE_RADIUS = 7
FREEZE_TURNS = 6
MISSION_TARGETS = (2,4,4,5,5,6,7,8,9)
PAN_STEP = 8
PAN = {1:(0,-PAN_STEP), 2:(0,PAN_STEP), 3:(-PAN_STEP,0), 4:(PAN_STEP,0)}


def line_route(points):
    result = [tuple(points[0])]
    for end in points[1:]:
        x, y = result[-1]
        while (x, y) != tuple(end):
            if x != end[0]: x += max(-2, min(2, end[0] - x))
            else: y += max(-2, min(2, end[1] - y))
            result.append((x, y))
    return result


def actor(name, role, route, confidence=4, priority=False, accent=10):
    return dict(id=name, role=role, route=route, index=0, pos=route[0],
                observed=route[0], confidence=confidence, priority=priority,
                alive=True, indoors=None, injured=False, accent=accent,
                rush=0, assignment=None, assisted=False, observed_at=0,
                returning=False, assist_ticks=0, evacuating=False, home=route[0],
                traffic=False, vehicle=False, riding=None, onboard=None,
                gather_until=0, crowd_target=None, ride_target=None, occupants=[])


def build_district(index):
    buildings = []
    for row in range(3):
        for col in range(3):
            kind = ('hospital', 'station', 'school')[col] if row == 2 else 'home'
            if row == 0 and col == 1: kind = 'depot'
            w = 10 + 2 * ((index + col + row) % 2)
            h = 7 + ((index + row) % 2)
            x, y = 8 + col * 18, 10 + row * 14
            buildings.append(dict(id=f'b{row}{col}', kind=kind, rect=(x,y,w,h),
                                  door=(x+4, y), integrity=3))
    roads = [(2,y,60,3) for y in (7,21,35,49)] + [(x,4,3,48) for x in (5,23,41,59)]
    actors = []
    lesson_routes = [line_route([(5,7),(13,7),(5,7)]),
                     line_route([(29,7),(35,7),(29,7)]),
                     line_route([(53,21),(59,21),(53,21)]),
                     line_route([(27,35),(35,35),(27,35)])]
    counts = (1,4,5,7,9,11,14,18)
    for i in range(counts[index]):
        if index <= 1:
            route = lesson_routes[i]
        else:
            zone = i % 6
            col, row = zone % 3, zone // 3
            x, y = 5 + col*18, 7 + row*14
            offset = (i // 6) * 3
            b = buildings[row*3+col]
            doorx, doory = b['door']
            if index >= 3 and i % 3 == 1:
                route = line_route([(x,y),(doorx,y),(doorx,doory+3),
                                    (doorx,doory+3),(doorx,y),(x,y)])
            else:
                route = line_route([(x,y),(x+10,y),(x,y)])
            route = route[offset:] + route[:offset]
        confidence = 4 if index < 2 or i % 3 == 0 else (i % 3)
        actors.append(actor(f'h{i}', 'hostile', route, confidence, index>=2 and i==1))
    for b in buildings:
        if b['kind'] in ('hospital','school'):
            x,y,w,h=b['rect']
            for k in range(3 if index<3 else 4):
                a=actor(f'{b["id"]}_c{k}','civilian',[(x+2+(k%2)*4,y+2+(k//2)*3)])
                a['indoors']=b['id']; actors.append(a)
    if index:
        for i in range(2+index):
            col=i%3; x=5+col*18
            route=line_route([(x,35),(x,49),(min(59,x+8),49),(x,49),(x,35)])
            route=route[(i*3)%len(route):]+route[:(i*3)%len(route)]
            actors.append(actor(f'c{i}','civilian',route, 1 if index>=2 and i==0 else 4))
    if index >= 4:
        for i, accent in enumerate((10,15,11)):
            actors.append(actor(f'r{i}','responder',[(27+i*4,49)],4,False,accent))
    x_lines=((5,23,41,59),(5,23,41,59),(5,21,43,59),(5,25,41,59),
             (5,21,39,59),(5,25,43,59),(5,23,43,59),(5,21,41,59))[index]
    y_lines=((7,21,35,49),(7,21,35,49),(7,19,35,49),(7,23,35,49),
             (7,21,37,49),(7,19,33,49),(7,23,37,49),(7,21,33,49))[index]
    def warp(value, old, new):
        for a,b,c,d in zip(old,old[1:],new,new[1:]):
            if a<=value<=b: return round(c+(value-a)*(d-c)/(b-a))
        return value
    def point(p):
        return (warp(p[0],(0,5,23,41,59,64),(0,*x_lines,64)),
                warp(p[1],(0,7,21,35,49,64),(0,*y_lines,64)))
    def rect(r):
        x,y=point(r[:2]); xx,yy=point((r[0]+r[2],r[1]+r[3]))
        return (x,y,max(1,xx-x),max(1,yy-y))
    roads=[rect(r) for r in roads]
    for b in buildings:
        b['rect']=rect(b['rect']);b['door']=point(b['door'])
    for a in actors:
        a['route']=[point(p) for p in a['route']]
        a['pos']=a['observed']=a['home']=a['route'][0]
    if index>=2:
        buildings[(0,2,3,5,0,2)[index-2]]['kind']='courtyard'
    return dict(buildings=buildings,roads=roads,actors=actors,
                sensor_period=3 if index>=6 else 1)


def offset_actor(original, offset, prefix):
    a=deepcopy(original);dx,dy=offset
    a['id']=prefix+a['id']
    for key in ('pos','observed','home'): a[key]=(a[key][0]+dx,a[key][1]+dy)
    a['route']=[(x+dx,y+dy) for x,y in a['route']]
    if a['indoors']: a['indoors']=prefix+a['indoors']
    return a


def build_city():
    buildings=[];roads=[];actors=[]
    for ward in range(4):
        dx,dy=(ward%2)*64,(ward//2)*52;prefix=f'w{ward}_'
        spec=build_district((0,3,5,7)[ward])
        for b in spec['buildings']:
            b=deepcopy(b);b['id']=prefix+b['id']
            x,y,w,h=b['rect'];b['rect']=(x+dx,y+dy,w,h)
            b['door']=(b['door'][0]+dx,b['door'][1]+dy);buildings.append(b)
        roads.extend((x+dx,y+dy,w,h) for x,y,w,h in spec['roads'])
        actors.extend(offset_actor(a,(dx,dy),prefix) for a in spec['actors'] if a['role']!='hostile')
        for n in range(5):
            x,y=((23,7),(41,21),(59,35),(5,49),(41,49))[n]
            a=actor(f'traffic{n}','civilian',line_route([(x,y),(min(59,x+8),y),(x,y)]))
            a['traffic']=True;a['vehicle']=n%2==0;a['accent']=(11,10,15,6,9)[n]
            actors.append(offset_actor(a,(dx,dy),prefix))
        if not any(a['role']=='responder' for a in spec['actors']):
            actors.append(offset_actor(actor('r0','responder',[(31,49)]),(dx,dy),prefix))
    roads.extend((60,y,8,3) for y in (7,21,35,49,59,73,87,101))
    roads.extend((x,48,3,12) for x in (5,23,41,59,69,87,105,123))
    rooms={b['id']:b for b in buildings}
    occupants={}
    for a in actors:
        if a['role']=='civilian' and not a['indoors']:a['traffic']=True
        elif a['role']=='civilian' and a['indoors'] in rooms:
            b=rooms[a['indoors']];x,y,w,h=b['rect']
            route=line_route([(x+2,y+2),(x+w-4,y+2),(x+w-4,y+h-3),(x+2,y+h-3),(x+2,y+2)])
            phase=occupants.get(b['id'],0)*2;occupants[b['id']]=occupants.get(b['id'],0)+1
            phase%=len(route);a['route']=route[phase:]+route[:phase]
            a['pos']=a['observed']=a['home']=a['route'][0]
    return buildings,roads,actors


MISSION_WARDS=(0,1,3,2,0,1,3,2,0)
MISSION_VIEWS=((0,0),(32,24),(64,52),(0,24),(48,0),(24,52),(64,16),(0,52),(32,26))
ZONE_LAYOUTS=((0,1,2,3,4,5),(4,2,0,5,1,3),(5,1,3,0,4,2),
              (2,4,1,5,0,3),(1,5,3,2,4,0),(3,2,4,0,5,1),
              (4,0,5,1,3,2),(2,5,1,3,0,4),(5,3,1,4,2,0))
SNAPSHOT_FIELDS=('buildings','roads','actors','craters','tools','tool_index','ammo','reload_progress',
    'sensor_period','tick','risk','total_hostiles','pending','fires','beacons',
    'events','incidents','ledger','stale','flash_tool','ending','before_actors',
    'view_x','view_y','before_view','mission_index','blocked_cells','response_load','slow_until',
    'sheltered_actors')


class Lt04(ARCBaseGame):
    def __init__(self):
        self._mission_number=None;self._mission_entry=None
        self.world_width=WORLD_WIDTH;self.world_height=WORLD_HEIGHT
        super().__init__(game_id="lt04", levels=[Level(sprites=[],grid_size=(64,64),
            data={'mission':i}) for i in range(9)],
            camera=Camera(width=64,height=64,background=5,letter_box=5),
            available_actions=[1,2,3,4,5,6,7],win_score=9)

    def on_set_level(self, level):
        index=level.get_data('mission')
        retry=self._mission_number==index and self._mission_entry is not None
        if retry:
            for name,value in deepcopy(self._mission_entry).items():setattr(self,name,value)
        else:
            continuing=self._mission_number is not None and index==self._mission_number+1
            if not continuing:
                self.buildings,self.roads,self.actors=build_city()
                self.craters={};self.view_x=0;self.view_y=0
                self.sheltered_actors=[]
            else:
                buildings={b['id']:b for b in self.buildings}
                for a in self.sheltered_actors:
                    b=buildings.get(a.get('indoors'))
                    if b and b['integrity']<=0:
                        a['indoors']=None;a['pos']=a['observed']=a['home']=b['door']
                        a['route']=[a['pos']];a['index']=0
                    self.actors.append(a)
                self.sheltered_actors=[]
            self.actors=[a for a in self.actors if a['role']!='hostile']
            survivors={a['id'] for a in self.actors}
            for a in self.actors:
                a['ride_target']=None
                a['occupants']=[key for key in a.get('occupants',[]) if key in survivors]
            self.response_load=0
            ward=MISSION_WARDS[index];offset=((ward%2)*64,(ward//2)*52)
            spec=build_district(min(max(index,1),7))
            enemies=[a for a in spec['actors'] if a['role']=='hostile'][:MISSION_TARGETS[index]]
            if index==0:
                enemies=[actor('h0','hostile',line_route([(29,21),(37,21),(29,21)])),
                         actor('h1','hostile',line_route([(43,35),(51,35),(43,35)]))]
            for number,a in enumerate(enemies):
                target_ward=(ward+1)%4 if 1<=index<8 and number==1 else (ward if index<8 else number%4)
                shift=((target_ward%2)*64,(target_ward//2)*52)
                ward_spec=build_district((0,3,5,7)[target_ward])
                if index>0:
                    zone=ZONE_LAYOUTS[index][number%6];col,row=zone%3,zone//3
                    building=ward_spec['buildings'][row*3+col]
                    bx,by=building['door'];y=by-3;x=building['rect'][0]-3
                    points=[(x,y),(bx+2,y),(x,y)]
                    if index>=3 and number%3==1:
                        points=[(x,y),(bx,y),(bx,by+3),(bx,y),(x,y)]
                    route=line_route(points);phase=(number//6)*3
                    a=actor(f'h{number}','hostile',route[phase:]+route[:phase],
                            4 if number==0 else number%3,index>=2 and number==1)
                if index<4:a['confidence']=4
                a.update(threat_age=0,threat_limit=100+index*12+number*14,attack_stage='quiet')
                self.actors.append(offset_actor(a,shift,f'm{index}_'))
            if index<4:
                patrols=[p for a in self.actors if a['role']=='hostile' for p in a['route']]
                for a in list(self.actors):
                    if a['role']=='hostile':continue
                    if any(self._near(p,q,13) for p in a['route'] for q in patrols):
                        self.actors.remove(a);self.sheltered_actors.append(a)
            if index>=4:
                riders=[a for a in self.actors if a['role']=='hostile' and int(a['id'].split('h')[-1])%3==0]
                for a in riders[:1+index//4]:
                    car=actor(a['id']+'_car','civilian',list(a['route']))
                    car.update(vehicle=True,traffic=index%2==0,accent=10,ride_target=a['id'])
                    people=[car]
                    for seat in range(2):
                        passenger=actor(car['id']+f'_p{seat}','civilian',[car['pos']])
                        passenger.update(traffic=car['traffic'],onboard=car['id'])
                        people.append(passenger)
                    car['occupants']=[c['id'] for c in people]
                    self.actors.extend(people)
            unlocked={'heavy','precision','fire'}
            if index>=2:unlocked.add('beacon')
            if index>=3:unlocked.add('aid')
            self.tools=[t for t in TOOL_ORDER if t in unlocked];self.tool_index=0
            self.view_x,self.view_y=MISSION_VIEWS[index]
            self.ammo={name:TOOLS[name]['stock'] for name in TOOL_ORDER}
            self.reload_progress={name:0 for name in TOOL_ORDER}
            self.sensor_period=spec['sensor_period'];self.tick=0;self.risk=120
            self.total_hostiles=self.remaining_hostiles()
            self.pending=[];self.fires=[];self.beacons=[];self.events=[];self.incidents=[]
            self.slow_until=0
            self.ledger=dict(hostiles=0,priority=0,civilian_losses=0,responder_losses=0,
                            building_damage=0,unconfirmed=0,aided=0,shots=0,
                            enemy_attacks=0,enemy_civilian_losses=0)
            self.stale=False;self.flash_tool=None;self.ending=None;self.before_actors={}
            if index>=5:
                hospitals=[b for b in self.buildings if b['kind']=='hospital' and b['integrity']>0]
                if hospitals:
                    b=min(hospitals,key=lambda b:abs(b['rect'][0]-offset[0])+abs(b['rect'][1]-offset[1]))
                    x,y,w,h=b['rect'];pos=(x+4,y+3)
                    self.incidents=[dict(pos=pos,deadline=180,resolved=False)]
                    self.fires=[dict(pos=pos,radius=2,left=180,incident=True,charged=set())]
                    patient=next((a for a in self.actors if a['alive'] and a['indoors']==b['id']),None)
                    if patient:patient['injured']=True
            self.before_view=(self.view_x,self.view_y);self.mission_index=index
            self._rebuild_collision()
            self._mission_entry=deepcopy({name:getattr(self,name) for name in SNAPSHOT_FIELDS})
        self._mission_number=index;self.animating=False;self.frame_index=0
        self.outro_phase=-1;self.intro_frames=2 if not retry and continuing and self._next_level else 0
        self.transition_phase=3 if self.intro_frames else -1
        self.camera.resize(64,64);self.camera.x=self.view_x;self.camera.y=self.view_y
        art_init(self);art_frame(self,FRAME_COUNT-1,FRAME_COUNT)
        if self.intro_frames:art_transition(self,3)

    def _rebuild_collision(self):
        self.blocked_cells=set()
        for b in self.buildings:
            if b['kind']=='courtyard' or b['integrity']<=0:continue
            x,y,w,h=b['rect']
            self.blocked_cells.update((xx,yy) for xx in range(x,x+w) for yy in range(y,y+h))

    def _paint_frame(self):
        fraction=(self.frame_index+1)/FRAME_COUNT
        self.camera.x=round(self.before_view[0]+(self.view_x-self.before_view[0])*fraction)
        self.camera.y=round(self.before_view[1]+(self.view_y-self.before_view[1])*fraction)
        art_frame(self,self.frame_index,FRAME_COUNT)

    def remaining_hostiles(self):
        return sum(a['alive'] and a['role']=='hostile' for a in self.actors)

    def _building_at(self, pos):
        x,y=pos
        for b in self.buildings:
            bx,by,w,h=b['rect']
            if b['kind']!='courtyard' and b['integrity']>0 and bx<=x<bx+w and by<=y<by+h: return b
        return None

    def _walkable(self,pos):
        x,y=pos
        if not (2<=x<=self.world_width-4 and 4<=y<=self.world_height-2): return False
        return not any((x+dx,y+dy) in self.blocked_cells for dx in (0,1) for dy in (0,1))

    def _street_path(self,start,end):
        start=tuple(start)
        if not self._walkable(start): return [start]
        queue=deque([start]); parent={start:None}; best=start
        while queue:
            p=queue.popleft()
            if abs(p[0]-end[0])+abs(p[1]-end[1]) < abs(best[0]-end[0])+abs(best[1]-end[1]): best=p
            if max(abs(p[0]-end[0]),abs(p[1]-end[1]))<=2: best=p;break
            for dx,dy in ((2,0),(-2,0),(0,2),(0,-2)):
                q=(p[0]+dx,p[1]+dy)
                if q not in parent and self._walkable(q): parent[q]=p;queue.append(q)
        result=[]
        while best is not None: result.append(best);best=parent[best]
        return result[::-1]

    def _frozen(self, a):
        return a['role']=='hostile' and any(
            self.tick < b['freeze_until'] and self._near(a['pos'], b['pos'], FREEZE_RADIUS)
            for b in self.beacons)

    def _move(self):
        for a in self.actors:
            if not a['alive'] or a['injured'] or a.get('onboard') or a.get('ride_target'): continue
            a['motion_path']=[]
            if self._frozen(a): continue
            if a['role']=='responder':
                if a['assignment']:
                    path=a['route']
                    a['index']=min(a['index']+1,len(path)-1);a['pos']=path[a['index']];a['motion_path']=[a['pos']]
                    if a['index']==len(path)-1:
                        if a['returning']:
                            a['assignment']=None;a['returning']=False;a['assist_ticks']=0
                        else:
                            a['assisted']=True;a['assist_ticks']+=1
                            for c in self.actors:
                                if c['alive'] and c['injured'] and self._near(c['pos'],a['pos'],5):
                                    c['injured']=False;self.ledger['aided']+=1
                            if a['assist_ticks']>=10+self.response_load*3:
                                a['returning']=True;a['route']=self._street_path(a['pos'],a['home']);a['index']=0
                continue
            if a.get('gather_until') and self.tick>=a['gather_until']:
                a['gather_until']=0;a['crowd_target']=None;a['evacuating']=False
                a['route']=self._street_path(a['pos'],a['home']);a['index']=0
            riding=a.get('riding')
            advances=2 if a['rush'] or riding or (a['role']=='hostile' and self.tick%7==0) else 1
            a['rush']=max(0,a['rush']-1)
            a['motion_path']=[]
            for _ in range(advances):
                a['index']=min(a['index']+1,len(a['route'])-1) if a.get('evacuating') else (a['index']+1)%len(a['route'])
                a['pos']=a['route'][a['index']];a['motion_path'].append(a['pos'])
            b=self._building_at(a['pos'])
            a['indoors']=b['id'] if b else None

        lookup={a['id']:a for a in self.actors}
        for car in self.actors:
            if not car['alive'] or not car.get('ride_target'):continue
            target=lookup.get(car['ride_target'])
            if not target or not target['alive']:
                car['ride_target']=None;continue
            count=len(target['route']);start=2;end=max(start+1,count-3)
            aboard=start<=target['index']<=end
            target['riding']=car['id'] if aboard else None
            before=car['pos']
            car['pos']=target['pos'] if aboard else (min(self.world_width-7,target['pos'][0]+12),target['pos'][1])
            car['motion_path']=line_route([before,car['pos']])[1:]
            car['occupants']=[car['id']]+[a['id'] for a in self.actors if a.get('onboard')==car['id'] and a['alive']]
            if aboard:car['occupants'].append(target['id'])
        for a in self.actors:
            if a['alive'] and a.get('onboard') in lookup:
                car=lookup[a['onboard']];a['pos']=car['pos'];a['motion_path']=car.get('motion_path',[])

    def _hit_actor(self,actor,pos,radius):
        if actor.get('vehicle') or actor['role']=='responder':
            x,y=actor['pos'];cx,cy=pos
            return not (x+5<cx-radius or x-3>cx+radius or y+5<cy-radius or y-2>cy+radius)
        return self._near(actor['pos'],pos,radius)

    @staticmethod
    def _near(point,center,radius):
        return not (point[0]+1<center[0]-radius or point[0]>center[0]+radius or
                    point[1]+1<center[1]-radius or point[1]>center[1]+radius)

    def _impact(self,pos,radius,tool,charged=None):
        self.craters[tuple(pos)]=max(radius,self.craters.get(tuple(pos),0))
        charged=set() if charged is None else charged
        hit_cars={a['id'] for a in self.actors if a['alive'] and a.get('vehicle') and self._hit_actor(a,pos,radius)}
        for a in self.actors:
            shared=a.get('onboard') in hit_cars or a.get('riding') in hit_cars
            if not a['alive'] or not (shared or self._hit_actor(a,pos,radius)): continue
            if a['role']=='hostile':
                if tool!='enemy':
                    self.ledger['hostiles']+=1
                    self.ledger['priority']+=int(a['priority'])
                if tool!='enemy' and a['confidence']<4:
                    self.ledger['unconfirmed']+=1;self.risk-=5
            else:
                key='responder_losses' if a['role']=='responder' else 'civilian_losses'
                self.ledger[key]+=1;self.risk-=18 if a['role']=='responder' else 14
            a['alive']=False
        for b in self.buildings:
            if b['kind']=='courtyard' or b['integrity']<=0 or b['id'] in charged: continue
            x,y,w,h=b['rect']
            if x>pos[0]+radius or x+w-1<pos[0]-radius or y>pos[1]+radius or y+h-1<pos[1]-radius: continue
            charged.add(b['id']);b['integrity']=max(0,b['integrity']-(2 if tool=='heavy' else 1))
            self.ledger['building_damage']+=1
            self.risk-=18 if b['kind'] in ('hospital','school') else 3
        self._rebuild_collision()
        self.risk=max(0,self.risk)
        self.beacons=[b for b in self.beacons if not self._near(b['pos'],pos,radius)]

    def _respond(self,pos):
        if self.mission_index<3:return
        self.response_load=min(18,self.response_load+1)
        pressure=self.response_load
        ordered=sorted((a for a in self.actors if a['alive']),
                       key=lambda a:abs(a['pos'][0]-pos[0])+abs(a['pos'][1]-pos[1]))
        ambulances=[a for a in ordered if a['role']=='responder' and not a['assignment']]
        for a in ambulances[:1+pressure//3]:
            a['assignment']=pos;a['route']=self._street_path(a['pos'],pos);a['index']=0
            a['returning']=False;a['assist_ticks']=0
        crowd=[a for a in ordered if a['role']=='civilian' and a.get('traffic')
               and not a.get('onboard') and not a.get('ride_target') and not a['indoors']
               and self._near(a['pos'],pos,24+pressure*2)]
        for n,a in enumerate(crowd[:2+pressure*2]):
            approach=(pos[0]+(n%3-1)*2,pos[1]+(n//3%3-1)*2)
            a['route']=self._street_path(a['pos'],approach);a['index']=0
            a['evacuating']=True;a['gather_until']=self.tick+18+pressure*4;a['rush']=3
        for a in ordered:
            if a['role']=='hostile' and not a['indoors'] and self._near(a['pos'],pos,12):a['rush']=3

    def _resolve(self,shot):
        pos=shot['pos'];tool=shot['tool'];radius=TOOLS[tool]['radius']
        self.events.append(dict(kind=tool,pos=pos,radius=radius))
        if tool=='aid':
            self.slow_until=max(self.slow_until,self.tick+AID_SLOW_TURNS+1)
            self.fires=[f for f in self.fires if not self._near(f['pos'],pos,radius)]
            for incident in self.incidents:
                if self._near(incident['pos'],pos,radius) and not incident['resolved']:
                    incident['resolved']=True;self.ledger['aided']+=1
            for a in self.actors:
                if (a['alive'] and a['role']=='civilian' and a.get('traffic')
                    and not a.get('onboard') and not a.get('ride_target')
                    and not a['indoors'] and self._near(a['pos'],pos,20)):
                    a['route']=self._street_path(a['pos'],pos);a['index']=0
                    a['evacuating']=True;a['crowd_target']=None
                    a['gather_until']=self.tick+12;self.ledger['aided']+=1
                if a['alive'] and a['injured'] and self._near(a['pos'],pos,radius):
                    a['injured']=False;self.ledger['aided']+=1
        elif tool=='beacon':
            self.beacons.append(dict(pos=pos,until=self.tick+9,freeze_until=self.tick+FREEZE_TURNS+1))
        else:
            self._impact(pos,radius,tool)
            if tool in ('heavy','fire'):self._respond(pos)
            if tool=='fire': self.fires.append(dict(pos=pos,radius=radius,left=4,incident=False,charged=set()))

    def _observe(self):
        self.stale=self.sensor_period>1 and self.tick%self.sensor_period!=0
        for a in self.actors:
            if not a['alive']: continue
            illuminated=any(self._near(a['pos'],b['pos'],TOOLS['beacon']['radius']) for b in self.beacons)
            refresh=not self.stale or illuminated
            if refresh:
                a['observed']=a['pos'];a['observed_at']=self.tick
                if illuminated and not a['indoors']: a['confidence']=4
                elif a['indoors'] and a['role']=='hostile': a['confidence']=min(3,a['confidence'])
                elif a['role']=='hostile' and a['confidence']<4 and self.tick%18==0 and not a['indoors']: a['confidence']+=1

    def _threats(self):
        if self.mission_index<3:return
        for target in self.actors:
            if target['role']!='hostile' or not target['alive'] or self._frozen(target):continue
            target['threat_age']+=1
            age,limit=target['threat_age'],target['threat_limit']
            target['attack_stage']='arming' if age>=limit*4//5 else 'gather' if age>=limit//2 else 'quiet'
            if target['attack_stage']!='quiet' and (age==limit//2 or age%12==0):
                crowd=sorted((a for a in self.actors if a['alive'] and a.get('traffic')
                    and not a.get('onboard') and not a.get('ride_target') and not a['indoors']
                    and a.get('crowd_target') in (None,target['id'])
                    and self._near(a['pos'],target['pos'],36)),
                    key=lambda a:abs(a['pos'][0]-target['pos'][0])+abs(a['pos'][1]-target['pos'][1]))
                count=3 if target['attack_stage']=='gather' else 7
                for n,a in enumerate(crowd[:count]):
                    point=(target['pos'][0]+(n%3-1)*2,target['pos'][1]+(n//3%3-1)*2)
                    a['route']=self._street_path(a['pos'],point);a['index']=0
                    a['evacuating']=True;a['crowd_target']=target['id']
                    a['gather_until']=self.tick+limit-age+20
            if age>=limit:
                before=self.ledger['civilian_losses']+self.ledger['responder_losses']
                self.events.append(dict(kind='fire',pos=target['pos'],radius=8))
                self._impact(target['pos'],8,'enemy')
                after=self.ledger['civilian_losses']+self.ledger['responder_losses']
                self.ledger['enemy_attacks']+=1;self.ledger['enemy_civilian_losses']+=after-before
                self.fires.append(dict(pos=target['pos'],radius=5,left=4,incident=False,charged=set()))
                self.risk=max(0,self.risk-45)

    def _world_tick(self,action,data):
        self.before_actors={a['id']:deepcopy(a) for a in self.actors}
        self.before_view=(self.view_x,self.view_y)
        self.events=[];self.flash_tool=None;self.tick+=1
        if action in PAN:
            dx,dy=PAN[action]
            self.view_x=max(0,min(self.world_width-64,self.view_x+dx))
            self.view_y=max(0,min(self.world_height-52,self.view_y+dy))
        elif action==5:
            self.tool_index=(self.tool_index+1)%len(self.tools)
            self.events.append(dict(kind='switch',pos=(0,0),radius=0))
        elif action==6:
            x,y=data.get('x',-1),data.get('y',-1)
            if isinstance(x,(int,np.integer)) and isinstance(y,(int,np.integer)):
                if 53<=y<=63:
                    i=int(x)//12
                    if 0<=i<len(TOOL_ORDER):
                        if TOOL_ORDER[i] in self.tools:
                            self.tool_index=self.tools.index(TOOL_ORDER[i])
                            self.events.append(dict(kind='switch',pos=(0,0),radius=0))
                        else:self.flash_tool=TOOL_ORDER[i]
                elif 2<=x<=61 and 4<=y<=51:
                    x,y=x+self.view_x,y+self.view_y
                    tool=self.tools[self.tool_index]
                    if self.ammo[tool]>0:
                        self.ammo[tool]-=1;self.ledger['shots']+=1
                        self.pending.append(dict(pos=(int(x),int(y)),tool=tool,
                                                 due=self.tick+TOOLS[tool]['delay']))
                    else:
                        self.events.append(dict(kind='refuse',pos=(int(x),int(y)),radius=2))
                        self.flash_tool=tool
        slowed=self.tick<self.slow_until and (self.slow_until-self.tick)%2==0
        if not slowed:
            self._move()
        else:
            for a in self.actors: a['motion_path']=[]
            for incident in self.incidents:
                if not incident['resolved']: incident['deadline']+=1
        for fire in self.fires:
            if slowed: continue
            fire['left']-=1
            if fire['incident']: continue
            fire['radius']=min(5,fire['radius']+1)
            self._impact(fire['pos'],fire['radius'],'fire',fire['charged'])
        self.fires=[f for f in self.fires if f['left']>0]
        due=[p for p in self.pending if p['due']<=self.tick]
        self.pending=[p for p in self.pending if p['due']>self.tick]
        for shot in due: self._resolve(shot)
        for incident in self.incidents:
            if not incident['resolved'] and self.tick>=incident['deadline']:
                self._impact(incident['pos'],5,'fire');incident['resolved']=True
        self.beacons=[b for b in self.beacons if b['until']>self.tick]
        if not slowed: self._threats()
        self._observe()
        recharge = PRACTICE_RECHARGE if self.mission_index==0 else RECHARGE_TURNS
        for tool in self.tools:
            if self.ammo[tool] < TOOLS[tool]['stock']:
                self.reload_progress[tool] += 1
                if self.reload_progress[tool] >= recharge:
                    self.ammo[tool] += 1
                    self.reload_progress[tool] = 0
            else:
                self.reload_progress[tool] = 0
        unresolved=any(not i['resolved'] for i in self.incidents)
        if self.mission_index>=3 and self.risk<=0:self.ending='lose'
        elif not self.remaining_hostiles() and not self.pending and not self.fires and not unresolved: self.ending='win'

    def step(self):
        if self.action.id==GameAction.RESET:
            self.complete_action();return
        if self.intro_frames:
            self.intro_frames-=1;art_frame(self,FRAME_COUNT-1,FRAME_COUNT)
            if self.intro_frames:art_transition(self,4)
            else:self.complete_action()
            return
        if self.outro_phase>=0:
            self.outro_phase+=1;art_frame(self,FRAME_COUNT-1,FRAME_COUNT)
            art_transition(self,self.outro_phase)
            if self.outro_phase>=2:
                last=self.is_last_level();self.next_level()
                if last:self.complete_action()
            return
        if self.animating:
            self.frame_index+=1;self._paint_frame()
            if self.frame_index>=FRAME_COUNT-1:
                self.animating=False
                if self.ending=='lose':self.lose();self.complete_action()
                elif self.ending=='win':
                    self.outro_phase=0;art_transition(self,0)
                else:self.complete_action()
            return
        action=self.action.id.value
        if action not in (1,2,3,4,5,6,7):self.complete_action();return
        self._world_tick(action,self.action.data or {})
        self.frame_index=0;self.animating=True;self._paint_frame()


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#  THE ART.  Everything below only draws; it reads the rule state and never writes to it.
#  Every thing on screen is a named Sprite (name, tags, layer): ground, roads, buildings, props, people, cars, fires,
#  the console.  Layers: ground -20, roads -12, props -9, craters -7, roofs -5, trees -4, doors -3, scan -1, fire 5,
#  beacon 6, aim 8, support 9, impact 10, smoke 11, ambient 16, heat 19, contacts 20-25, console 30+.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

WHT, BLK, MAG, PNK, RED, BLU, LBL, YEL, ORG, MAR, GRN, VIO = 0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
# one letter per flat colour so sprites can be drawn as pictures; capital letters are slots a caller fills in
KEY = dict(w=0, k=5, m=6, p=7, r=8, b=9, l=10, y=11, o=12, n=13, g=14, v=15)


def art(rows, slots=None):
    """Turn a drawn picture (list of strings) into engine pixels. '.' is clear, lower case is a fixed colour,
    capitals are looked up in slots."""
    slots = slots or {}
    return np.array([[-1 if ch == '.' else (KEY[ch] if ch in KEY else slots[ch]) for ch in row] for row in rows],
                    dtype=np.int8)


def shifted(rows, top_rows, dx=1):
    """The same picture swaying: the first top_rows rows lean one pixel right (canvas padded by one)."""
    return ['.' * dx + r if i < top_rows else r + '.' * dx for i, r in enumerate(rows)]


def mix(*values):
    """Small stable hash so every prop, person and puff keeps its own look from one frame to the next."""
    h = 2166136261
    for v in values:
        h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    return h


def name_seed(text):
    return sum((i + 1) * ord(c) for i, c in enumerate(str(text)))


# ───────────────────────────── the nine mission looks (one per mission; the city changes season each time) ──────────
# ground: the field colour; mark: road dashes; road: (kerb, surface, mark) of the streets; roofs: (tile, light tile) and
# roofs2: the second roof colour a ward mixes in so the rooftops are not all one colour; rstyle: what the season puts on
# its roofs (snow, frosting, bunting...); tree: (kind, canopy, highlight, fruit); smalls: the small props that sit beside
# buildings; big: the two tall landmarks that stand in the narrow gaps of the ward; plaza: the centrepiece of a courtyard;
# deco: scatter on the ground (kind, colour); critters: the two little animals that live in the spare corners of this
# season; ambient: what drifts; floor: the two plaza tiles; border: (rail, post) of the world-edge fence.
THEMES = (
    dict(ground=GRN, mark=YEL, road=(WHT, BLK, YEL), roofs=(RED, ORG), roofs2=(BLU, LBL), rstyle='solar',
         tree=('apple', GRN, YEL, RED), critters=('rabbit', 'duck'),
         smalls=('flowers', 'bench', 'bush'), big=('windmill', 'pond'), plaza='fountain',
         deco=('daisy', WHT), ambient='butterfly', floor=(WHT, LBL), border=(ORG, MAR)),
    dict(ground=YEL, mark=MAR, road=(MAR, ORG, WHT), roofs=(BLU, LBL), roofs2=(MAG, PNK), rstyle='sand',
         tree=('acacia', GRN, WHT, ORG), critters=('lizard', 'beetle'),
         smalls=('cactus', 'rocks', 'bench'), big=('pyramid', 'tent'), plaza='oasis',
         deco=('ripple', ORG), ambient='sand', floor=(WHT, YEL), border=(MAR, ORG)),
    dict(ground=WHT, mark=WHT, road=(LBL, BLK, WHT), roofs=(VIO, MAG), roofs2=(BLU, LBL), rstyle='snow',
         tree=('snowpine', GRN, WHT, RED), critters=('penguin', 'fox'),
         smalls=('snowman', 'lamp', 'bush'), big=('igloo', 'snowfolk'), plaza='rink',
         deco=('drift', LBL), ambient='snow', floor=(LBL, WHT), border=(BLU, LBL)),
    dict(ground=VIO, mark=YEL, road=(LBL, BLK, YEL), roofs=(YEL, WHT), roofs2=(BLU, LBL), rstyle='spots',
         tree=('toadtree', MAG, PNK, YEL), critters=('frog', 'cat'),
         smalls=('mushroom', 'lamp', 'bench'), big=('toadstool', 'moonpond'), plaza='ring',
         deco=('star', LBL), ambient='firefly', floor=(BLU, VIO), border=(MAG, PNK)),
    dict(ground=LBL, mark=MAR, road=(MAR, ORG, MAR), roofs=(RED, WHT), roofs2=(BLU, WHT), rstyle='awning',
         tree=('palm', GRN, YEL, MAR), critters=('crab', 'gull'),
         smalls=('buoy', 'crate', 'barrel'), big=('lighthouse', 'boat'), plaza='dock',
         deco=('wave', BLU), ambient='gull', floor=(WHT, BLU), border=(BLU, WHT)),
    dict(ground=ORG, mark=YEL, road=(MAR, BLK, YEL), roofs=(BLU, WHT), roofs2=(VIO, MAG), rstyle='leaf',
         tree=('maple', RED, YEL, ORG), critters=('squirrel', 'hedgehog'),
         smalls=('pumpkin', 'bench', 'bush'), big=('haystack', 'scarecrow'), plaza='well',
         deco=('leafpile', MAR), ambient='leaf', floor=(YEL, WHT), border=(ORG, YEL)),
    dict(ground=BLU, mark=WHT, road=(PNK, BLK, WHT), roofs=(WHT, PNK), roofs2=(YEL, ORG), rstyle='frosting',
         tree=('candytree', PNK, WHT, YEL), critters=('gummy', 'cookie'),
         smalls=('lollipop', 'bench', 'flowers'), big=('cupcake', 'giantlolly'), plaza='candy',
         deco=('sprinkle', WHT), ambient='heart', floor=(PNK, WHT), border=(WHT, PNK)),
    dict(ground=BLK, mark=LBL, road=(VIO, BLK, LBL), roofs=(VIO, MAG), roofs2=(BLU, LBL), rstyle='moon', edge=BLU,
         tree=('nightpine', VIO, LBL, YEL), critters=('owl', 'bat'),
         smalls=('lamp', 'lamp', 'bench'), big=('observatory', 'campfire'), plaza='moonpool',
         deco=('star', WHT), ambient='stars', floor=(BLU, VIO), border=(VIO, LBL)),
    dict(ground=GRN, mark=WHT, road=(YEL, BLK, WHT), roofs=(BLU, WHT), roofs2=(RED, YEL), rstyle='bunting',
         tree=('lighttree', MAG, PNK, YEL), critters=('monkey', 'seal'),
         smalls=('balloon', 'lantern', 'balloon'), big=('bigtop', 'balloons'), plaza='carousel',
         deco=('sprinkle', BLU), ambient='confetti', floor=(YEL, WHT), border=(BLU, WHT)),
)

# trees: A canopy, B highlight, C fruit or blossom, n trunk.  Each season grows its own kind of tree; the top rows lean for
# the sway (see tree_pixels).  Never wider than seven, never taller than eight.
TREE_PICTURES = {
    'apple': ('.kkkk.', 'kABAAk', 'kACAAk', 'kAAACk', 'kAAAAk', '.kkkk.', '..kn..', '..nn..'),
    'acacia': ('..kkk..', 'kkABAkk', 'kAABAAk', 'kAAAACk', '.kkkkk.', '...n...', '..kn...', '...n...'),
    'snowpine': ('..kk..', '.kwwk.', '.kAAk.', 'kwwwwk', 'kAAAAk', 'kwACwk', 'kAAAAk', '..nn..'),
    'toadtree': ('.kkkkk.', 'kABBBAk', 'kAACAAk', 'kAAAAAk', '.kkkkk.', '...n...', '...n...', '..nnn..'),
    'palm': ('k.kkk.k', 'kAkAkAk', '.kABAk.', 'kAkCkAk', '..kCk..', '..knk..', '..knk..', '..kn...'),
    'maple': ('.kkkkk.', 'kABAAAk', 'kAACAAk', 'kACAABk', '.kAAAk.', '..kkk..', '..knk..', '..knn..'),
    'candytree': ('.kkkk.', 'kAwAAk', 'kBAwAk', 'kAwACk', '.kkkk.', '..ww..', '..ww..', '.wwww.'),
    'nightpine': ('..kk..', '.kBAk.', '.kAAk.', 'kBAAAk', 'kAAACk', 'kAAAAk', 'kAAAAk', '..nn..'),
    'lighttree': ('.kkkk.', 'kCABCk', 'kAAAAk', 'kBAACk', 'kAAAAk', '.kkkk.', '..kn..', '..nn..'),
}
# small props beside the buildings, two frames each (a flicker, a nod, a glint); A and B are the season's canopy colours
SMALL_PICTURES = {
    'flowers': (('p.y.w', 'ggggg', 'knnnk'), ('y.p.w', 'ggggg', 'knnnk')),
    'bench': (('.....', 'ooooo', 'nnnnn', 'k...k'), ('..b..', 'ooooo', 'nnnnn', 'k...k')),
    'bush': (('.kkk.', 'kAAAk', 'kABAk'), ('.kkk.', 'kACAk', 'kABAk')),
    'rocks': (('.kk...', 'kookk.', 'kwoook'), ('.kk..y', 'kookk.', 'kwoook')),
    'cactus': (('..g.', 'g.gg', 'gggk', '..g.', '..n.'), ('.pg.', 'g.gg', 'gggk', '..g.', '..n.')),
    'snowman': (('.k.', 'kkk', 'kwk', 'rrr', 'wkw', 'www'), ('.k.', 'kkk', 'www', 'rrr', 'wkw', 'www')),
    'lamp': (('.y.', 'yoy', '.k.', '.k.'), ('.w.', 'ywy', '.k.', '.k.')),
    'mushroom': (('.rr.', 'rwrr', '.ww.', '.ww.'), ('.rr.', 'rrwr', '.ww.', '.ww.')),
    'buoy': (('.w.', 'rwr', 'wrw', '.k.'), ('.y.', 'rwr', 'wrw', '.k.')),
    'crate': (('kkkk', 'konk', 'knok', 'kkkk'),),
    'barrel': (('kkk', 'non', 'non', 'kkk'),),
    'pumpkin': (('.ng.', 'okko', '.oo.'), ('.ng.', 'oyyo', '.oo.')),
    'lollipop': (('pwp', 'wpw', 'pwp', '.w.', '.w.'), ('wpw', 'pwp', 'wpw', '.w.', '.w.')),
    'balloon': (('.A.', 'AwA', 'AAA', '.A.', '.k.'), ('.A.', 'AAA', 'AwA', '.A.', '.k.')),
    'lantern': (('.k.', 'ooo', 'oyo', 'ooo'), ('.k.', 'ooo', 'owo', 'ooo')),
}
# ground scatter, two frames each so the ground itself twinkles and sways
DECO_PICTURES = {
    'daisy': (('.A.', 'AyA', '.A.'), ('.A.', 'AwA', '.A.')),
    'ripple': (('.AA.',), ('A..A',)),
    'drift': (('.AA.', 'AAAA'), ('..AA', 'AAAA')),
    'star': (('.A.', 'AwA', '.A.'), ('...', '.w.', '...')),
    'wave': (('A.A.', '.A.A'), ('.A.A', 'A.A.')),
    'leafpile': (('.A.', 'AoA'), ('.A.', 'AyA')),
    'sprinkle': (('A.', '.p'), ('.A', 'p.')),
    'tuft': (('A.A', '.A.'), ('.A.', 'A.A')),
}
# the little animals that live in the spare corners, five wide, four tall, two frames (blink, hop, flutter)
CRITTERS = {
    'rabbit': (('.w.w.', 'wwwww', 'wkwkw', '.wpw.'), ('.w.w.', 'wwwww', 'wwwww', '.wpw.')),
    'duck': (('.yyy.', 'ykyky', '.ooo.', '.yyy.'), ('.yyy.', 'yyyyy', '.ooo.', '.yyy.')),
    'lizard': (('g...g', 'gkgkg', 'ggggg', '.ggg.'), ('g...g', 'gkgkg', 'ggggg', '.grg.')),
    'beetle': (('k...k', '.kbk.', 'kbwbk', '.kbk.'), ('.k.k.', '.kbk.', 'kbwbk', 'k.b.k')),
    'penguin': (('.kkk.', 'kwkwk', 'kkokk', '.o.o.'), ('.kkk.', 'kkkkk', 'kkokk', 'o.o..')),
    'fox': (('o...o', 'okoko', 'owkwo', '.www.'), ('o...o', 'ooooo', 'owkwo', '.www.')),
    'frog': (('.g.g.', 'gkgkg', 'ggggg', '.g.g.'), ('.g.g.', 'ggggg', 'ggggg', 'g...g')),
    'cat': (('k...k', 'kkkkk', 'kykyk', '.kkk.'), ('k...k', 'kkkkk', 'kkkkk', '.kkk.')),
    'crab': (('r...r', 'rrrrr', 'rkrkr', 'r.r.r'), ('rr.rr', 'rrrrr', 'rkrkr', '.r.r.')),
    'gull': (('.www.', 'wkwkw', '.wyw.', '.o.o.'), ('.www.', 'wwwww', '.wyw.', 'o...o')),
    'squirrel': (('n...n', 'nknkn', 'nyyyn', '.nnno'), ('n...n', 'nnnnn', 'nyyyn', '.nnno')),
    'hedgehog': (('.k.k.', 'kkkkk', 'kkkyk', '.n.n.'), ('k.k.k', 'kkkkk', 'kkkyk', '.n.n.')),
    'gummy': (('yy.yy', 'yyyyy', 'ykyky', '.yyy.'), ('yy.yy', 'yyyyy', 'yyyyy', '.yyy.')),
    'cookie': (('.ooo.', 'okoko', 'ooyoo', '.o.o.'), ('.ooo.', 'ooooo', 'ooyoo', 'o...o')),
    'owl': (('n...n', 'nnnnn', 'ykoky', '.nnn.'), ('n...n', 'nnnnn', 'nnonn', '.nnn.')),
    'bat': (('v...v', 'vvvvv', '.vkv.', '..v..'), ('..v..', '.vkv.', 'vvvvv', 'v...v')),
    'monkey': (('n...n', 'nyyyn', 'nkyky', '.nnn.'), ('n...n', 'nyyyn', 'nyyyn', '.nnn.')),
    'seal': (('.lll.', 'lkllk', 'lllll', '.lrl.'), ('.lll.', 'lllll', 'lllll', '.lrl.')),
}
# the five console icons: 7 wide, 5 tall
ICON_PICTURES = {
    'heavy': ('...y.o.', '..vvk..', '.vwvvv.', '.vvvvn.', '..vnn..'),
    'precision': ('..lwl..', '.l.w.l.', 'lwwkwwl', '.l.w.l.', '..lwl..'),
    'fire': ('...y...', '..yoy..', '.yorro.', '.orrro.', '..ooo..'),
    'aid': ('.gg.gg.', 'ggwgwgg', '.gwwwg.', '..ggg..', '...g...'),
    'beacon': ('y..y..y', '.y.w.y.', '..ywy..', '.y.w.y.', 'y..y..y'),
}
FLIGHT_PICTURES = {
    'heavy': ('...o.', '..y..', '.kkk.', 'kwkkk', 'kkkkk', '.kkk.'),
    'precision': ('.w.', '.l.', '.l.', 'lbl', 'b.b', '...'),
    'fire': ('..y..', '.yoy.', '.oro.', '.kkk.', '.kkk.', '..k..'),
    'aid': ('.gwgwg.', 'gwgwgwg', 'k..k..k', '.k.k.k.', '..kok..', '..kkk..'),
    'beacon': ('.y.', 'yyy', '.y.', '.o.', '.o.', '.o.'),
}
# ward landmarks: the tall shapes that stand in the narrow gaps beside buildings, two per season, each with two frames
# (blades, glints, flames, sway).  Drawn as pictures, no words.
LANDMARKS = {
    'windmill': (('r...w', '.r.w.', '..y..', '.w.r.', 'w.o.r', '.owo.', '.oko.', 'ooooo'),
                 ('..r..', '..w..', 'wwyrr', '..w..', '..o..', '.owo.', '.oko.', 'ooooo')),
    'pond': (('.lll.', 'lbwbl', 'lbbgl', '.lll.'), ('.lll.', 'lbbbl', 'lwbgl', '.lll.')),
    'pyramid': (('..y..', '.yyo.', 'yyooo', 'yoooo', 'nnnnn'), ('..w..', '.yyo.', 'yyooo', 'yoooo', 'nnnnn')),
    'tent': (('..k..', '.rwr.', 'rwrwr', 'rrkrr'), ('..y..', '.rwr.', 'rwrwr', 'rrkrr')),
    'igloo': (('.lll.', 'lwlwl', 'lwwwl', 'lkkkl'), ('.lll.', 'lwlwl', 'lwwwl', 'lkkkl')),
    'snowfolk': (('..k..', '.kkk.', 'lwwwl', 'lkokl', 'lrrrl', 'lwkwl', 'lwwwl', '.lll.'),
                 ('..k..', '.kkk.', 'lwwwl', 'lkokl', 'lrrrr', 'lwkwl', 'lwwwl', '.lll.')),
    'toadstool': (('.rrr.', 'rwrwr', 'rrrrr', '.www.', '.wlw.', '.www.'),
                  ('.rrr.', 'rrwrr', 'rwrrw', '.www.', '.wlw.', '.www.')),
    'moonpond': (('.bbb.', 'bbwbb', 'bbbbb', '.bbb.'), ('.bbb.', 'bbbbb', 'bwbbb', '.bbb.')),
    'lighthouse': (('.rr.', 'kyyk', '.kk.', '.ww.', '.rr.', '.ww.', '.rr.', '.ww.', 'kkkk'),
                   ('.rr.', 'kwwk', '.kk.', '.ww.', '.rr.', '.ww.', '.rr.', '.ww.', 'kkkk')),
    'boat': (('..y..', '.kww.', '.kwww', '.k...', 'rrrrr', '.rrr.'), ('..y..', '.kww.', '.kww.', '.k...', 'rrrrr', '.rrr.')),
    'haystack': (('.yyy.', 'yoyoy', 'yyoyy', 'ooooo'), ('.yyy.', 'yyoyo', 'yoyyy', 'ooooo')),
    'scarecrow': (('.ooo.', 'ooooo', '.yky.', 'yvvvy', '.vvv.', '.vwv.', '..k..', '..k..'),
                  ('.ooo.', 'ooooo', '.yky.', 'yvvvy', '.vvv.', '.vwv.', '..k..', '..k..')),
    'cupcake': (('..r..', '.www.', 'ppppp', 'yoyoy', '.yoy.'), ('.r...', '.www.', 'ppppp', 'yoyoy', '.yoy.')),
    'giantlolly': (('.ppp.', 'pwpwp', 'ppwpp', 'pwpwp', '.ppp.', '..w..', '..w..', '..w..'),
                   ('.ppp.', 'pppwp', 'pwpwp', 'pwppp', '.ppp.', '..w..', '..w..', '..w..')),
    'observatory': (('.vvv.', 'vvvyv', 'vvyyv', 'vvvvv', 'lllll'), ('.vvv.', 'vvvwv', 'vvwwv', 'vvvvv', 'lllll')),
    'campfire': (('..y..', '.yoy.', '.ror.', 'nnnnn'), ('.y.y.', '.oyo.', '.ror.', 'nnnnn')),
    'bigtop': (('..y..', '.bwb.', 'bwbwb', 'bwbwb', 'bbkbb'), ('..o..', '.bwb.', 'bwbwb', 'bwbwb', 'bbkbb')),
    'balloons': (('rr.bb', 'rr.bb', '.k.k.', '..k..', '..k..', '..k..'), ('.rr.b', '.rrbb', '..kk.', '..k..', '..k..', '..k..')),
}
# the same landmarks drawn three wide, for the narrow gaps (most gaps between a ward's buildings are three pixels across).
# Placement picks the wide picture only where five pixels of free ground really exist, so no landmark lies over a street.
LANDMARKS_NARROW = {
    'windmill': (('.r.', 'wyw', '.r.', '.o.', 'owo', 'oko', 'ooo', 'ooo'), ('r.w', '.y.', 'w.r', '.o.', 'owo', 'oko', 'ooo', 'ooo')),
    'pond': (('g.y', 'gg.', 'lll', 'bwb', 'bgb', 'lll'), ('.gy', 'gg.', 'lll', 'bbw', 'bgb', 'lll')),
    'pyramid': (('.y.', 'yoy', 'yoo', 'ooo', 'nnn'), ('.w.', 'yoy', 'yoo', 'ooo', 'nnn')),
    'tent': (('.y.', 'rwr', 'wrw', 'rkr'), ('.o.', 'rwr', 'wrw', 'rkr')),
    'igloo': (('.l.', 'lwl', 'lll', 'lkl'), ('.w.', 'lwl', 'lll', 'lkl')),
    'snowfolk': (('.k.', 'kkk', 'kwk', 'rrr', 'wkw', 'www', 'www'), ('.k.', 'kkk', 'www', 'rrr', 'wkw', 'www', 'www')),
    'toadstool': (('rrr', 'wrw', 'rrr', '.w.', '.w.', '.w.'), ('rrr', 'rwr', 'rrr', '.w.', '.w.', '.w.')),
    'moonpond': (('v.v', '.v.', 'lll', 'bwb', 'bbb', 'lll'), ('v.v', 'v.v', 'lll', 'bbb', 'bwb', 'lll')),
    'lighthouse': (('.r.', 'kyk', 'kkk', 'www', 'rrr', 'www', 'rrr', 'kkk'), ('.r.', 'kwk', 'kkk', 'www', 'rrr', 'www', 'rrr', 'kkk')),
    'boat': (('.y.', 'wkw', 'wkw', '.k.', 'rrr', '.r.'), ('.o.', 'wkw', 'wkw', '.k.', 'rrr', '.r.')),
    'haystack': (('.y.', 'yoy', 'ooo', 'ooo'), ('.k.', 'yoy', 'ooo', 'ooo')),
    'scarecrow': (('.k.', 'kkk', 'kyk', 'vvv', '.v.', '.k.', '.k.'), ('.k.', 'kkk', 'kyk', 'vvy', '.v.', '.k.', '.k.')),
    'cupcake': (('.r.', 'www', 'ppp', 'yoy', '.y.'), ('.r.', 'wpw', 'ppp', 'yoy', '.y.')),
    'giantlolly': (('ppp', 'pwp', 'ppp', '.w.', '.w.', '.w.'), ('ppp', 'wpp', 'ppp', '.w.', '.w.', '.w.')),
    'observatory': (('.y.', '.v.', 'vyv', 'vvv', 'lll'), ('.w.', '.v.', 'vwv', 'vvv', 'lll')),
    'campfire': (('.y.', 'yoy', 'ror', 'nnn'), ('y.y', 'oyo', 'ror', 'nnn')),
    'bigtop': (('.y.', 'bwb', 'wbw', 'bkb'), ('.o.', 'bwb', 'wbw', 'bkb')),
    'balloons': (('.r.', 'rrr', 'rwr', '.r.', '.k.', '.k.', '.k.'), ('.r.', 'rrr', 'rrw', '.r.', '.k.', '.k.', '.k.')),
}
# courtyard centrepieces: seven wide, five tall, two frames each
PLAZAS = {
    'oasis': (('..g.g..', '.lbgbl.', 'lbbwbbl', '.lbbbl.', '..lll..'), ('.g...g.', '.lbgbl.', 'lbbbwbl', '.lbbbl.', '..lll..')),
    'rink': (('.lllll.', 'lwrwwwl', 'lwwwwwl', 'lwwwbwl', '.lllll.'), ('.lllll.', 'lwwwrwl', 'lwwwwwl', 'lwbwwwl', '.lllll.')),
    'ring': (('.y.y.y.', 'l.....l', 'y..w..y', 'l.....l', '.y.y.y.'), ('.l.l.l.', 'y.....y', 'l..w..l', 'y.....y', '.l.l.l.')),
    'dock': (('...k...', '..kkk..', '...k...', 'k..k..k', '.kkkkk.'), ('...k..y', '..kkk..', '...k...', 'k..k..k', '.kkkkk.')),
    'well': (('.ooooo.', 'okbbbko', 'okbwbko', 'okbbbko', '.ooooo.'), ('.ooooo.', 'okbbbko', 'okbbwko', 'okbbbko', '.ooooo.')),
    'candy': (('.rwrwr.', 'wrwrwrw', 'rwrywrw', 'wrwrwrw', '.rwrwr.'), ('.wrwrw.', 'rwrwrwr', 'wrwyrwr', 'rwrwrwr', '.wrwrw.')),
    'moonpool': (('.lllll.', 'lbbbwbl', 'lbwbbbl', 'lbbbbbl', '.lllll.'), ('.lllll.', 'lbbwbbl', 'lbbbbwl', 'lbbbbbl', '.lllll.')),
    'carousel': (('..y.y..', '.rwrwr.', 'rwrwrwr', '.k.k.k.', 'kkkkkkk'), ('..o.o..', '.wrwrw.', 'wrwrwrw', '.k.k.k.', 'kkkkkkk')),
}
TOOL_COLOUR = {'heavy': ORG, 'precision': WHT, 'fire': MAR, 'aid': GRN, 'beacon': YEL}
TOOL_PIP = {'heavy': YEL, 'precision': LBL, 'fire': ORG, 'aid': GRN, 'beacon': YEL}
# colour of the small ground tufts for each of the nine seasons
TUFT_COLOUR = (YEL, MAR, LBL, MAG, WHT, YEL, YEL, VIO, YEL)
PERSON_SKIN = (YEL, ORG, MAR)
PERSON_HAIR = (MAR, VIO, BLU, ORG, WHT)
PERSON_SLEEVE = (BLU, VIO, MAG, LBL, WHT)
PERSON_TROUSERS = (BLU, MAR, VIO, BLK)
CAR_BODY = (BLU, ORG, MAG, VIO, LBL, WHT, RED)
CONFETTI = (MAG, BLU, VIO, ORG, WHT, PNK, LBL, MAG)


def small_art(kind, theme, frame=0):
    """A small prop in the colours of the current look; frame picks which of its (one or two) pictures to show."""
    slots = {'A': theme['tree'][1], 'B': theme['tree'][2], 'C': theme['tree'][3]}
    if kind == 'balloon':
        slots['A'] = MAG if theme['ground'] != MAG else LBL
    pictures = SMALL_PICTURES[kind]
    return art(pictures[frame % len(pictures)], slots)


# ───────────────────────────── putting a sprite on the stage ─────────────────────────────
def put(game, name, pixels, x, y, layer=0, tags=(), field=False, key=None):
    """Create or update the sprite called name.  pixels may be a function so a cached picture (same key) is not
    redrawn.  field=True clips to the world, layer >= 30 is console and rides with the camera."""
    full = game._full.get(name) if key is not None and game._keys.get(name) == key else None
    if full is None:
        full = np.asarray(pixels() if callable(pixels) else pixels, dtype=np.int8)
        game._full[name] = full
        game._keys[name] = key
    x, y = int(x), int(y)
    if layer >= 30:
        x += int(game.camera.x)
        y += int(game.camera.y)
    shown = full
    clip = (0, 0)
    if field:
        left, top = max(0, x), max(0, y)
        right = min(game.world_width, x + full.shape[1])
        bottom = min(game.world_height, y + full.shape[0])
        if right <= left or bottom <= top:
            return None
        clip = (left - x, top - y, right - x, bottom - y)
        shown = full[clip[1]:clip[3], clip[0]:clip[2]]
        x, y = left, top
    sprite = game._sprites.get(name)
    if sprite is None:
        sprite = Sprite(pixels=shown, name=name, x=x, y=y, layer=layer, collidable=False, tags=list(tags))
        game.current_level.add_sprite(sprite)
        game._sprites[name] = sprite
        game._shown[name] = (id(full), clip)
    else:
        if game._shown.get(name) != (id(full), clip):
            sprite.pixels = shown
            game._shown[name] = (id(full), clip)
        if sprite.x != x or sprite.y != y:
            sprite.set_position(x, y)
        if sprite.layer != layer:
            sprite.set_layer(layer)
    game._used.add(name)
    return sprite


def brackets(colour, size=8, inner=None):
    """Four corner brackets (and optionally a centre dot)."""
    px = np.full((size, size), -1, dtype=np.int8)
    for x, y in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        px[y, x] = colour
        px[y, x + (1 if x == 0 else -1)] = colour
        px[y + (1 if y == 0 else -1), x] = colour
    if inner is not None:
        px[size // 2, size // 2] = inner
    return px


def ring_pixels(colour, size):
    px = np.full((size, size), colour, dtype=np.int8)
    px[1:-1, 1:-1] = -1
    return px


def disc(size, fill, edge):
    """A filled round blob (smoke, craters, bursts)."""
    px = np.full((size, size), -1, dtype=np.int8)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = (x - c) ** 2 + (y - c) ** 2
            if d <= (size / 2 - 0.2) ** 2:
                px[y, x] = fill
            if (size / 2 - 1.4) ** 2 < d <= (size / 2 + 0.2) ** 2:
                px[y, x] = edge
    return px


# ───────────────────────────── buildings: roofs, damage, rubble, plazas ─────────────────────────────
KIND_ROOFS = {'hospital': (WHT, LBL), 'school': (MAG, PNK), 'station': (BLU, LBL), 'depot': (ORG, MAR)}
# the next-darker and next-lighter flat colour of each tile, so a roof can show shingles, a ridge and a shaded eave
DARKER = {WHT: LBL, LBL: BLU, BLU: VIO, MAG: VIO, PNK: MAG, YEL: ORG, ORG: MAR, RED: MAR, MAR: BLK, VIO: BLK, GRN: BLK}
LIGHTER = {MAR: ORG, ORG: YEL, BLU: LBL, LBL: WHT, VIO: MAG, MAG: PNK, RED: ORG, PNK: WHT, WHT: WHT, YEL: WHT}


def roof_pixels(kind, w, h, integrity, theme, variant=0):
    """One roof, drawn as a picture: black outline, a pitched roof (light upper slope, ridge, darker lower slope, shaded
    eave), shingle ticks, a trim that says what the building is, and cracks, scorch and a hole as it takes damage."""
    if kind == 'courtyard':
        return plaza_pixels(w, h, theme)
    if integrity <= 0:
        return rubble_pixels(w, h)
    a, b = KIND_ROOFS.get(kind, theme['roofs'])
    if kind == 'home' and variant == 1:                      # one house in three wears the season's second roof colour
        a, b = theme['roofs2']
    px = np.full((h, w), theme.get('edge', BLK), dtype=np.int8)   # the night city gets a blue outline: black would vanish
    ridge = h // 2
    for row in range(1, h - 1):
        for col in range(1, w - 1):
            main = b if row < ridge else a                  # upper slope catches the light
            if row == ridge:
                main = DARKER.get(a, BLK)                   # the ridge line, a shadow between the two slopes
            elif (row + col * 2) % 5 == 0 and row != 1 and DARKER.get(main, BLK) != BLK:     # shingle ticks
                main = DARKER[main]
            px[row, col] = main
    px[1, 1:w - 1] = LIGHTER.get(b, WHT)                    # a lit top edge
    px[1, 1] = WHT                                          # catch-light on the corner
    if kind == 'hospital':
        px[1, 1:w - 1] = PNK
        px[h - 2, 1:w - 1] = PNK
        px[1:h - 1, 1] = PNK
        px[1:h - 1, w - 2] = PNK
        px[2:h - 2, 2:w - 2] = WHT
        px[h - 3, 2:w - 2] = LBL
        px[2:h - 2, w - 3] = LBL
    elif kind == 'station':
        px[ridge, 1:w - 1] = WHT                            # white band
        px[ridge + 1, 1:w - 1] = BLU
    elif kind == 'depot':
        for col in range(1, w - 1):
            px[h - 2, col] = BLK if col % 2 else YEL         # hazard stripe along the loading edge
        for col in range(2, w - 2, 3):                      # roll-up doors seen from above
            px[2:4, col:col + 2] = LBL
            px[4, col:col + 2] = BLU
    elif kind == 'school':
        px[ridge, 1:w - 1] = YEL                            # a gold ridge cap
        px[ridge - 1, 1:w - 1:2] = WHT
    elif kind == 'home' and w >= 8 and h >= 6:
        px[1:3, w - 4:w - 2] = [[LBL, WHT], [RED, MAR]]    # brick chimney stack
        px[3, w - 4:w - 2] = BLK                            # its shadow
    px[0, 0] = px[0, w - 1] = px[h - 1, 0] = px[h - 1, w - 1] = -1
    if integrity >= 2 and kind != 'hospital':
        roof_style(px, theme['rstyle'], kind, w, h, variant)
    if integrity < 3:                                      # cracks run across the roof, with scorch around them
        for i in range(h - 2):
            col = w // 2 - 1 + (i % 2) + i // 3
            if 1 <= col < w - 1:
                px[1 + i, col] = BLK
                if 1 <= col + 1 < w - 1 and i % 2:
                    px[1 + i, col + 1] = MAR
        px[2, 2] = px[3, 2] = BLK
        px[h - 3, 2] = MAR
    if integrity < 2:                                      # a hole through to the fire below
        cy, cx = h // 2, w // 2
        px[cy - 2:cy + 2, cx - 3:cx + 3] = MAR              # scorched ring
        px[cy - 1:cy + 2, cx - 2:cx + 2] = BLK
        px[cy - 1, cx - 1] = ORG
        px[cy, cx - 2] = RED
        px[cy + 1, cx] = YEL
    return px


def roof_style(px, style, kind, w, h, variant):
    """What the season lays on a roof: snow caps, frosting with sprinkles, bunting, leaves, sand drifts, awnings, solar
    panels, moonlit skylights, red spots.  Picture only; it is drawn into the roof and cracks run over it."""
    home = kind == 'home' and w >= 8 and h >= 6
    if style == 'snow':
        px[1, 1:w - 1] = WHT                                # a thick cap of snow along the top edge
        px[2, 1:w - 1:2] = WHT                              # with icicle drips below it
        px[h - 2, 1:w - 1:3] = WHT
    elif style == 'frosting':
        px[1, 1:w - 1] = WHT
        px[2, 1:w - 1:2] = WHT
        for column in range(2, w - 2, 3):                   # sprinkles
            px[3 + (variant + column) % 2, column] = (RED, YEL, GRN, VIO)[(variant + column) % 4]
    elif style == 'bunting':
        for column in range(1, w - 1):                      # a string of flags from edge to edge
            px[3, column] = (RED, YEL, BLU, WHT, GRN)[(column + variant) % 5]
        px[4, 1:w - 1:2] = (YEL, RED, WHT)[variant % 3]
    elif style == 'leaf':
        for n in range(7):                                  # fallen leaves lying on the tiles
            r, c = mix(variant, n, w) % (h - 2), (mix(variant, n, h) >> 3) % (w - 2)
            px[1 + r, 1 + c] = (ORG, YEL, RED)[n % 3]
    elif style == 'sand':
        px[1, 1:3] = px[2, 1] = YEL                         # sand blown into the corners
        px[h - 2, w - 4:w - 1] = px[h - 3, w - 2] = YEL
        if home:
            px[3, 2:w - 2:2] = (WHT, RED, YEL)[variant % 3]  # washing on a line
    elif style == 'awning':
        for column in range(1, w - 1):                      # a striped awning along the lower edge
            px[h - 3, column] = RED if column % 2 else WHT
            px[h - 2, column] = WHT if column % 2 else RED
    elif style == 'solar' and home:
        if variant % 2:
            px[h - 4:h - 2, 2:5] = [[BLU, LBL, BLU], [LBL, BLU, LBL]]      # solar panel
        else:
            px[h - 3, 2:w - 4] = GRN                                         # a roof garden
            px[h - 4, 3:w - 5:2] = (YEL, WHT)[variant % 2]
    elif style == 'moon':
        px[2, 2:4] = YEL                                    # lit skylights
        px[h - 3, w - 5:w - 3] = YEL
        px[h - 2, 1:w - 1:2] = LBL                          # moonlit edge
    elif style == 'spots':
        for r, c in ((2, 2), (4, 4), (3, w - 3), (h - 3, 3)):
            if r < h - 1 and c < w - 1:
                px[r, c] = RED


def rubble_pixels(w, h):
    """What is left of a roof: a charred slab with a bright scorch ring, a few tilted black beams, bricks and one live
    ember, kept orderly (few colours, big shapes) so a wrecked building reads as one thing."""
    px = np.full((h, w), -1, dtype=np.int8)
    for row in range(h):
        for col in range(w):
            reach = ((col - (w - 1) / 2) / (w / 2)) ** 2 + ((row - (h - 1) / 2) / (h / 2)) ** 2
            if reach < 0.55:
                px[row, col] = BLK
            elif reach < 1.0:
                px[row, col] = MAR if mix(row, col, w) % 3 else BLK
            elif reach < 1.3 and mix(row, col, w) % 3 == 0:
                px[row, col] = MAR                         # soot thrown outward
    for col in range(1, w - 1, 3):                         # splintered beams lying across the slab
        y = 1 + (col * 5) % max(1, h - 3)
        px[y, col:min(w - 1, col + 3)] = ORG
        px[min(h - 1, y + 1), col:min(w - 1, col + 2)] = MAR
    px[h // 2 - 1:h // 2 + 1, w // 2 - 1:w // 2 + 1] = [[ORG, YEL], [RED, ORG]]     # an ember still glowing
    px[2, 2:4] = RED                                       # a broken brick
    return px


def plaza_pixels(w, h, theme):
    first, second = theme['floor']
    px = np.zeros((h, w), dtype=np.int8)
    for row in range(h):
        for col in range(w):
            px[row, col] = first if ((row // 2) + (col // 2)) % 2 == 0 else second
    px[0, :] = BLK
    px[-1, :] = BLK
    px[:, 0] = BLK
    px[:, -1] = BLK
    return px


def fountain_pixels(jet):
    rows = ('.kkkkk.', 'kllbllk', 'klbwblk', 'kllbllk', '.kkkkk.')
    px = art(rows)
    if jet == 1:
        px[2, 3] = YEL
    elif jet == 2:
        px[1, 3] = px[3, 3] = WHT
    return px


def playground_pixels(width):
    px = np.full((3, width), ORG, dtype=np.int8)
    px[0, :] = BLK
    px[2, :] = BLK
    px[:, 0] = px[:, -1] = BLK
    px[1, width // 2] = BLU                                # a slide
    px[1, width // 2 - 1] = WHT
    px[1, 1 if width > 5 else 2] = MAG                     # a ball
    px[1, width - 2] = YEL
    return px


def flag_pixels(wave):
    rows = ('kbbbb', 'kbwwb', 'kbbbb', 'k....', 'k....')
    px = art(rows)
    if wave:
        px[0, 4] = -1
        px[2, 4] = -1
        px[1, 4] = BLU
        px[0, 3] = BLU
    return px


def smoke_column(phase):
    """Chimney smoke: three drifting puffs."""
    px = np.full((7, 4), -1, dtype=np.int8)
    for i in range(3):
        y = (6 - (phase * 2 + i * 3)) % 7
        x = (1 + (i + phase) % 2)
        px[y, x] = WHT
        if y + 1 < 7:
            px[y + 1, x] = LBL
    return px


def siren_pixels(phase):
    return np.array([[RED if phase else BLU, BLU if phase else RED]], dtype=np.int8)


def tree_pixels(kind, a, b, c, lean):
    """One tree of the season.  The crown (top half) leans a pixel in the wind; the trunk stays planted."""
    rows = TREE_PICTURES[kind]
    if lean:
        rows = shifted(rows, 3 if kind in ('palm', 'acacia', 'toadtree') else 4)
    else:
        rows = [r + '.' for r in rows]
    return art(rows, {'A': a, 'B': b, 'C': c})


# ───────────────────────────── roads, fences, ground, scatter, drifters ─────────────────────────────
def road_pixels(width, height, style):
    """A street: kerb on both long edges, a surface, a painted centre dash.  Harbour streets (kerb == surface family
    of wood) get plank joints instead of dashes so the whole street grid reads as a boardwalk."""
    kerb, surface, mark = style
    horizontal = width > height
    px = np.full((height, width), surface, dtype=np.int8)
    if horizontal:
        px[0, :] = kerb
        px[-1, :] = kerb
        if surface == ORG:                                 # planks
            px[:, ::4] = mark
        else:
            px[height // 2, 2::6] = mark
    else:
        px[:, 0] = kerb
        px[:, -1] = kerb
        if surface == ORG:
            px[::4, :] = mark
        else:
            px[2::6, width // 2] = mark
    return px


def junction_rects(roads):
    """Where a long street crosses another: a plain square so the two kerbs do not cut across each other."""
    found = []
    for hx, hy, hw, hh in roads:
        if hw <= hh:
            continue
        for vx, vy, vw, vh in roads:
            if vw >= vh:
                continue
            left, right = max(hx, vx), min(hx + hw, vx + vw)
            top, bottom = max(hy, vy), min(hy + hh, vy + vh)
            if right > left and bottom > top:
                found.append((left, top, right - left, bottom - top))
    return found


def fence_pixels(length, vertical, rail, post):
    px = np.full((2, length), rail, dtype=np.int8)
    px[1, ::4] = post
    px[0, ::4] = post
    return px.T if vertical else px


def _overlaps(rect, others, pad):
    x, y, w, h = rect
    return any(x < ox + ow + pad and ox < x + w + pad and y < oy + oh + pad and oy < y + h + pad
               for ox, oy, ow, oh in others)


def art_init(game):
    for sprite in list(game.current_level.get_sprites()):
        game.current_level.remove_sprite(sprite)
    game._sprites, game._full, game._keys, game._shown = {}, {}, {}, {}
    game._used = set()
    game._facing = {}
    theme = THEMES[game.mission_index % len(THEMES)]
    game._theme = theme
    seed = game.mission_index * 977 + 13
    put(game, 'city_ground', np.full((game.world_height, game.world_width), theme['ground']), 0, 0, -20,
        ['terrain'], key='ground')
    for index, (x, y, width, height) in enumerate(game.roads):
        put(game, 'road_' + str(index), road_pixels(width, height, theme['road']), x, y, -12, ['road'], True,
            key=('road', width, height, theme['road']))
    for index, (x, y, width, height) in enumerate(junction_rects(game.roads)):
        put(game, 'junction_' + str(index), np.full((height, width), theme['road'][1], dtype=np.int8), x, y, -11,
            ['road', 'junction'], True, key=('junction', width, height, theme['road']))
    rail, post = theme['border']
    W, H = game.world_width, game.world_height
    for name, length, vertical, x, y in (('fence_left', H, True, 0, 0), ('fence_right', H, True, W - 2, 0),
                                         ('fence_top', W, False, 0, 0), ('fence_bottom', W, False, 0, H - 2)):
        put(game, name, fence_pixels(length, vertical, rail, post), x, y, -11, ['fence'], True,
            key=('fence', length, vertical, rail, post))
    solids = [tuple(b['rect']) for b in game.buildings] + [tuple(r) for r in game.roads]
    streets = list(solids)                                  # buildings and streets only: what a landmark must not cover
    rng = np.random.default_rng(seed)
    game._props = []
    smalls = theme['smalls']
    for index, building in enumerate(game.buildings):
        x, y, w, h = building['rect']
        bid = building['id']
        if building['kind'] == 'courtyard':
            game._props.append(('fountain_' + bid, theme['plaza'], x + w // 2 - 3, y + h // 2 - 2, -4, ['fountain']))
            continue
        if index % 2 == 0:
            game._props.append(('tree_' + bid, 'tree', x + w - 2, y + h - 1, -4, ['tree']))
            solids.append((x + w - 2, y + h - 1, 7, 8))
        small = smalls[index % len(smalls)]
        placed_landmark = False
        if index % 2:                                   # the tall ward landmark stands in the gap beside the building
            landmark = theme['big'][(index // 2) % 2]
            for label, pictures, need in (('wide', LANDMARKS, 5), ('thin', LANDMARKS_NARROW, 3)):
                tall = len(pictures[landmark][0])
                free = 0                                # measure the real gap: free columns right of the building
                for column in range(x + w, x + w + need):
                    if any(sx <= column < sx + sw and y + 1 < sy + sh and sy < y + 1 + tall for sx, sy, sw, sh in streets):
                        break
                    free += 1
                if free >= need:
                    game._props.append(('landmark_' + bid, label + ':' + landmark, x + w, y + 1, -4, ['landmark']))
                    solids.append((x + w, y + 1, need, tall))
                    placed_landmark = True
                    break
        if not placed_landmark:                         # no room for a tall shape: a small prop sits below the building
            game._props.append(('small_' + bid, small, x + 1, y + h + 1, -9, ['decoration']))
            solids.append((x + 1, y + h + 1, 5, 4))
        if building['kind'] == 'school':
            pw = max(4, w - 2)
            put(game, 'playground_' + bid, playground_pixels(pw), x + 1, y + h + 1, -8, ['school_court'], True,
                key=('playground', pw))
    # the little animals of the season live in the spare corners (seven wide so they can wander a step or two)
    game._critters = []
    for attempt in range(220):
        if len(game._critters) >= 7:
            break
        x, y = int(rng.integers(3, W - 9)), int(rng.integers(6, H - 6))
        rect = (x, y - 1, 7, 5)
        if _overlaps(rect, solids, 0):
            continue
        solids.append(rect)
        game._critters.append(('critter_' + str(len(game._critters)), theme['critters'][len(game._critters) % 2], x, y,
                               mix(seed, len(game._critters))))
    game._decos = []
    for attempt in range(400):                              # two kinds of scatter: the season's own, and small tufts
        kind, colour = theme['deco'] if attempt % 3 else ('tuft', TUFT_COLOUR[game.mission_index % len(TUFT_COLOUR)])
        x, y = int(rng.integers(3, W - 7)), int(rng.integers(5, H - 5))
        size = art(DECO_PICTURES[kind][0], {'A': colour})
        rect = (x, y, size.shape[1], size.shape[0])
        if _overlaps(rect, solids, 1):
            continue
        solids.append(rect)
        game._decos.append(('deco_' + str(len(game._decos)), kind, colour, x, y))
        if len(game._decos) >= 16:                        # a calmer ground: fewer, so the roofs and people read first
            break
    game._static = set(game._used)
    game._building_cache = {}
    game._crater_cache = {}
    # drifting life: things that only ride the air and mean nothing
    ambient = theme['ambient']
    count = {'butterfly': 8, 'sand': 10, 'snow': 22, 'firefly': 12, 'gull': 4, 'leaf': 12, 'heart': 8,
             'stars': 14, 'confetti': 16}[ambient]
    speed = {'butterfly': (1, 0), 'sand': (2, 0), 'snow': (0, 1), 'firefly': (0, 0), 'gull': (2, 0),
             'leaf': (1, 1), 'heart': (0, -1), 'stars': (0, 0), 'confetti': (1, 1)}[ambient]
    game._drift = []
    for number in range(count):
        game._drift.append((number, int(rng.integers(0, W)), int(rng.integers(5, H - 5)),
                            speed[0] * (1 if number % 3 else 2) if speed[0] else 0,
                            speed[1] * (1 if number % 3 else 2) if speed[1] else 0, mix(seed, number)))


def drift_art(kind, number, step, seed):
    """One drifting thing; step says which of its frames to show."""
    if kind == 'butterfly':
        colour = (PNK, YEL, LBL, ORG)[seed % 4]
        return np.array([[colour, -1, colour], [-1, BLK, -1]] if step % 2 else [[-1, BLK, -1], [colour, -1, colour]],
                        dtype=np.int8)
    if kind == 'sand':
        return np.array([[ORG, WHT]] if step % 2 else [[WHT, ORG]], dtype=np.int8)
    if kind == 'snow':
        return np.array([[LBL]] if step % 3 else [[LBL, -1], [-1, LBL]], dtype=np.int8)
    if kind == 'firefly':
        return np.array([[LBL]] if step % 2 else [[WHT, LBL]], dtype=np.int8)
    if kind == 'gull':
        rows = (('w.w.w', '.www.', '.....'), ('..w..', 'wwwww', '.w.w.'))[step % 2]
        return art(rows)
    if kind == 'leaf':
        colour = (ORG, MAR, ORG, BLK)[seed % 4]
        return np.array([[colour, -1], [-1, BLK]] if step % 2 else [[-1, colour], [BLK, -1]], dtype=np.int8)
    if kind == 'heart':
        return art(('p.p', 'ppp', '.p.')) if step % 2 else art(('w.w', 'www', '.w.'))
    if kind == 'stars':
        return art(('.l.', 'lwl', '.l.')) if step % 3 == 0 else np.array([[WHT]], dtype=np.int8)
    colour = CONFETTI[seed % len(CONFETTI)]
    return np.array([[colour, colour], [colour, -1]] if step % 2 else [[colour, -1], [colour, colour]],
                    dtype=np.int8)


def draw_drift(game, phase):
    theme = game._theme
    kind = theme['ambient']
    t = game.tick * FRAME_COUNT + phase
    for number, sx, sy, vx, vy, seed in game._drift:
        wobble = (0, 1, 1, 0, -1, -1)[(t // 3 + number) % 6]
        if kind == 'gull':
            x = (sx + (vx * t) // FRAME_COUNT) % (game.world_width + 12) - 6
            y = sy + wobble
        elif kind in ('firefly', 'stars'):
            x, y = sx, sy
        else:
            x = (sx + (vx * t) // FRAME_COUNT + wobble) % game.world_width
            y = (sy + (vy * t) // FRAME_COUNT) % (game.world_height - 8) + 4
        step = (t // 3 + number) % 6
        put(game, 'drift_' + str(number), lambda: drift_art(kind, number, step, seed), x, y, 16, ['ambient'], True,
            key=(kind, step % 6, seed % 8))


# ───────────────────────────── people, cars, ambulances ─────────────────────────────
def person_pixels(skin, hair, sleeve, look, legs, blink, mood=0, style=0, small=False):
    """A six-by-eight person with a real face: hair (three styles, one is a cap in the shirt colour), eyes that look
    where the person walks, a mouth, a body with a black badge square where the identity colours sit, and legs that
    step.  mood: 0 calm, 1 cheering (big grin), -1 wincing (frown and a tear).  small=True is the four-by-five head
    that peeks out of a window indoors.  The picture never carries the identity colours: the black square is theirs."""
    eye = WHT if skin == MAR else BLK                       # dark skin gets bright eyes
    if small:
        rows = [[hair] * 4, [skin, eye, eye, skin] if not blink else [skin] * 4,
                [sleeve, BLK, BLK, sleeve], [sleeve, BLK, BLK, sleeve], [-1, BLK, BLK, -1] if legs else [BLK, -1, -1, BLK]]
        if mood == -1:
            rows[1] = [skin, eye, eye, LBL]
        return np.array(rows, dtype=np.int8)
    top = hair if style != 2 else sleeve                    # style 2 is a cap
    trousers = PERSON_TROUSERS[(hair + sleeve) % len(PERSON_TROUSERS)]
    rows = [[-1, top, top, top, top, -1],                   # 0 hair / cap
            [top] * 6,                                      # 1 fringe
            [skin] * 6,                                     # 2 eyes
            [skin] * 6,                                     # 3 mouth and chin
            [sleeve, sleeve, BLK, BLK, sleeve, sleeve],     # 4-5 body; the black square is the identity badge's backing
            [sleeve, sleeve, BLK, BLK, sleeve, sleeve],
            [-1, trousers, trousers, trousers, trousers, -1],  # 6 trousers
            [-1, WHT, -1, -1, WHT, -1] if legs else [-1, -1, WHT, WHT, -1, -1]]    # 7 trainers, stepping
    rows[3][0] = rows[3][5] = -1 if style != 1 else hair
    if style == 2:
        rows[1][0] = rows[1][5] = hair                      # a lick of hair under the cap
    if style == 1:
        rows[2][0] = rows[2][5] = hair                      # long hair framing the face
    left, right = {-1: (1, 3), 0: (1, 4), 1: (2, 4)}[look]
    if mood == 1:                                           # a happy squint: lids shut, wide open grin with teeth
        rows[2][left] = rows[2][right] = skin
        rows[1][left] = rows[1][right] = top if style != 0 else hair
        rows[3][1:5] = [BLK, WHT, WHT, BLK]
    elif blink:
        rows[2][left] = rows[2][right] = skin
        rows[3][2] = rows[3][3] = BLK
    elif mood == -1:                                        # a wince: eyes screwed up, tears, a small tight mouth
        rows[2][left] = rows[2][right] = eye
        rows[3][left] = rows[3][right] = LBL
        rows[3][2] = BLK
    else:
        rows[2][left] = rows[2][right] = eye
        rows[3][2] = rows[3][3] = BLK
    return np.array(rows, dtype=np.int8)


# cars seen from above, nose up: headlights, tyres, a lit roof; the four seat windows are exactly where the identity squares
# sit (two by two at the cell offsets of the rules), the solo car has one big windscreen over its single square
# Ten wide and nine tall: the body colour is the car (hood, roof pillars, boot, bumpers, tyres at the corners); the glass
# is only what peeps out between the identity squares.  B body, D its shaded side, W its highlight.
CAR_SEATS = ('.kyBBBByk.', 'kkWBBBBBkk', 'kBllBllBDk', 'kBllBllBDk', 'kDwBBBBnDk', 'kBllBllBDk', 'kBllBllBDk', 'kkBBBBBDkk',
             '.krBBBBrk.')
CAR_SOLO = ('.kyBBBByk.', 'kkWBBBBBkk', 'kBBllllBDk', 'kBBllllBDk', 'kBBllllBDk', 'kBDwBBnBDk', 'kBBBBBBBDk', 'kkBBBBBDkk',
            '.krBBBBrk.')
# the ambulance, side on: white box with a red stripe and cross, a blue-glass cab, black wheels with white hubs
AMBULANCE = ('..kkkkkk....', '.kwwwwwwkkk.', 'kwwprpwwklbk', 'kwprrrpwklbk', 'kwwprpwwkkkk', 'kbbbbbbbbbbk', '.kkwk..kwkk.',
             '..kkk..kkk..')


def contact_core(actor):
    """The identity colours, exactly as before: how many of the four cells are red says how sure the track is."""
    confidence = max(0, min(4, actor.get('confidence', 0)))
    if actor.get('traffic') and actor['role'] == 'civilian':
        cells = [YEL] * 4
    elif actor['role'] == 'civilian' and actor.get('indoors'):
        cells = [GRN] * 4
    elif confidence == 4:
        cells = [RED if actor['role'] == 'hostile' else GRN] * 4
    else:
        cells = [RED] * confidence + [YEL] * (4 - confidence)
    return np.array([cells[0:2], cells[2:4]], dtype=np.int8)


def contact_position(actor, previous, tick, phase):
    start = tuple(previous.get('observed', previous['pos']))
    end = tuple(actor.get('observed', actor['pos']))
    fresh = actor.get('observed_at', tick) == tick
    if start == end:
        return end, False
    path = [tuple(point) for point in actor.get('motion_path', [])]
    if not fresh or start != tuple(previous['pos']) or not path or path[-1] != end:
        return end, fresh
    points = [start] + path
    lengths = []
    for a, b in zip(points, points[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            return end, True
        lengths.append(abs(a[0] - b[0]) + abs(a[1] - b[1]))
    distance = min(1, (phase + 1) / 3) * sum(lengths)
    for a, b, length in zip(points, points[1:], lengths):
        if distance <= length and length:
            fraction = distance / length
            return tuple(round(v + (w - v) * fraction) for v, w in zip(a, b)), False
        distance -= length
    return end, False


# where a size-n bracket ring sits relative to the identity square (a tall person needs its ring lifted over the head)
HALO = {8: (3, 3), 10: (4, 4), 12: (5, 4)}


def threat_signal(game, name, people, x, y, phase, size=8):
    """Dashes round a contact that is gathering a crowd (cool) or arming (hot, more dashes as the time runs down)."""
    threats = [p for p in people if p.get('alive') and p['role'] == 'hostile' and p.get('attack_stage', 'quiet') != 'quiet']
    if not threats:
        return
    threat = max(threats, key=lambda p: p.get('threat_age', 0) / max(1, p.get('threat_limit', 1)))
    ratio = min(1, threat.get('threat_age', 0) / max(1, threat.get('threat_limit', 1)))
    arming = threat.get('attack_stage') == 'arming'
    count = min(8, 3 + round(ratio * 5)) if arming else 2
    colour = ORG if arming else LBL
    dashes = np.full((size, size), -1, dtype=np.int8)
    middle, last = size // 2, size - 1
    dx0, dy0 = HALO[size]
    positions = ((middle - 1, 0), (middle - 1, last), (0, middle - 1), (last, middle - 1),
                 (2, 0), (last - 3, last), (0, 2), (last, last - 3))
    for index, (dx, dy) in enumerate(positions[:count]):
        dashes[dy, dx] = colour
        if dy in (0, last):
            dashes[dy, min(last, dx + 1)] = colour
        else:
            dashes[min(last, dy + 1), dx] = colour
    put(game, 'threat_' + name, dashes, x - dx0, y - dy0, 19, ['arming' if arming else 'gathering'], True)


def draw_contacts(game, phase):
    t = game.tick * FRAME_COUNT + phase
    before = getattr(game, 'before_actors', {})
    by_id = {a['id']: a for a in game.actors}
    for actor in game.actors:
        if actor.get('onboard') or actor.get('riding'):
            continue
        old = before.get(actor['id'], actor)
        if not actor['alive'] and (phase >= 3 or not old.get('alive', False)):
            continue
        shown = actor
        (x, y), reacquired = contact_position(shown, old, game.tick, phase)
        aid = actor['id']
        seed = name_seed(aid)
        core = contact_core(shown)
        seat_people, has_seats = [], False
        if shown['role'] == 'responder':
            put(game, 'contact_' + aid, lambda: art(AMBULANCE), x - 6, y - 2, 20, ['contact', 'responder'], True,
                key='ambulance')
            flash = (t // 2) % 2
            put(game, 'siren_' + aid, lambda: art(('rr.bb',) if flash else ('bb.rr',)), x - 4, y - 3, 22,
                ['responder', 'siren'], True, key=('siren', flash))
        elif shown.get('vehicle'):
            body = CAR_BODY[seed % len(CAR_BODY)]
            if body == game._theme['ground']:
                body = VIO if body != VIO else MAG
            occupants = shown.get('occupants')
            has_seats = bool(occupants)
            put(game, 'contact_' + aid,
                lambda: art(CAR_SEATS if has_seats else CAR_SOLO, {'B': body, 'D': DARKER.get(body, BLK),
                                                                   'W': LIGHTER.get(body, WHT)}),
                x - 4, y - 3, 20, ['contact', 'traffic_vehicle'], True, key=('car', has_seats, body))
            if has_seats:
                for seat, occupant_id in enumerate(occupants[:4]):
                    occupant = by_id.get(occupant_id)
                    if occupant is None or not occupant.get('alive', False):
                        continue
                    seat_people.append(occupant)
                    ox, oy = ((-2, -1), (1, -1), (-2, 2), (1, 2))[seat]
                    put(game, 'seat_core_' + aid + '_' + str(seat), contact_core(occupant), x + ox, y + oy, 23,
                        ['contact', 'identity', 'vehicle_occupant'], True)
        else:
            last = game._facing.get(aid, 0)
            moved = old.get('observed', old['pos'])[0] != shown.get('observed', shown['pos'])[0]
            if moved:
                last = 1 if shown.get('observed', shown['pos'])[0] > old.get('observed', old['pos'])[0] else -1
                game._facing[aid] = last
            if shown.get('indoors'):
                put(game, 'heat_window_' + aid, brackets(LBL, 6), x - 2, y - 2, 19, ['heat'], True, key='heat')
            legs = (t // 3 + seed) % 2 if moved or phase < 3 else 0
            blink = (t // 2 + seed) % 11 == 0
            skin = PERSON_SKIN[seed % 3]
            hair = PERSON_HAIR[(seed // 3) % 5]
            if hair == skin:
                hair = VIO
            sleeve = PERSON_SLEEVE[(seed // 7) % 5]
            style = (seed // 5) % 3
            mood = 1 if game.ending == 'win' else -1 if game.ending == 'lose' else 0
            small = bool(shown.get('indoors'))
            hop = -1 if mood == 1 and (t // 2 + seed) % 2 else 0            # cheering people hop
            shake = (t // 2) % 2 if mood == -1 and not small else 0          # wincing people shiver
            if small:
                put(game, 'contact_' + aid, lambda: person_pixels(skin, hair, sleeve, last, legs, blink, mood, style, True),
                    x - 1, y - 2 + hop, 20, ['contact'], True, key=('person', skin, hair, sleeve, last, legs, blink, mood, 's'))
            else:
                put(game, 'contact_' + aid, lambda: person_pixels(skin, hair, sleeve, last, legs, blink, mood, style),
                    x - 2 + shake, y - 4 + hop, 20, ['contact'], True,
                    key=('person', skin, hair, sleeve, last, legs, blink, mood, style))
        if not has_seats:
            put(game, 'core_' + aid, core, x, y, 23, ['contact', 'identity'], True)
        ring_size = 12 if has_seats else 10 if (shown['role'] != 'responder' and not shown.get('indoors')) else 8
        dx0, dy0 = HALO[ring_size]
        threat_signal(game, aid, seat_people if has_seats else [shown], x, y, phase, ring_size)
        priority = shown.get('priority') or any(p.get('priority') for p in seat_people)
        if priority:
            glint = (t // 2) % 4 == 0
            put(game, 'priority_' + aid, brackets(WHT, ring_size, YEL if glint else None), x - dx0, y - dy0, 18,
                ['priority'], True, key=('priority', ring_size, glint))
        if game._frozen(shown) or any(game._frozen(p) for p in seat_people):
            put(game, 'frozen_' + aid, brackets(LBL, ring_size, WHT), x - dx0, y - dy0, 25, ['frozen'], True,
                key=('frozen', ring_size))
        if shown.get('injured'):
            put(game, 'injured_' + aid, lambda: art(('..k..', '.kpk.', 'kpppk', '.kpk.', '..k..')), x - 1, y + 3, 18,
                ['injured'], True, key='injured')
        if shown.get('observed_at', game.tick) < game.tick:
            stale = np.full((6, 6), -1, dtype=np.int8)
            stale[0, :2] = stale[-1, -2:] = MAG
            put(game, 'stale_' + aid, stale, x - 1, y - 3, 18, ['stale_track'], True, key='stale')
        elif reacquired and phase < 3:
            put(game, 'reacquire_' + aid, brackets(LBL, 6), x - 2, y - 2, 18, ['reacquired_track'], True, key='ping')


# ───────────────────────────── shots, blasts, fire, craters ─────────────────────────────
def crater_pixels(radius):
    size = radius * 2 + 3
    px = np.full((size, size), -1, dtype=np.int8)
    for row in range(size):
        for col in range(size):
            d = (row - radius - 1) ** 2 + (col - radius - 1) ** 2
            if d <= radius * radius:
                px[row, col] = ORG if mix(row, col, radius) % 11 == 0 else BLK
            elif d <= (radius + 1) ** 2 and (row + col) % 2:
                px[row, col] = MAR
    return px


def draw_craters(game):
    for (x, y), radius in game.craters.items():
        radius = max(1, int(radius))
        put(game, 'crater_%d_%d' % (x, y), lambda: crater_pixels(radius), x - radius - 1, y - radius - 1, -7, ['crater'],
            True, key=('crater', radius))


FIRE_RISE = 4          # how many rows a flame may climb above the burning spot


def fire_pixels(radius, tick, phase):
    """A burning spot: a scorched ring on the ground, then tongues of flame (red base, orange body, yellow tip, a white-hot
    core) that dance higher than the spot is wide, with a few embers lifting off.  The footprint is the same diamond of
    the rules' radius; the flames only rise above it, so nothing about where the fire is changes."""
    side = radius * 2 + 3
    height = side + FIRE_RISE
    flame = np.full((height, side), -1, dtype=np.int8)
    centre = radius + 1
    for col in range(side):
        span = radius + 1 - abs(col - centre)              # half-height of the diamond in this column
        if span < 0:
            continue
        base = FIRE_RISE + centre + span                   # lowest row of this column's flame
        flicker = mix(col, tick, phase // 2) % 3            # how high this tongue licks this moment
        top = FIRE_RISE + centre - span - flicker - (1 if abs(col - centre) < 2 else 0)
        for row in range(max(0, top), min(height, base + 1)):
            reach = (base - row) / max(1, base - top)       # 0 at the foot, 1 at the tip
            flame[row, col] = MAR if reach < 0.12 else RED if reach < 0.4 else ORG if reach < 0.72 else YEL
    for row in range(FIRE_RISE + centre - 1, FIRE_RISE + centre + 1):       # a white-hot core
        flame[row, centre] = WHT if (tick + phase) % 2 else YEL
    for row in range(height):                              # a ragged scorch under the flames
        for col in range(side):
            if flame[row, col] < 0 and row >= FIRE_RISE and abs(col - centre) + abs(row - FIRE_RISE - centre) == radius + 1 \
                    and (row + col + phase) % 2:
                flame[row, col] = MAR
    for number in range(2):                                # embers drifting up
        ex = (mix(number, tick) % side)
        ey = (FIRE_RISE - 1 - (phase + number * 2) // 2) % FIRE_RISE
        if flame[ey, ex] < 0:
            flame[ey, ex] = YEL if number else ORG
    return flame


def draw_fires(game, phase):
    for index, fire in enumerate(game.fires):
        radius = max(1, fire['radius'])
        x, y = fire['pos']
        put(game, 'fire_' + str(index), fire_pixels(radius, game.tick, phase), x - radius - 1,
            y - radius - 1 - FIRE_RISE, 5, ['fire'], True)
    if game.tick < game.slow_until:
        left = game.slow_until - game.tick
        put(game, 'slow_glass', lambda: art(('wwwww', '.ggg.', '..g..', '.ggg.', 'wwwww')), 30, 5, 38, ['slowdown'],
            key='glass')
        put(game, 'slow_duration', [[GRN if i < (left + 1) // 2 else MAR for i in range(6)]], 29, 11, 38, ['slowdown'])
    for index, beacon in enumerate(game.beacons):
        x, y = beacon['pos']
        t = game.tick * FRAME_COUNT + phase
        art_px = brackets(YEL, 7)
        art_px[3, 3] = WHT if (t // 2) % 2 else ORG
        art_px[2:5, 3] = YEL
        art_px[3, 2:5] = YEL
        put(game, 'beacon_' + str(index), art_px, x - 3, y - 3, 6, ['beacon'], True)


def draw_shots(game, phase, frames):
    for index, strike in enumerate(game.pending):
        x, y = strike['pos']
        tool = strike['tool']
        colour = TOOL_COLOUR[tool]
        delay = max(0, strike['due'] - game.tick)
        reticle = brackets(colour, 7, WHT if phase % 2 else colour)
        put(game, 'aim_' + str(index), reticle, x - 3, y - 3, 8, ['pending'], True)
        put(game, 'fuse_' + str(index), [[colour if i < delay else MAR for i in range(4)]], x - 1, y + 4, 8, ['fuse'],
            True)
        travel = max(1, TOOLS[tool]['delay'])
        progress = max(0, min(1, (travel - delay + (phase + 1) / max(1, frames)) / travel))
        picture = art(FLIGHT_PICTURES[tool])
        put(game, 'fall_' + str(index), picture, x + round(10 * (1 - progress)) - picture.shape[1] // 2,
            y - round(12 * (1 - progress)) - picture.shape[0] + 2, 8, ['payload_flight'], True, key=('flight', tool))


BLAST_PAD = 4          # the blast picture is drawn this many pixels bigger than its radius, for rays, sparks and a shock ring


def blast_pixels(radius, phase, frames):
    """The strike: a white flash with rays, then a layered fireball (white-hot, yellow, orange, red rim) ringed by a shock
    wave and flying debris, which cools to red, then to a charred scorch.  The picture is symmetrical about the impact."""
    size = 2 * radius + 2 * BLAST_PAD + 1
    centre = radius + BLAST_PAD
    blast = np.full((size, size), -1, dtype=np.int8)
    last = phase >= frames - 1
    for row in range(size):
        for col in range(size):
            d = ((row - centre) ** 2 + (col - centre) ** 2) ** 0.5
            if phase <= 2:                                  # the flash
                if d <= radius * 0.8 + 0.8:
                    blast[row, col] = WHT
                elif d <= radius + 1.2:
                    blast[row, col] = YEL
            elif not last:                                   # the fireball, hot in the middle
                body = radius + 0.7 - (phase - 3) * 0.35
                if d <= body:
                    inner = d / max(1.0, body)
                    heat = ((YEL, ORG, RED, RED) if phase == 3 else (ORG, RED, RED, MAR))[min(3, int(inner * 4))]
                    blast[row, col] = WHT if (inner < 0.2 and phase == 3) else heat
                elif d <= body + 1.2:
                    blast[row, col] = BLK if phase >= 4 else MAR
            else:                                            # the scorch it leaves
                if d <= radius * 0.9 + 0.5:
                    blast[row, col] = MAR if mix(row, col) % 5 else ORG
                elif d <= radius + 1.3 and mix(row, col) % 3 == 0:
                    blast[row, col] = BLK
    if phase <= 3:                                           # rays and a shock ring, wider as the blast grows
        reach = radius + 2 + (phase - 2)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            length = reach if dx == 0 or dy == 0 else max(1, int(reach * 0.7))
            for step in range(radius, length + 1):
                sx, sy = centre + dx * step, centre + dy * step
                if 0 <= sx < size and 0 <= sy < size and blast[sy, sx] < 0:
                    blast[sy, sx] = WHT if step <= radius + 1 else YEL
    if 3 <= phase < frames - 1:                              # flying debris
        for number in range(7):
            h = mix(number, radius, phase)
            angle = (h % 16) * 0.3927
            span = radius + 2 + (h >> 4) % 2 + (phase - 3)
            sx = centre + int(round(span * np.cos(angle)))
            sy = centre + int(round(span * np.sin(angle)))
            if 0 <= sx < size and 0 <= sy < size and blast[sy, sx] < 0:
                blast[sy, sx] = (BLK, ORG, MAR)[number % 3]
    return blast


def draw_events(game, phase, frames):
    for index, event in enumerate(game.events):
        kind = event['kind']
        if kind == 'switch':
            continue
        x, y = event.get('pos', (0, 0))
        if kind == 'refuse':
            cross = brackets(RED, 7)
            for i in range(1, 6):
                if (i + phase) % 2 == 0:
                    cross[i, i] = cross[i, 6 - i] = RED
            put(game, 'refusal_' + str(index), cross, x - 3, y - 3, 10, ['feedback'], True)
            continue
        if phase < 2:
            continue
        if kind in ('aid', 'beacon'):
            size = min(9, 3 + 2 * (phase - 2))
            colour = GRN if kind == 'aid' else YEL
            support = ring_pixels(colour, size)
            support[size // 2, size // 2] = WHT
            if kind == 'aid' and size >= 5:
                support[size // 2, size // 2 - 1:size // 2 + 2] = WHT
                support[size // 2 - 1:size // 2 + 2, size // 2] = WHT
            put(game, 'support_' + str(index), support, x - size // 2, y - size // 2, 9, ['support_effect'], True)
        else:
            radius = min(max(1, event['radius']), max(1, phase - 1))
            centre = radius + BLAST_PAD
            put(game, 'impact_' + str(index), blast_pixels(radius, phase, frames), x - centre, y - centre, 10,
                ['impact'], True)
            if phase >= 3:                                   # a billow of smoke that swells and climbs
                bulk = min(9, 5 + 2 * (phase - 3))
                put(game, 'smoke_' + str(index), lambda: puff_pixels(bulk), x - bulk // 2,
                    y - 4 - bulk // 2 - 2 * (phase - 3), 11, ['smoke'], True, key=('smoke', bulk))


def puff_pixels(size):
    """One round cloud: white with a pale-blue shaded underside, a black outline and a bright catch-light."""
    px = disc(size, WHT, BLK)
    for row in range(size):
        for col in range(size):
            if px[row, col] == WHT and row + col > size * 1.1:
                px[row, col] = LBL
    px[1:3, 1:3] = np.where(px[1:3, 1:3] == WHT, WHT, px[1:3, 1:3])
    return px


# ───────────────────────────── the console ─────────────────────────────
def pod_pixels(border, fill, selected):
    px = np.full((11, 11), fill, dtype=np.int8)
    px[0, :] = px[-1, :] = border
    px[:, 0] = px[:, -1] = border
    for cx, cy in ((0, 0), (10, 0), (0, 10), (10, 10)):
        px[cy, cx] = -1
    if selected:
        px[1, 1] = px[1, 9] = px[9, 1] = px[9, 9] = YEL
        px[0, 3:8] = YEL
    return px


def draw_console(game, phase):
    t = game.tick * FRAME_COUNT + phase
    put(game, 'hud_top_mask', np.full((4, 64), BLK), 0, 0, 30, ['instrument'], key='top')
    bottom = np.full((12, 64), MAR, dtype=np.int8)
    bottom[0, :] = ORG
    put(game, 'hud_bottom_mask', bottom, 0, 52, 30, ['instrument'], key='bottom')
    remaining = game.remaining_hostiles()
    targets = np.full((4, 29), -1, dtype=np.int8)
    pitch = 4 if game.total_hostiles * 4 <= 29 else 3    # a pixel of air between the faces whenever they fit
    for index in range(min(9, game.total_hostiles)):
        if index < remaining:                              # a scowling raider, horns up, fangs showing
            glyph = art(('r.r', 'krk', 'rrr', '.w.') if (t // 6 + index) % 9 else ('r.r', 'rrr', 'rrr', '.w.'))
        else:                                              # the same one, tamed: a happy green face
            glyph = art(('.g.', 'kgk', 'gwg', '.g.') if (t // 6 + index) % 9 else ('.g.', 'ggg', 'gwg', '.g.'))
        targets[:, index * pitch:index * pitch + 3] = glyph
    put(game, 'mission_targets', targets, 1, 0, 40, ['mission'])
    shield = np.full((4, 12), -1, dtype=np.int8)
    shield_colour = GRN if game.risk > 40 else YEL if game.risk > 20 else RED
    for row, inset in enumerate((0, 1, 2, 4)):
        for col in range(inset, 12 - inset):
            if col in (3, 8) and row < 3:
                continue
            shield[row, col] = shield_colour if game.risk >= (col + 1) * 120 // 12 else MAR
    put(game, 'civilian_condition', shield, 30, 0, 40, ['condition'])
    pressure = np.full((4, 2), -1, dtype=np.int8)
    load = min(4, max(0, (getattr(game, 'response_load', 0) + 1) // 2))
    for row in range(4):
        pressure[3 - row, row % 2] = ORG if row < load else MAR
    put(game, 'response_pressure', pressure, 42, 0, 40, ['response_pressure'])
    threats = [a for a in game.actors if a['alive'] and a['role'] == 'hostile']
    danger = max(threats, key=lambda a: a.get('threat_age', 0) / max(1, a.get('threat_limit', 1)), default=None)
    ratio = 0 if danger is None else min(1, danger.get('threat_age', 0) / max(1, danger.get('threat_limit', 1)))
    stage = 'quiet' if danger is None else danger.get('attack_stage', 'quiet')
    bloom = np.full((4, 10), -1, dtype=np.int8)
    colour = ORG if stage == 'arming' else YEL if stage == 'gather' else LBL
    petals = ((4, 1), (5, 1), (3, 2), (6, 2), (3, 0), (6, 0), (1, 1), (8, 1), (0, 0), (9, 0))
    count = 2 + round(8 * ratio)
    for index, (x, y) in enumerate(petals):
        bloom[y, x] = colour if index < count else MAR
        if y < 3:
            bloom[y + 1, x] = colour if index < count else MAR
    bloom[3, 4:6] = colour
    put(game, 'operation_clock', bloom, 45, 0, 40, ['threat_pressure'])
    eye = YEL if game.stale else LBL
    blinking = (t // 4) % 9 == 0
    lid = (['.eeeee.', 'e.....e', 'e.....e', '.eeeee.'] if blinking else
           ['.eeeee.', 'ewwkwwe', 'ewwkwwe', '.eeeee.'])
    sensor = art(lid, {'e': eye})
    if game.stale:
        sensor[sensor == WHT] = YEL
    put(game, 'sensor_freshness', sensor, 57, 0, 40, ['sensor'])
    selected_tool = game.tools[game.tool_index]
    switched = any(e.get('kind') == 'switch' for e in game.events)
    for index, tool in enumerate(TOOL_ORDER):
        x = 2 + index * 12
        enabled = tool in game.tools
        selected = enabled and tool == selected_tool
        border = WHT if selected else LBL if enabled else MAR
        fill = BLU if selected else BLK
        if getattr(game, 'flash_tool', None) == tool:
            border, fill = RED, MAR
        put(game, 'payload_slot_' + tool, pod_pixels(border, fill, selected), x - 1, 53, 40, ['payload'],
            key=('pod', border, fill, selected))
        icon = art(ICON_PICTURES[tool])
        if not enabled:
            icon[icon >= 0] = MAR
        put(game, 'payload_icon_' + tool, icon, x + 1, 54, 41, ['payload'], key=('icon', tool, enabled))
        stock = game.ammo.get(tool, 0) if enabled else 0
        if enabled and stock < TOOLS[tool]['stock']:
            recharge = PRACTICE_RECHARGE if game.mission_index == 0 else RECHARGE_TURNS
            filled = game.reload_progress[tool] * 6 // recharge
            put(game, 'recharge_' + tool, [[YEL if i < filled else MAR for i in range(6)]], x + 1, 59, 41,
                ['recharge'])
        rounds = np.full((3, 8), -1, dtype=np.int8)
        if tool == 'heavy':
            for n in range(3):
                rounds[:, n * 3] = YEL if n < stock else MAR
                rounds[:, n * 3 + 1] = ORG if n < stock else MAR
        else:
            for n in range(6):
                row, col = (n // 3) * 2, (n % 3) * 3
                rounds[row, col:col + 2] = TOOL_PIP[tool] if n < stock else MAR
        put(game, 'payload_stock_' + tool, rounds, x, 60, 41, ['ammunition'])
        if not enabled:
            put(game, 'payload_locked_' + tool, lambda: art(('.www.', 'w...w', 'yyyyy', 'yykyy', 'yyyyy')), x + 2, 54,
                42, ['locked'], key='padlock')
        if selected and switched and phase < 5:
            orbit = np.full((11, 11), -1, dtype=np.int8)
            points = ((2, 0), (5, 0), (8, 0), (10, 3), (10, 6), (8, 10), (5, 10), (2, 10), (0, 6), (0, 3))
            for offset in (0, 1):
                ox, oy = points[(phase * 2 + offset) % len(points)]
                orbit[oy, ox] = YEL if offset else WHT
            put(game, 'payload_switch_orbit', orbit, x - 1, 53, 43, ['selection_feedback'])
            connector = np.full((1, 60), ORG, dtype=np.int8)
            connector[0, max(0, index * 12 - 2):min(60, index * 12 + 11)] = YEL
            put(game, 'payload_switch_connector', connector, 2, 52, 43, ['selection_feedback'])


def draw_edge_cues(game):
    cx, cy = int(game.camera.x), int(game.camera.y)
    nearest = {}
    for actor in game.actors:
        if not actor['alive'] or actor['role'] != 'hostile':
            continue
        x, y = actor.get('observed', actor['pos'])
        lx, ly = x - cx, y - cy
        if 2 <= lx <= 61 and 4 <= ly <= 50:
            continue
        dx, dy = lx - 32, ly - 28
        if abs(dx) * 22 >= abs(dy) * 30:
            edge = 'left' if dx < 0 else 'right'
            sx = 0 if dx < 0 else 61
            sy = max(7, min(47, round(28 + dy * 30 / max(1, abs(dx)))))
        else:
            edge = 'up' if dy < 0 else 'down'
            sx = max(4, min(57, round(32 + dx * 22 / max(1, abs(dy)))))
            sy = 4 if dy < 0 else 49
        distance = abs(dx) + abs(dy)
        if edge not in nearest or distance < nearest[edge][0]:
            nearest[edge] = (distance, sx, sy, RED if actor.get('confidence') == 4 else YEL)
    shapes = {'left': ('.c.', 'cc.', '.c.'), 'right': ('.c.', '.cc', '.c.'),
              'up': ('.c.', 'ccc', '...'), 'down': ('...', 'ccc', '.c.')}
    for edge, (_, x, y, colour) in nearest.items():
        arrow = art(shapes[edge], {'c': colour})
        put(game, 'bearing_' + edge, arrow, x, y, 35, ['contact_bearing'], key=('arrow', edge, colour))


# ───────────────────────────── feedback: win sparkle, run over ─────────────────────────────
SAD_FACE = ('....kkkkk....', '..kkyyyyykk..', '.kyyyyyyyyyk.', '.kyyyyyyyyyk.', 'kyyykyyykyyyk', 'kyyykyyykyyyk',
            'kyyylyyylyyyk', 'kyyylyyylyyyk', 'kyyyykkkyyyyk', 'kyykkyyykkyyk', '.kyyyyyyyyyk.', '..kkyyyyykk..',
            '....kkkkk....')
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


FIREWORKS = ((13, 15, YEL), (50, 13, LBL), (31, 31, ORG), (12, 38, GRN), (51, 36, PNK))
SHOWER = (YEL, WHT, LBL, PNK, ORG, GRN, MAG, VIO, RED)


def cloud_pixels():
    """A storm cloud for a lost run: violet body, a lit pink top edge, a black outline (round blobs, one picture)."""
    w, h = 28, 11
    body = np.zeros((h, w), dtype=bool)
    for cx, cy, r in ((6, 6, 4.5), (12, 4.5, 5), (19, 5, 5), (23, 7, 4), (14, 7, 5)):
        for row in range(h):
            for col in range(w):
                if (col - cx) ** 2 + (row - cy) ** 2 <= r * r:
                    body[row, col] = True
    px = np.full((h, w), -1, dtype=np.int8)
    for row in range(h):
        for col in range(w):
            if body[row, col]:
                px[row, col] = MAG if row == 0 or not body[row - 1, col] else VIO
    for row in range(h):
        for col in range(w):
            if not body[row, col] and any(0 <= row + dy < h and 0 <= col + dx < w and body[row + dy, col + dx]
                                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[row, col] = BLK
    return px


def draw_feedback(game, phase):
    if game.ending == 'win' and phase >= 1:
        # a shower of confetti and five fireworks; the shower keeps falling while the curtain closes (outro_phase)
        shower = phase + (game.outro_phase + 1) * 2 if game.outro_phase >= 0 else phase
        for number in range(16):
            h = mix(game.mission_index, number, 7)
            x = 3 + h % 58
            y = 4 + ((h >> 8) % 44 + shower * (2 + number % 3)) % 46
            colour = SHOWER[(number + shower // 2) % len(SHOWER)]
            piece = [[colour, colour]] if (shower + number) % 2 else [[colour], [colour]]
            put(game, 'win_confetti_' + str(number), piece, x, y, 52, ['win_sparkle'])
        for number, (bx, by, colour) in enumerate(FIREWORKS):
            age = shower - 1 - number
            if not 0 <= age <= 6:
                continue
            reach = age + 1
            spark = np.full((13, 13), -1, dtype=np.int8)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                for ring in (reach, reach // 2) if reach >= 4 else (reach,):
                    sx, sy = 6 + dx * ring, 6 + dy * ring
                    if 0 <= sx < 13 and 0 <= sy < 13:
                        spark[sy, sx] = colour if age < 4 else (WHT if (dx + dy) % 2 else colour)
            spark[6, 6] = WHT if age < 2 else -1
            put(game, 'win_firework_' + str(number), spark, bx - 6, by - 6, 53, ['win_sparkle'])
        for number in range(9):
            h = mix(game.mission_index, number)
            x = 5 + h % 54
            y = 8 + (h >> 8) % 38
            size = min(7, 1 + 2 * phase // 2 + 1) if (phase + number) % 2 else min(5, phase + 1)
            size += 1 - size % 2                               # odd sizes so the cross has a centre
            colour = (YEL, WHT, LBL, PNK, ORG, GRN, MAG, YEL, WHT)[(number + phase) % 9]
            star = np.full((size, size), -1, dtype=np.int8)
            star[size // 2, :] = colour
            star[:, size // 2] = colour
            star[size // 2, size // 2] = WHT
            if size >= 5:                                      # a diamond glint on the arms of the bigger stars
                star[size // 2 - 1, size // 2 - 1] = star[size // 2 + 1, size // 2 + 1] = colour
                star[size // 2 - 1, size // 2 + 1] = star[size // 2 + 1, size // 2 - 1] = colour
            put(game, 'win_star_' + str(number), star, x - size // 2, y - size // 2, 50, ['win_sparkle'])
        burst = np.full((11, 11), -1, dtype=np.int8)           # one big golden starburst in the middle of the field
        reach = min(5, 1 + phase)
        for d in range(-reach, reach + 1):
            burst[5 + d, 5] = burst[5, 5 + d] = YEL if abs(d) < 3 else ORG
            if abs(d) <= reach // 2 + 1:
                burst[5 + d, 5 + d] = burst[5 + d, 5 - d] = WHT if abs(d) < 2 else YEL
        burst[4:7, 4:7] = WHT
        put(game, 'win_burst', burst, 26, 19, 51, ['win_sparkle'])
    if game.ending == 'lose' and phase >= 1:
        level = min(2, phase)                              # a light red haze that never hides the wincing faces
        tint = np.full((48, 64), -1, dtype=np.int8)
        for row in range(48):
            for col in range(64):
                if BAYER[row % 4][col % 4] < level * 3:
                    tint[row, col] = MAR if (row + col) % 3 else RED
        put(game, 'loss_tint', tint, 0, 4, 50, ['run_over'])
        if phase >= 2:
            put(game, 'loss_cloud', cloud_pixels, 18, 5, 54, ['run_over'], key='cloud')
            for number in range(14):                       # rain falling out of the cloud over the whole field
                h = mix(game.mission_index, number, 3)
                x = 4 + h % 56
                y = 14 + ((h >> 8) % 36 + phase * (3 + number % 3) * 3) % 36
                put(game, 'loss_rain_' + str(number), [[WHT], [LBL], [BLU]], x, y, 52, ['run_over'])
            if phase % 2:                                  # a flash of lightning under the cloud
                put(game, 'loss_bolt', lambda: art(('..yy', '.yy.', 'yyyy', '..y.', '.y..', 'y...')), 38, 14, 54, ['run_over'],
                    key='bolt')
            put(game, 'loss_face', lambda: art(SAD_FACE), 25, 20, 55, ['run_over'], key='sad')
        if phase >= 3:
            put(game, 'loss_tear', [[LBL], [LBL]], 28 if phase % 2 else 29, 27 + phase, 56, ['run_over'])


def art_transition(game, phase):
    """The curtain between missions: gold-fringed curtains close on a star burst, and open again on the next mission."""
    phase = max(0, min(4, int(phase)))
    overlay = np.full((48, 64), -1, dtype=np.int8)
    width = (0, 15, 30, 20, 6)[phase]
    if width:
        for col in range(width):
            overlay[:, col] = MAR if col % 3 else RED
            overlay[:, 63 - col] = MAR if col % 3 else RED
        overlay[::2, width - 1] = YEL
        overlay[1::2, width - 1] = ORG
        overlay[::2, 64 - width] = ORG
        overlay[1::2, 64 - width] = YEL
    if phase < 3:
        radius = (10, 7, 3)[phase]
        for row in range(24 - radius - 2, 24 + radius + 3):
            for col in range(32 - radius - 2, 32 + radius + 3):
                distance = abs(row - 24) + abs(col - 32)
                if distance in (radius, radius + 1):
                    overlay[row, col] = YEL if (row + col) % 2 else WHT
        for side in (-1, 1):
            x = 32 + side * (radius + 3)
            overlay[22:27, x] = YEL
            overlay[21, x - side] = overlay[27, x - side] = ORG
        for number in range(8):                            # sparks round the burst
            h = mix(number, phase)
            overlay[(h >> 4) % 44, 20 + h % 24] = (WHT, YEL, PNK, LBL)[number % 4]
    else:
        sweep = 15 if phase == 3 else 34
        overlay[sweep, width:64 - width] = YEL
        overlay[sweep + 1, width:64 - width:3] = ORG
        for number in range(6):
            h = mix(number, phase)
            overlay[(h >> 4) % 44, width + h % max(1, 64 - 2 * width)] = (WHT, LBL, PNK)[number % 3]
    put(game, 'mission_transition', overlay, 0, 4, 60, ['mission_transition'])


# ───────────────────────────── one picture of the whole world ─────────────────────────────
def draw_world(game, phase):
    theme = game._theme
    t = game.tick * FRAME_COUNT + phase
    tree_kind, canopy, high, fruit = theme['tree']
    for building in game.buildings:
        x, y, w, h = building['rect']
        kind, integrity, bid = building['kind'], building['integrity'], building['id']
        variant = name_seed(bid) % 3
        put(game, 'building_' + bid, lambda: roof_pixels(kind, w, h, integrity, theme, variant), x, y, -5,
            ['building', kind], True, key=('roof', kind, w, h, integrity, game.mission_index, variant))
        if kind == 'courtyard':
            continue
        if integrity > 0:
            dx, dy = building['door']
            put(game, 'door_' + bid, lambda: art(('ww', 'kk')), dx, dy, -3, ['door'], True, key='door')
            seed = name_seed(bid)
            if kind == 'hospital':
                big = w >= 8 and h >= 8
                cross = ('..p..', '..p..', 'ppppp', '..p..', '..p..') if big else ('.p.', 'ppp', '.p.')
                put(game, 'roof_mark_' + bid, lambda: art(cross), x + (w - len(cross[0])) // 2,
                    y + (h - len(cross)) // 2 + (0 if big else 0), -2, ['building_mark'], True, key=('cross', big))
            elif kind == 'school':
                put(game, 'roof_mark_' + bid, lambda: flag_pixels((t // 4) % 2), x + w - 6, y + 1, -2,
                    ['building_mark'], True, key=('flag', (t // 4) % 2))
            elif kind == 'station':
                put(game, 'roof_mark_' + bid, lambda: siren_pixels((t // 2) % 2), x + w // 2 - 1, y + h // 2, -2,
                    ['building_mark'], True, key=('siren', (t // 2) % 2))
            elif kind == 'depot' and w >= 10:
                put(game, 'roof_mark_' + bid, lambda: art(SMALL_PICTURES['crate'][0]), x + w - 6, y + 2, -2,
                    ['building_mark'], True, key='crate')
            elif kind == 'home' and seed % 3 == 0 and w >= 8 and h >= 6:
                put(game, 'chimney_smoke_' + bid, lambda: smoke_column((t // 3) % 3), x + w - 5, y - 4, 12,
                    ['smoke_chimney'], True, key=('chimney', (t // 3) % 3))
            if integrity == 1:
                put(game, 'burning_' + bid, lambda: smoke_column((t // 2) % 3), x + w // 2 - 2, y + h // 2 - 6, 12,
                    ['smoke_chimney'], True, key=('burn', (t // 2) % 3))
    for name, kind, x, y, layer, tags in game._props:
        seed = name_seed(name)
        if kind == 'tree':
            lean = ((t // 5) + seed) % 2
            put(game, name, lambda: tree_pixels(tree_kind, canopy, high, fruit, lean), x, y, layer, tags, True,
                key=('tree', tree_kind, canopy, high, fruit, lean))
        elif kind == 'fountain':
            jet = (t // 2) % 3
            put(game, name, lambda: fountain_pixels(jet), x, y, layer, tags, True, key=('fountain', jet))
        elif kind in PLAZAS:
            frame = (t // 4 + seed) % 2
            put(game, name, lambda: art(PLAZAS[kind][frame]), x, y, layer, tags, True, key=('plaza', kind, frame))
        elif ':' in kind:                                   # a landmark: 'wide:name' or 'thin:name'
            label, which = kind.split(':')
            frame = (t // 6 + seed) % 2
            pictures = (LANDMARKS if label == 'wide' else LANDMARKS_NARROW)[which]
            put(game, name, lambda: art(pictures[frame]), x, y, layer, tags, True, key=('landmark', kind, frame))
        else:
            frame = (t // 7 + seed) % 2
            put(game, name, lambda: small_art(kind, theme, frame), x, y, layer, tags, True,
                key=('small', kind, game.mission_index, frame % len(SMALL_PICTURES[kind])))
    for number, (name, kind, colour, x, y) in enumerate(game._decos):          # the ground scatter twinkles and sways
        frame = (t // 9 + number) % 2
        put(game, name, lambda: art(DECO_PICTURES[kind][frame], {'A': colour}), x, y, -10, ['decoration'], True,
            key=('deco', kind, colour, frame))
    for name, kind, x, y, seed in game._critters:                              # little animals: blink, hop, wander a step
        step = t // 7 + seed
        frame = step % 2
        wander = (0, 1, 2, 2, 1, 0, 0, 0)[(step // 3) % 8]
        put(game, name, lambda: art(CRITTERS[kind][frame]), x + wander, y - (1 if frame and step % 4 == 1 else 0), -8,
            ['critter'], True, key=('critter', kind, frame))
    draw_craters(game)
    row = (game.tick * 3 + phase) % 48
    scan = np.full((1, 60), -1, dtype=np.int8)
    scan[0, ::3] = theme['mark'] if theme['mark'] != theme['ground'] else WHT
    put(game, 'sensor_scan', scan, int(game.camera.x) + 2, int(game.camera.y) + 4 + row, -1, ['sensor_texture'],
        True, key=('scan', theme['mark']))
    draw_drift(game, phase)


def art_frame(game, phase, frames):
    game._used = set(game._static)
    if not hasattr(game, '_facing'):
        game._facing = {}
    draw_world(game, phase)
    draw_fires(game, phase)
    draw_shots(game, phase, frames)
    draw_events(game, phase, frames)
    draw_contacts(game, phase)
    draw_console(game, phase)
    draw_edge_cues(game)
    draw_feedback(game, phase)
    for name in list(game._sprites):
        if name not in game._used:
            game.current_level.remove_sprite(game._sprites.pop(name))
            game._shown.pop(name, None)
