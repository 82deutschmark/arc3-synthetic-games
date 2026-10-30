# ARC-AGI-3 candidate task lt02.py.

from __future__ import annotations
from copy import deepcopy
from collections import deque
import numpy as np
from arcengine import ARCBaseGame, Camera, GameAction, Level, Sprite


def block(colour: int, cell: int = 4) -> list[list[int]]:
    return [[colour] * cell for _ in range(cell)]

def rounded(colour: int, cell: int = 4) -> list[list[int]]:
    px = block(colour, cell)
    for (y, x) in ((0, 0), (0, cell - 1), (cell - 1, 0), (cell - 1, cell - 1)):
        px[y][x] = -1
    return px

def ring(colour: int, cell: int = 4) -> list[list[int]]:
    px = block(colour, cell)
    for y in range(1, cell - 1):
        for x in range(1, cell - 1):
            px[y][x] = -1
    return px

def pips(colour: int, count: int, cell: int = 6) -> list[list[int]]:
    px = [[-1] * cell for _ in range(cell)]
    if count <= 0:
        return px
    n = 0
    for y in range(cell - 2, 0, -1):
        for x in range(1, cell - 1):
            if n >= count:
                return px
            px[y][x] = colour
            n += 1
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
RECHARGE_TURNS = 10
MISSION_TARGETS = (1,2,3,4,5,6,7,8,9)
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
    tools=['heavy'] if index==0 else ['heavy','precision']
    if index>=2: tools+=['beacon']
    if index>=5: tools=['heavy','precision','fire','aid','beacon']
    return dict(buildings=buildings,roads=roads,actors=actors,tools=tools,
                time_limit=(190,210,260,290,320,350,390,440)[index],
                sensor_period=3 if index>=6 else 1, initial_incident=index>=5)


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
    'time_limit','sensor_period','tick','risk','total_hostiles','pending','fires','beacons',
    'events','incidents','ledger','stale','flash_tool','ending','before_actors',
    'view_x','view_y','before_view','mission_index','blocked_cells','response_load')


class Lt02(ARCBaseGame):
    def __init__(self):
        self._mission_number=None;self._mission_entry=None
        self.world_width=WORLD_WIDTH;self.world_height=WORLD_HEIGHT
        super().__init__(game_id='lt02', levels=[Level(sprites=[],grid_size=(64,64),
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
            self.actors=[a for a in self.actors if a['role']!='hostile']
            survivors={a['id'] for a in self.actors}
            for a in self.actors:
                a['ride_target']=None
                a['occupants']=[key for key in a.get('occupants',[]) if key in survivors]
            self.response_load=0
            ward=MISSION_WARDS[index];offset=((ward%2)*64,(ward//2)*52)
            spec=build_district(min(index,7))
            enemies=[a for a in spec['actors'] if a['role']=='hostile'][:MISSION_TARGETS[index]]
            if index==0:
                enemies=[actor('h0','hostile',line_route([(29,21),(37,21),(29,21)]))]
            for number,a in enumerate(enemies):
                target_ward=ward if index<8 else (number%6)%4
                shift=offset if index<8 else ((target_ward%2)*64,(target_ward//2)*52)
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
                a.update(threat_age=0,threat_limit=100+index*12+number*14,attack_stage='quiet')
                self.actors.append(offset_actor(a,shift,f'm{index}_'))
            if index>=2:
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
            unlocked={'heavy','precision'}
            if index>=2:unlocked.add('beacon')
            if index>=3:unlocked.add('aid')
            if index>=4:unlocked.add('fire')
            self.tools=[t for t in TOOL_ORDER if t in unlocked];self.tool_index=0
            self.view_x,self.view_y=MISSION_VIEWS[index]
            self.ammo={name:TOOLS[name]['stock'] for name in TOOL_ORDER}
            self.reload_progress={name:0 for name in TOOL_ORDER}
            self.time_limit=spec['time_limit']+100 if index<8 else 700
            self.sensor_period=spec['sensor_period'];self.tick=0;self.risk=100
            self.total_hostiles=self.remaining_hostiles()
            self.pending=[];self.fires=[];self.beacons=[];self.events=[];self.incidents=[]
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
        city_art_init(self);city_art_frame(self,FRAME_COUNT-1,FRAME_COUNT)
        if self.intro_frames:city_art_transition(self,3)

    def _rebuild_collision(self):
        self.blocked_cells=set()
        for b in self.buildings:
            if b['kind']=='courtyard' or b['integrity']<=0:continue
            x,y,w,h=b['rect']
            self.blocked_cells.update((xx,yy) for xx in range(x,x+w) for yy in range(y,y+h))

    def screen_position(self, point):
        return point[0]-self.view_x,point[1]-self.view_y

    def _paint_frame(self):
        fraction=(self.frame_index+1)/FRAME_COUNT
        self.camera.x=round(self.before_view[0]+(self.view_x-self.before_view[0])*fraction)
        self.camera.y=round(self.before_view[1]+(self.view_y-self.before_view[1])*fraction)
        city_art_frame(self,self.frame_index,FRAME_COUNT)

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

    def _move(self):
        for a in self.actors:
            if not a['alive'] or a['injured'] or a.get('onboard') or a.get('ride_target'): continue
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
            self.fires=[f for f in self.fires if not self._near(f['pos'],pos,radius)]
            for incident in self.incidents:
                if self._near(incident['pos'],pos,radius) and not incident['resolved']:
                    incident['resolved']=True;self.ledger['aided']+=1
            for a in self.actors:
                if a['alive'] and a.get('gather_until') and self._near(a['pos'],pos,12):
                    a['route']=self._street_path(a['pos'],pos);a['index']=0
                    a['gather_until']=self.tick+8;self.ledger['aided']+=1
                if a['alive'] and a['injured'] and self._near(a['pos'],pos,radius):
                    a['injured']=False;self.ledger['aided']+=1
        elif tool=='beacon':
            self.beacons.append(dict(pos=pos,until=self.tick+9))
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
        if self.mission_index==0:return
        for target in self.actors:
            if target['role']!='hostile' or not target['alive']:continue
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
                if 54<=y<=63:
                    i=int(x)//12
                    if 0<=i<len(TOOL_ORDER):self.flash_tool=TOOL_ORDER[i]
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
        self._move()
        for fire in self.fires:
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
        self._threats()
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
        if self.mission_index>0 and self.risk<=0:self.ending='lose'
        elif not self.remaining_hostiles() and not self.pending and not self.fires and not unresolved: self.ending='win'

    def step(self):
        if self.action.id==GameAction.RESET:
            self.complete_action();return
        if self.intro_frames:
            self.intro_frames-=1;city_art_frame(self,FRAME_COUNT-1,FRAME_COUNT)
            if self.intro_frames:city_art_transition(self,4)
            else:self.complete_action()
            return
        if self.outro_phase>=0:
            self.outro_phase+=1;city_art_frame(self,FRAME_COUNT-1,FRAME_COUNT)
            city_art_transition(self,self.outro_phase)
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
                    self.outro_phase=0;city_art_transition(self,0)
                else:self.complete_action()
            return
        action=self.action.id.value
        if action not in (1,2,3,4,5,6,7):self.complete_action();return
        self._world_tick(action,self.action.data or {})
        self.frame_index=0;self.animating=True;self._paint_frame()


def _city_put(game, name, pixels, x, y, layer=0, tags=(), field=False):
    pixels = np.asarray(pixels, dtype=np.int8)
    x, y = int(x), int(y)
    if layer >= 30:
        x += int(game.camera.x)
        y += int(game.camera.y)
    if field:
        left, top = max(0, x), max(0, y)
        right = min(game.world_width, x + pixels.shape[1])
        bottom = min(game.world_height, y + pixels.shape[0])
        if right <= left or bottom <= top:
            return
        pixels = pixels[top-y:bottom-y, left-x:right-x]
        x, y = left, top
    sprite = game._city_sprites.get(name)
    if sprite is None:
        sprite = Sprite(pixels=pixels, name=name, x=x, y=y, layer=layer,
                        collidable=False, tags=list(tags))
        game.current_level.add_sprite(sprite)
        game._city_sprites[name] = sprite
    else:
        sprite.pixels = pixels
        sprite.set_position(x, y)
        sprite.set_layer(layer)
        sprite.tags[:] = list(tags)
    game._city_used.add(name)
    return sprite


def _city_brackets(colour, size=8):
    pixels = np.full((size, size), -1, dtype=np.int8)
    for x, y in ((0, 0), (size-1, 0), (0, size-1), (size-1, size-1)):
        pixels[y, x] = colour
        pixels[y, x + (1 if x == 0 else -1)] = colour
        pixels[y + (1 if y == 0 else -1), x] = colour
    return pixels


def _city_roof(building):
    _, _, width, height = building['rect']
    if building['kind']=='courtyard':
        pixels=np.full((height,width),5,dtype=np.int8)
        pixels[::3,:]=4;pixels[:,::4]=4
        pixels[1::3,1::4]=3
        return pixels
    pixels = np.full((height, width), 3, dtype=np.int8)
    pixels[0, :] = 2
    pixels[-1, :] = 4
    pixels[:, 0] = 2
    pixels[:, -1] = 4
    pixels[0, 0] = pixels[0, -1] = pixels[-1, 0] = pixels[-1, -1] = -1
    for row in range(2, height-2, 3):
        for col in range(2, width-2, 4):
            pixels[row:row+1, col:col+2] = 4
    if width >= 8 and height >= 6:
        pixels[2:4, width-4:width-2] = [[1, 2], [2, 4]]
    if building['integrity'] < 3:
        for row in range(1, height-1):
            pixels[row, 1 + (row*3) % max(1, width-2)] = 5
    if building['integrity'] <= 0:
        for row in range(height):
            for col in range(width):
                pixels[row, col] = 4 if (row*7+col*11) % 5 < 3 else -1
    return pixels


def city_art_init(game):
    for sprite in list(game.current_level.get_sprites()):
        game.current_level.remove_sprite(sprite)
    game._city_sprites = {}
    game._city_used = set()
    _city_put(game, 'city_ground', np.full((game.world_height, game.world_width), 5),
              0, 0, -20, ['terrain'])
    for index, (x, y, width, height) in enumerate(game.roads):
        road = np.full((height, width), 4, dtype=np.int8)
        if width > height:
            road[height//2, 2::6] = 3
        else:
            road[2::6, width//2] = 3
        _city_put(game, 'road_'+str(index), road, x, y, -12, ['road'], True)
    tree = pixel_art(('.aa.', 'abba', '.aa.', '..b.'), {'a': 4, 'b': 3})
    parked = pixel_art(('.aaa.', 'ababa', '.aaa.'), {'a': 3, 'b': 2})
    for index, building in enumerate(game.buildings):
        x, y, width, height = building['rect']
        if index % 2 == 0:
            _city_put(game, 'tree_'+str(index), tree, x+width-2, y+height+1,
                      -9, ['decoration'], True)
        else:
            _city_put(game, 'parked_'+str(index), parked, x+1, y-3,
                      -9, ['decoration'], True)
        if building['kind'] == 'school':
            playground = np.full((3, max(4, width-2)), -1, dtype=np.int8)
            playground[0, :] = 4
            playground[-1, :] = 4
            playground[:, 0] = playground[:, -1] = 4
            playground[:, playground.shape[1]//2] = 3
            _city_put(game, 'playground_'+building['id'], playground,
                      x+1, y+height+1, -8, ['school_court'], True)
    game._city_static = set(game._city_used)
    game._city_building_cache = {}
    game._city_crater_cache = {}


def _city_contact_art(actor):
    confidence = max(0, min(4, actor.get('confidence', 0)))
    if actor.get('traffic') and actor['role'] == 'civilian':
        core = [11]*4
    elif actor['role'] == 'civilian' and actor.get('indoors'):
        core = [14]*4
    elif confidence == 4:
        colour = 8 if actor['role'] == 'hostile' else 14
        core = [colour]*4
    else:
        core = [8]*confidence + [11]*(4-confidence)
    pixels = np.array([[-1, 3, 3, -1],
                       [3, core[0], core[1], 3],
                       [3, core[2], core[3], 3],
                       [3, -1, -1, 3]], dtype=np.int8)
    return pixels


def _city_payload_icon(tool):
    patterns = {
        'heavy': (('..aaa..', '.abbba.', 'aabbbaa', '..a.a..'), {'a':12,'b':11}),
        'precision': (('...a...', '...b...', '..aba..', 'aa...aa'), {'a':10,'b':0}),
        'fire': (('...a...', '..aba..', '.ababa.', '..bbb..'), {'a':12,'b':8}),
        'aid': (('...a...', '..aaa..', '...a...', '.b...b.'), {'a':14,'b':10}),
        'beacon': (('..aaa..', '.a.b.a.', '..aaa..', '...a...'), {'a':15,'b':10}),
    }
    rows, colours = patterns[tool]
    return pixel_art(rows, colours)


def _city_instruments(game, phase=5):
    _city_put(game, 'hud_top_mask', np.full((4, 64), 5), 0, 0, 30, ['instrument'])
    _city_put(game, 'hud_bottom_mask', np.full((12, 64), 5), 0, 52, 30, ['instrument'])
    targets = np.full((4, 27), -1, dtype=np.int8)
    remaining = game.remaining_hostiles()
    for index in range(min(9, game.total_hostiles)):
        colour = 8 if index < remaining else 14
        glyph = pixel_art(('a.a', '.a.', 'a.a', '.b.'), {'a':colour, 'b':3})
        targets[:, index*3:index*3+3] = glyph
    _city_put(game, 'mission_targets', targets, 1, 0, 40, ['mission'])
    shield = np.full((4, 12), -1, dtype=np.int8)
    shield_colour = 14 if game.risk > 40 else 11 if game.risk > 20 else 8
    for row, inset in enumerate((0, 1, 2, 4)):
        for col in range(inset, 12-inset):
            if col in (3, 8) and row < 3:
                continue
            threshold = (col+1)*100//12
            shield[row, col] = shield_colour if game.risk >= threshold else 4
    _city_put(game, 'civilian_condition', shield, 30, 0, 40, ['condition'])
    pressure = np.full((4, 2), -1, dtype=np.int8)
    load = min(4, max(0, (getattr(game, 'response_load', 0)+1)//2))
    for row in range(4):
        pressure[3-row, row%2] = 7 if row < load else 4
    _city_put(game, 'response_pressure', pressure, 42, 0, 40, ['response_pressure'])
    threats = [actor for actor in game.actors if actor['alive'] and actor['role'] == 'hostile']
    danger = max(threats, key=lambda actor: actor.get('threat_age', 0)/max(1, actor.get('threat_limit', 1)), default=None)
    ratio = 0 if danger is None else min(1, danger.get('threat_age', 0)/max(1, danger.get('threat_limit', 1)))
    stage = 'quiet' if danger is None else danger.get('attack_stage', 'quiet')
    bloom = np.full((4,10), -1, dtype=np.int8)
    colour = 12 if stage == 'arming' else 11 if stage == 'gather' else 2
    petals = ((4,1),(5,1),(3,2),(6,2),(3,0),(6,0),(1,1),(8,1),(0,0),(9,0))
    count = 2 + round(8*ratio)
    for index, (x,y) in enumerate(petals):
        bloom[y,x] = colour if index < count else 4
        if y < 3:
            bloom[y+1,x] = colour if index < count else 4
    bloom[3,4:6] = colour
    _city_put(game, 'operation_clock', bloom, 45, 0, 40, ['threat_pressure'])
    sensor_colour = 11 if game.stale else 10
    sensor = pixel_art(('.a...a.', 'a..b..a', 'a..b..a', '.a...a.'),
                       {'a':sensor_colour, 'b':4 if game.stale else 0})
    _city_put(game, 'sensor_freshness', sensor, 57, 0, 40, ['sensor'])
    selected_tool = game.tools[game.tool_index]
    switched = any(event.get('kind') == 'switch' for event in game.events)
    for index, tool in enumerate(TOOL_ORDER):
        x = 2 + index*12
        enabled = tool in game.tools
        selected = enabled and tool == selected_tool
        colour = 0 if selected else 3 if enabled else 4
        if getattr(game, 'flash_tool', None) == tool:
            colour = 8
        pod = np.full((10, 11), -1, dtype=np.int8)
        pod[0, 2:9] = pod[9, 2:9] = colour
        pod[1, 1] = pod[1, 9] = pod[8, 1] = pod[8, 9] = colour
        pod[2:8, 0] = pod[2:8, 10] = colour
        if selected:
            pod[3:7, 1] = pod[3:7, 9] = 10
            pod[0, 4:7] = 11
        _city_put(game, 'payload_slot_'+tool, pod, x-1, 53, 40, ['payload'])
        icon = np.asarray(_city_payload_icon(tool), dtype=np.int8)
        if not enabled:
            icon[icon >= 0] = 4
        _city_put(game, 'payload_icon_'+tool, icon, x+1, 54, 41, ['payload'])
        stock = game.ammo.get(tool, 0) if enabled else 0
        if enabled and stock < TOOLS[tool]['stock']:
            recharge = PRACTICE_RECHARGE if game.mission_index == 0 else RECHARGE_TURNS
            filled = game.reload_progress[tool]*6//recharge
            charge=[10 if i < filled else 4 for i in range(6)]
            _city_put(game, 'recharge_'+tool, [charge], x+2, 58, 41, ['recharge'])
        rounds = np.full((3, 8), -1, dtype=np.int8)
        if tool == 'heavy':
            for count in range(3):
                rounds[:, count*3:count*3+2] = 11 if count < stock else 4
        else:
            for count in range(6):
                row, col = (count//3)*2, (count%3)*3
                rounds[row, col:col+2] = 10 if count < stock else 4
        _city_put(game, 'payload_stock_'+tool, rounds, x+1, 59, 41, ['ammunition'])
        if not enabled:
            _city_put(game, 'payload_locked_'+tool, [[3,3,3]], x+3, 58, 42, ['locked'])
        if selected and switched and phase < 5:
            orbit = np.full((10, 11), -1, dtype=np.int8)
            points = ((2,0),(5,0),(8,0),(10,3),(10,6),(8,9),(5,9),(2,9),(0,6),(0,3))
            for offset in (0,1):
                ox,oy = points[(phase*2+offset)%len(points)]
                orbit[oy,ox] = 11 if offset else 10
            _city_put(game, 'payload_switch_orbit', orbit, x-1, 53, 43, ['selection_feedback'])
            connector = np.full((1, 60), 4, dtype=np.int8)
            connector[0, max(0,index*12-2):min(60,index*12+11)] = 10
            _city_put(game, 'payload_switch_connector', connector, 2, 52, 43, ['selection_feedback'])


def _city_contact_position(actor, previous, tick, phase):
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
        lengths.append(abs(a[0]-b[0])+abs(a[1]-b[1]))
    distance = min(1, (phase+1)/3) * sum(lengths)
    for a, b, length in zip(points, points[1:], lengths):
        if distance <= length and length:
            fraction = distance/length
            return tuple(round(v+(w-v)*fraction) for v,w in zip(a,b)), False
        distance -= length
    return end, False


def city_art_frame(game, phase, frames):
    game._city_used = set(game._city_static)
    for building in game.buildings:
        state = (tuple(building['rect']), tuple(building['door']), building['kind'], building['integrity'])
        cached = game._city_building_cache.get(building['id'])
        if cached is not None and cached[0] == state:
            game._city_used.update(cached[1])
            continue
        previous_names = set(game._city_used)
        x, y, width, height = building['rect']
        _city_put(game, 'building_'+building['id'], _city_roof(building),
                  x, y, -5, ['building', building['kind']], True)
        dx, dy = building['door']
        _city_put(game, 'door_'+building['id'], [[1, 1], [5, 5]],
                  dx, dy, -3, ['door'], True)
        if building['integrity'] > 0:
            if building['kind'] == 'hospital':
                sign = pixel_art(('.g.', 'ggg', '.g.'), {'g': 1})
            elif building['kind'] == 'school':
                sign = pixel_art(('g.g', 'ggg', 'g.g'), {'g': 2})
            elif building['kind'] == 'station':
                sign = pixel_art(('c.c', '.c.', 'c.c'), {'c': 2})
            elif building['kind'] == 'depot':
                sign = pixel_art(('www', 'w.w', 'www'), {'w': 2})
            else:
                sign = [[2, 4], [4, 2]]
            _city_put(game, 'roof_mark_'+building['id'], sign,
                      x+2, y+2, -2, ['building_mark'], True)
        game._city_building_cache[building['id']] = (state, game._city_used-previous_names)
    _city_craters(game)
    scan = np.full((48, 60), -1, dtype=np.int8)
    scan_row = (game.tick*3 + phase) % 48
    scan[scan_row, ::3] = 3
    for index in range(13):
        sx = (index*19 + game.tick*7 + phase*3) % 60
        sy = (index*13 + game.tick*5) % 48
        scan[sy, sx] = 4
    _city_put(game, 'sensor_scan', scan, int(game.camera.x)+2, int(game.camera.y)+4,
              -1, ['sensor_texture'])
    for index, fire in enumerate(game.fires):
        radius = max(1, fire['radius'])
        side = radius*2+3
        flame = np.full((side, side), -1, dtype=np.int8)
        for row in range(side):
            for col in range(side):
                distance = abs(col-radius-1)+abs(row-radius-1)
                if distance <= radius:
                    flame[row, col] = 12 if (row+col+game.tick+phase)%5 == 0 else 4
                elif distance == radius+1 and (row+col+phase)%2:
                    flame[row, col] = 3
        x, y = fire['pos']
        _city_put(game, 'fire_'+str(index), flame, x-radius-1, y-radius-1,
                  5, ['fire'], True)
    for index, beacon in enumerate(game.beacons):
        x, y = beacon['pos']
        art = _city_brackets(2, 7)
        art[3, 3] = 11
        _city_put(game, 'beacon_'+str(index), art, x-3, y-3, 6, ['beacon'], True)
    for index, strike in enumerate(game.pending):
        x, y = strike['pos']
        colour = {'heavy':12, 'precision':1, 'fire':12, 'aid':2, 'beacon':11}[strike['tool']]
        _city_put(game, 'aim_'+str(index), _city_brackets(colour, 7),
                  x-3, y-3, 8, ['pending'], True)
        delay = max(0, strike['due']-game.tick)
        _city_put(game, 'fuse_'+str(index), [[colour if i<delay else 4 for i in range(4)]],
                  x-1, y+4, 8, ['fuse'], True)
        travel = max(1, TOOLS[strike['tool']]['delay'])
        progress = max(0, min(1, (travel-delay+(phase+1)/max(1,frames))/travel))
        flight_x = x+round(10*(1-progress))
        flight_y = y-round(12*(1-progress))
        flight = pixel_art(('c.', 'cc', '.w'), {'c':colour, 'w':0})
        _city_put(game, 'fall_'+str(index), flight,
                  flight_x, flight_y, 8, ['payload_flight'], True)
    for index, event in enumerate(game.events):
        kind = event['kind']
        if kind == 'switch':
            continue
        x, y = event.get('pos', (0,0))
        if kind == 'refuse':
            _city_put(game, 'refusal_'+str(index), _city_brackets(8, 7),
                      x-3, y-3, 10, ['feedback'], True)
            continue
        if phase < 2:
            continue
        if kind in ('aid', 'beacon'):
            size = min(9, 3+2*(phase-2))
            colour = 1 if kind == 'aid' else 2
            support = np.array(ring(colour, size), dtype=np.int8)
            if kind == 'beacon': support[size//2,size//2] = 11
            _city_put(game, 'support_'+str(index), support,
                      x-size//2, y-size//2, 9, ['support_effect'], True)
        else:
            radius = min(max(1, event['radius']), max(1, phase-1))
            blast = np.full((2*radius+5, 2*radius+5), -1, dtype=np.int8)
            centre = radius+2
            for row in range(blast.shape[0]):
                for col in range(blast.shape[1]):
                    distance = (row-centre)**2+(col-centre)**2
                    if max(0,radius-1)**2 <= distance <= (radius+1)**2:
                        blast[row, col] = 0 if phase == 2 else 12 if phase < frames-1 else 3
                    elif phase == 2 and distance <= radius*radius:
                        blast[row, col] = 11
            _city_put(game, 'impact_'+str(index), blast, x-centre, y-centre,
                      10, ['impact'], True)
            if phase >= 3:
                smoke = np.full((7, 9), -1, dtype=np.int8)
                for sy in range(7):
                    for sx in range(9):
                        if (sx-4)**2+(sy-3)**2 < 13 and (sx+sy+phase)%3:
                            smoke[sy,sx] = 3 if phase < frames-1 else 4
                _city_put(game, 'smoke_'+str(index), smoke, x-4, y-4-(phase-3),
                          11, ['smoke'], True)
    before = getattr(game, 'before_actors', {})
    actor_by_id = {actor['id']:actor for actor in game.actors}
    for actor in game.actors:
        if actor.get('onboard') or actor.get('riding'):
            continue
        old = before.get(actor['id'], actor)
        if not actor['alive'] and (phase >= 3 or not old.get('alive', False)):
            continue
        shown = actor
        (x, y), reacquired = _city_contact_position(shown, old, game.tick, phase)
        core = _city_contact_art(shown)[1:3, 1:3].copy()
        seat_occupants = []
        has_seats = False
        if shown.get('indoors'):
            _city_put(game, 'heat_window_'+actor['id'], _city_brackets(3, 6),
                      x-2, y-2, 19, ['heat'], True)
        elif shown['role'] == 'responder':
            art = pixel_art(('.aaaaaa.', 'abbbbbaa', 'abbbb..a', 'abbbb..a', '.aaaaaa.', '.b....b.'),
                            {'a':3, 'b':4})
            _city_put(game, 'contact_'+actor['id'], art, x-5, y-2, 20,
                      ['contact','responder'], True)
            cross = pixel_art(('..p..','..p..','ppppp','..p..','..p..'), {'p':7})
            _city_put(game, 'rescue_mark_'+actor['id'], cross, x-5, y-2, 22,
                      ['responder','medical_cross'], True)
        elif shown.get('vehicle') or shown.get('vehicles'):
            accent = 2 if shown.get('accent', 3) in (9,10,11) else 3
            art = np.array(pixel_art(('.aaaaaa.', 'abbbbbba', 'abbbbbba', 'abbbbbba',
                                     'abbbbbba', 'abbbbbba', '.a....a.'),
                                    {'a':accent, 'b':3}), dtype=np.int8)
            occupants = shown.get('occupants')
            has_seats = bool(occupants)
            if has_seats:
                for seat, occupant_id in enumerate(occupants[:4]):
                    occupant = actor_by_id.get(occupant_id)
                    if occupant is None or not occupant.get('alive', False):
                        continue
                    seat_occupants.append(occupant)
                    ox, oy = ((-2,-1),(1,-1),(-2,2),(1,2))[seat]
                    seat_core = _city_contact_art(occupant)[1:3,1:3].copy()
                    art[oy+2:oy+4, ox+3:ox+5] = -1
                    _city_put(game, 'seat_core_'+actor['id']+'_'+str(seat), seat_core,
                              x+ox, y+oy, 23, ['contact','identity','vehicle_occupant'], True)
            else:
                art[2:4,3:5] = -1
            _city_put(game, 'contact_'+actor['id'], art, x-3, y-2, 20,
                      ['contact','traffic_vehicle'], True)
        else:
            body = _city_contact_art(shown)
            body[1:3, 1:3] = -1
            if shown.get('traffic'):
                body[body == 3] = 3
            _city_put(game, 'contact_'+actor['id'], body,
                      x-1, y-1, 20, ['contact'], True)
        if not has_seats:
            _city_put(game, 'core_'+actor['id'], core, x, y, 23,
                      ['contact', 'identity'], True)
        _city_threat_signal(game, actor['id'], seat_occupants if has_seats else [shown],
                            x, y, phase, 12 if has_seats else 8)
        priority = shown.get('priority') or any(person.get('priority') for person in seat_occupants)
        if priority:
            size = 12 if has_seats else 8
            _city_put(game, 'priority_'+actor['id'], _city_brackets(0, size),
                      x-(5 if has_seats else 3), y-(4 if has_seats else 3),
                      18, ['priority'], True)
        if shown.get('injured'):
            _city_put(game, 'injured_'+actor['id'], [[1,1]], x, y+3,
                      18, ['injured'], True)
        if shown.get('observed_at', game.tick) < game.tick:
            stale = np.full((5, 5), -1, dtype=np.int8)
            stale[0, :2] = stale[-1, -2:] = 3
            _city_put(game, 'stale_'+actor['id'], stale,
                      x-1, y-1, 18, ['stale_track'], True)
        elif reacquired and phase < 3:
            _city_put(game, 'reacquire_'+actor['id'], _city_brackets(2, 6),
                      x-2, y-2, 18, ['reacquired_track'], True)
    _city_instruments(game, phase)
    _city_edge_cues(game)
    for name in list(game._city_sprites):
        if name not in game._city_used:
            game.current_level.remove_sprite(game._city_sprites.pop(name))


def _city_craters(game):
    for (x, y), radius in game.craters.items():
        name = 'crater_'+str(x)+'_'+str(y)
        radius = max(1, int(radius))
        if game._city_crater_cache.get(name) == radius:
            game._city_used.add(name)
            continue
        size = radius*2+3
        pixels = np.full((size, size), -1, dtype=np.int8)
        for row in range(size):
            for col in range(size):
                distance = (row-radius-1)**2+(col-radius-1)**2
                if distance <= radius*radius:
                    pixels[row, col] = 5 if (row*3+col*5)%5 else 4
                elif distance <= (radius+1)**2 and (row+col)%2:
                    pixels[row, col] = 3
        _city_put(game, name, pixels, x-radius-1, y-radius-1, -7, ['crater'], True)
        game._city_crater_cache[name] = radius


def _city_edge_cues(game):
    camera_x, camera_y = int(game.camera.x), int(game.camera.y)
    nearest = {}
    for actor in game.actors:
        if not actor['alive'] or actor['role'] != 'hostile':
            continue
        x, y = actor.get('observed', actor['pos'])
        local_x, local_y = x-camera_x, y-camera_y
        if 2 <= local_x <= 61 and 4 <= local_y <= 50:
            continue
        dx, dy = local_x-32, local_y-28
        if abs(dx)*22 >= abs(dy)*30:
            edge = 'left' if dx < 0 else 'right'
            sx = 0 if dx < 0 else 61
            sy = max(7, min(47, round(28+dy*30/max(1, abs(dx)))))
        else:
            edge = 'up' if dy < 0 else 'down'
            sx = max(4, min(57, round(32+dx*22/max(1, abs(dy)))))
            sy = 4 if dy < 0 else 49
        distance = abs(dx)+abs(dy)
        if edge not in nearest or distance < nearest[edge][0]:
            nearest[edge] = (distance, sx, sy, 8 if actor.get('confidence') == 4 else 11)
    shapes = {
        'left': ('.c.', 'cc.', '.c.'), 'right': ('.c.', '.cc', '.c.'),
        'up': ('.c.', 'ccc', '...'), 'down': ('...', 'ccc', '.c.'),
    }
    for edge, (_, x, y, colour) in nearest.items():
        _city_put(game, 'bearing_'+edge, pixel_art(shapes[edge], {'c': colour}),
                  x, y, 35, ['contact_bearing'])


def city_art_transition(game, phase):
    phase = max(0, min(4, int(phase)))
    overlay = np.full((48,64), -1, dtype=np.int8)
    width = (0, 15, 30, 20, 6)[phase]
    if width:
        overlay[:, :width] = 5
        overlay[:, 64-width:] = 5
        overlay[::2, width-1] = 10
        overlay[1::2, 64-width] = 10
    if phase < 3:
        radius = (10,7,3)[phase]
        for row in range(24-radius-2,24+radius+3):
            for col in range(32-radius-2,32+radius+3):
                distance = abs(row-24)+abs(col-32)
                if distance in (radius,radius+1):
                    overlay[row,col] = 14
        for side in (-1,1):
            x = 32+side*(radius+3)
            overlay[22:27,x] = 10
            overlay[21,x-side] = overlay[27,x-side] = 10
    else:
        sweep = 15 if phase == 3 else 34
        overlay[sweep, width:64-width] = 10
        overlay[sweep+1, width:64-width:3] = 3
    _city_put(game, 'mission_transition', overlay, 0, 4, 60, ['mission_transition'])


def _city_threat_signal(game, name, people, x, y, phase, size=8):
    threats = [person for person in people if person.get('alive') and person['role'] == 'hostile'
               and person.get('attack_stage', 'quiet') != 'quiet']
    if not threats:
        return
    threat = max(threats, key=lambda person: person.get('threat_age', 0)/max(1, person.get('threat_limit', 1)))
    ratio = min(1, threat.get('threat_age', 0)/max(1, threat.get('threat_limit', 1)))
    arming = threat.get('attack_stage') == 'arming'
    count = min(8, 3+round(ratio*5)) if arming else 2
    colour = 12 if arming else 2
    dashes = np.full((size,size), -1, dtype=np.int8)
    middle, last = size//2, size-1
    positions = ((middle-1,0),(middle-1,last),(0,middle-1),(last,middle-1),
                 (2,0),(last-3,last),(0,2),(last,last-3))
    for index, (dx,dy) in enumerate(positions[:count]):
        dashes[dy,dx] = colour
        if dy in (0,last):
            dashes[dy,min(last,dx+1)] = colour
        else:
            dashes[min(last,dy+1),dx] = colour
    _city_put(game, 'threat_'+name, dashes,
              x-(5 if size == 12 else 3), y-(4 if size == 12 else 3),
              19, ['arming' if arming else 'gathering'], True)
