# Author: Claude Sonnet 5.5
# Date: 07-November-2026
# PURPOSE: te02 redraws te01 (cable-routing in eight stages: dock, core, posts, spinning blades and a rolling cover) with the
#          rules unchanged. Layouts, solutions, cable lengths, blade geometry, the cover's rail, inputs, undo and reset are
#          the same code as te01; only the pictures are new: each stage is its own room with its own floor, frame, shelf,
#          posts and gentle life, and every object is a named sprite with a face or a texture, drawn in the early-console look.
# Updated: 07-November-2026, Claude Sonnet 5.5: round A, calm and readable. Floors turned down to one hue family and one quiet line or less
#   (no speckle, dither or stars of colour), far fewer and better-spaced props in every room, fewer border bulbs. Rules untouched.
# Updated: 07-November-2026, Claude Sonnet 5.5: round B, animation. A move now eases and hops over four frames with dust at the feet
#   (and at the cover when it is pushed); pickup and latch pop a little star burst; every refused or missed input gets a short drawn
#   reaction (a nudge or head-shake, closing target brackets, a cable flash when taut); the rover's head lamp pulses; a level clear ends
#   in an iris that closes on the rover and opens on the next stage. Rules untouched; idle motion still rides only on action frames.
# Updated: 07-November-2026, Claude Sonnet 5.5: round C, final look (the loss no longer rains: cloud and drops removed). A move now crouches, leaps and lands with a squash (the rover
#   flattens a pixel on take-off and landing and stands tall again on the last frame); dust puffs are bigger with a dark rim so they
#   show on the bright stages; a pulled-tight cable now rings like a plucked string for a few frames; the whole screen shakes when
#   the run is lost; the level-clear is one frame shorter. Rules untouched; idle motion still rides only on action frames.
# SRP/DRY check: Pass -- the rule functions come first and are copied from te01 untouched; the art below only reads the state.
#
# CHANGELOG
# 07-Nov-2026 (Claude Sonnet 5.5): pass 4, polish. Cave posts now blue with a violet mark (the sky-blue pillars glared), cobble stones calmer with
#   rarer blue ones, candy frosting quieter (one broken gloss line), the kitchen rug has a medallion, the welder is an orange cart with a visor
#   slit (it was pink with a face and read as a character), space has more haze, a small planet and stars, the whale has a bigger eye, and
#   roaming creatures now cross only the screen width so they are not off-screen for long. Rules untouched.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 3, variety and life. Every stage has its own floor texture (concrete slabs, tile, icing, grating,
#   nebula, water light, lawn, cobbles, no more plain checkers) and a cast of its own: conveyor with crates, rug, cat and mouse,
#   turbine and steam, ringed planets and a comet, a spiral lollipop and gingerbread man, a whale, crab and seaweed, a pond with a frog and a
#   hopping bunny, bats and watching eyes. The dock got a tall lamp-face canopy so its face shows with the rover on it, and the cable reel moved above
#   it so the two no longer stack. Saws drawn at their real size (small ones five pixels). Level clear is now a confetti shower; the run-over adds a
#   rain cloud and flying shards. Posts cast a shadow. Rules untouched.
# 07-Nov-2026 (Claude Sonnet 5.5): pass 2, art critique. Rover now nine pixels with a real face (blink, wince at a refused move, cheer and
#   hop on a win, droop and cry on a loss); dock is a lamp-eyed charger with no pad; the cable counter is a real side-view reel;
#   hood is a visored guard robot; saw blades have teeth that turn; calmer floors; riveted corner plates on every stage;
#   bigger two-ring win stars; fish and ripples redrawn; rails are steel with sleepers. Rules untouched (equivalence 0 differences).
# 07-Nov-2026 (Claude Sonnet 5.5): first version. Win and loss now play a short drawn effect (sparkle burst; red alarm,
#   smoke and a sad robot) before the level changes or the run ends. The cable reel is still the cable counter.
"""te02: te01 with new art; the rules are unchanged."""
from functools import lru_cache
from collections import namedtuple
from itertools import combinations
import random
from math import hypot, isfinite, cos, sin, pi

import numpy as np
from arcengine import ARCBaseGame, Camera, Level, Sprite


# --- art helper ---
def pixel_art(rows: tuple, colours: dict) -> list[list[int]]:
    """Letters to colour indices; '.' is -1, so the ground shows through."""
    return [[-1 if ch == "." else colours[ch] for ch in row] for row in rows]


EPS = 1e-9
CELL, OX, OY = 6, 2, 2
WHITE, SILVER, GRAY, DARK, BLACK = 0, 1, 2, 4, 5
RED, BLUE, SKY, YELLOW, ORANGE, GREEN = 8, 9, 10, 11, 12, 14
DIRECTIONS = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}
BODY_RADIUS = .55
GUARD_HALF = .48
LEVELS = [{'name': 'te01-1',
  'size': (10, 9),
  'dock': (1, 4),
  'core': (7, 4),
  'obstacles': ((3.2, 3.6, 3.8, 5.3),),
  'cable': 7.8,
  'cutters': ()},
 {'name': 'te01-2',
  'size': (10, 9),
  'dock': (1, 7),
  'core': (9, 2),
  'obstacles': ((2.3, 5.3, 3.3, 9.0), (4.8, 5.5, 5.4, 7.4), (6.7, 2.3, 7.7, 4.7)),
  'cable': 14.0,
  'cutters': ()},
 {'name': 'te01-3',
  'size': (10, 9),
  'dock': (1, 7),
  'core': (9, 2),
  'obstacles': ((2.3, 5.3, 3.3, 9.0), (4.8, 5.5, 5.4, 7.4), (6.7, 2.3, 7.7, 4.7)),
  'cable': 14.0,
  'cutters': ((4.8, 3.5, 0.35),)},
 {'name': 'te01-4',
  'size': (10, 10),
  'dock': (1, 8),
  'core': (9, 2),
  'obstacles': ((2.3, 5.3, 3.3, 10.0), (4.8, 5.5, 5.4, 7.4), (6.7, 2.3, 7.7, 4.7)),
  'cable': 14.0,
  'cutters': ((4.8, 3.5, 0.35),)},
 {'name': 'te01-5',
  'size': (10, 9),
  'dock': (1, 7),
  'core': (9, 2),
  'obstacles': ((2.3, 5.3, 3.3, 9.0), (4.8, 5.5, 5.4, 7.4), (6.7, 2.3, 7.7, 4.7)),
  'cable': 14.0,
  'cutters': ((4.8, 3.5, 0.35), (6.0, 6.8, 0.25)),
  'guard_start': (7, 7),
  'guard_rail': ((6, 7), (7, 7)),
  'guard_target': 1},
 {'name': 'te01-6',
  'size': (10, 10),
  'dock': (1, 7),
  'core': (9, 2),
  'obstacles': ((2.3, 5.3, 3.3, 10.0), (4.8, 5.5, 5.4, 7.4), (6.7, 2.3, 7.7, 4.7)),
  'cable': 14.0,
  'cutters': ((4.8, 3.5, 0.35), (6.0, 6.8, 0.25)),
  'guard_start': (7, 8),
  'guard_rail': ((7, 8), (7, 7), (6, 7)),
  'guard_target': 1},
 {'name': 'te01-7',
  'size': (10, 10),
  'dock': (1, 8),
  'core': (9, 2),
  'obstacles': ((2.3, 4.3, 3.3, 10.0), (5.3, 0.0, 5.7, 5.7), (7.7, 4.3, 8.1, 10.0)),
  'cable': 30.0,
  'cutters': ((7.0, 6.0, 0.25),),
  'guard_start': (7, 7),
  'guard_rail': ((7, 6), (7, 7)),
  'guard_target': 0},
 {'name': 'te01-8',
  'size': (10, 10),
  'dock': (1, 8),
  'core': (9, 8),
  'obstacles': ((2.3, 2.3, 3.3, 10.0), (5.3, 0.0, 5.7, 6.7), (7.7, 2.3, 8.1, 10.0)),
  'cable': 42.0,
  'cutters': ((7.0, 7.0, 0.25),),
  'guard_start': (7, 8),
  'guard_rail': ((7, 7), (7, 8)),
  'guard_target': 0}]
State = namedtuple("State", "rover path carrying done dead pulse feedback focus facing guard latched")


def cross(first, second, third):
    return ((second[0]-first[0])*(third[1]-first[1])
            -(second[1]-first[1])*(third[0]-first[0]))


def canonical(points):
    result = []
    for point in points:
        point = tuple(round(value, 9) for value in point)
        if not result or point != result[-1]:
            result.append(point)
    return tuple(result)


def cable_length(path):
    return sum(hypot(second[0]-first[0], second[1]-first[1])
               for first, second in zip(path, path[1:]))


def segment_clear(first, second, obstacles):
    """Clip against each open rectangle interior; boundary contact is allowed."""
    for left, top, right, bottom in obstacles:
        low_time, high_time = 0.0, 1.0
        for origin, delta, low, high in ((first[0], second[0]-first[0], left, right),
                                       (first[1], second[1]-first[1], top, bottom)):
            if abs(delta) < EPS:
                if not low+EPS < origin < high-EPS:
                    low_time, high_time = 1.0, 0.0
                    break
            else:
                entry, leave = sorted(((low+EPS-origin)/delta, (high-EPS-origin)/delta))
                low_time, high_time = max(low_time, entry), min(high_time, leave)
        if low_time < high_time-EPS:
            return False
    return True


def clip_triangle(polygon, triangle):
    """Convex polygon clipping; all accepted points stay inside the old bend."""
    orientation = 1 if cross(*triangle) > 0 else -1
    for first, second in zip(triangle, triangle[1:]+triangle[:1]):
        if not polygon:
            break
        clipped, previous = [], polygon[-1]
        old_side = orientation*cross(first, second, previous)
        for current in polygon:
            new_side = orientation*cross(first, second, current)
            if (old_side >= -EPS) != (new_side >= -EPS):
                fraction = old_side/(old_side-new_side)
                clipped.append((previous[0]+(current[0]-previous[0])*fraction,
                                previous[1]+(current[1]-previous[1])*fraction))
            if new_side >= -EPS:
                clipped.append(current)
            previous, old_side = current, new_side
        polygon = clipped
    return canonical(polygon)


def hull(points):
    ordered = sorted(set(points))
    if len(ordered) < 3:
        return tuple(ordered)
    chains = []
    for ordering in (ordered, list(reversed(ordered))):
        chain = []
        for point in ordering:
            while len(chain) > 1 and cross(chain[-2], chain[-1], point) <= EPS:
                chain.pop()
            chain.append(point)
        chains.append(chain[:-1])
    return tuple(chains[0]+chains[1])


def shorten_bend(first, middle, last, obstacles):
    if abs(cross(first, middle, last)) <= EPS:
        return canonical((first, last))
    triangle, points = (first, middle, last), [first, last]
    for left, top, right, bottom in obstacles:
        polygon = clip_triangle(((left, top), (right, top), (right, bottom), (left, bottom)), triangle)
        area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(polygon, polygon[1:]+polygon[:1]))
        if abs(area) > EPS:
            points.extend(polygon)
    boundary = hull(points)
    if len(boundary) <= 2:
        return canonical((first, last))
    start, finish = boundary.index(first), boundary.index(last)
    choices = []
    for direction in (1, -1):
        chain, index = [first], start
        while index != finish:
            index = (index+direction) % len(boundary)
            chain.append(boundary[index])
        choices.append(tuple(chain))
    # The outer hull chain keeps the solids on the same side as the old bend.
    return max(choices, key=lambda chain: sum(abs(cross(first, last, point)) for point in chain))


@lru_cache(maxsize=50000)
def tighten(path, obstacles):
    path = canonical(path)
    while True:
        changed = False
        for index in range(1, len(path)-1):
            old = path[index-1:index+2]
            replacement = shorten_bend(*old, obstacles)
            if replacement == old:
                continue
            old_length, new_length = cable_length(old), cable_length(replacement)
            if new_length > old_length+1e-7:
                continue                      # never lengthen the cable; keep the bend as it is
            if new_length < old_length-EPS or len(replacement) < len(old):
                path = canonical(path[:index-1]+replacement+path[index+2:])
                changed = True
                break
        if not changed:
            return path


def closest_point(point, first, last):
    dx, dy = last[0]-first[0], last[1]-first[1]
    length_squared = dx*dx+dy*dy
    fraction = 0 if length_squared < EPS else max(0, min(1,
        ((point[0]-first[0])*dx+(point[1]-first[1])*dy)/length_squared))
    return first[0]+fraction*dx, first[1]+fraction*dy


def disc_segment(center, radius, first, last):
    point = closest_point(center, first, last)
    return hypot(center[0]-point[0], center[1]-point[1]) <= radius+EPS


def disc_triangle(center, radius, first, middle, last):
    area = cross(first, middle, last)
    if abs(area) > EPS:
        orientation = 1 if area > 0 else -1
        if all(orientation*cross(start, end, center) >= -EPS
               for start, end in ((first, middle), (middle, last), (last, first))):
            return True
    return any(disc_segment(center, radius, start, end)
               for start, end in ((first, middle), (middle, last), (last, first)))


def position_at(first, last, fraction):
    return (first[0]+(last[0]-first[0])*fraction,
            first[1]+(last[1]-first[1])*fraction)


@lru_cache(maxsize=40000)
def sweep_intervals(path, destination, obstacles):
    """Partition at exact changes of the taut cable's fixed final support.

    For rectangles, a support can change only when the moving endpoint aligns
    with two dock/corner supports. Extra collinearity events are harmless. Between
    events the stationary prefix and one endpoint triangle cover the full sweep,
    including reversal and paths whose full winding overlaps itself.
    """
    supports = {path[0]}
    for left, top, right, bottom in obstacles:
        supports.update(((left, top), (right, top), (right, bottom), (left, bottom)))
    times, start = {0., 1.}, path[-1]
    for first, last in combinations(sorted(supports), 2):
        before, after = cross(first, last, start), cross(first, last, destination)
        if abs(after-before) > EPS:
            time = -before/(after-before)
            if EPS < time < 1-EPS:
                times.add(round(time, 12))
    times, intervals = sorted(times), []
    for low, high in zip(times, times[1:]):
        middle = position_at(start, destination, (low+high)/2)
        taut = tighten(path+(middle,), obstacles)
        prefix = taut[:-1] if len(taut) > 1 else taut
        intervals.append((low, high, prefix))
    return tuple(intervals)


@lru_cache(maxsize=50000)
def cable_sweep_hit(path, destination, obstacles, cutters):
    """Return first (fraction, exact cable contact, cutter index), or None."""
    start = path[-1]
    for low, high, prefix in sweep_intervals(path, destination, obstacles):
        first, last = position_at(start, destination, low), position_at(start, destination, high)
        hits = []
        for number, (cx, cy, radius) in enumerate(cutters):
            center = (cx, cy)
            static_hit = any(disc_segment(center, radius, a, b) for a, b in zip(prefix, prefix[1:]))
            if not static_hit and not disc_triangle(center, radius, prefix[-1], first, last):
                continue
            earliest = low
            if not static_hit and not disc_segment(center, radius, prefix[-1], first):
                left, right = low, high
                for _ in range(36):
                    middle = (left+right)/2
                    point = position_at(start, destination, middle)
                    if disc_triangle(center, radius, prefix[-1], first, point):
                        right = middle
                    else:
                        left = middle
                earliest = right
            contact_path = prefix+(position_at(start, destination, earliest),)
            contact = min((closest_point(center, a, b) for a, b in zip(contact_path, contact_path[1:])),
                          key=lambda point: hypot(cx-point[0], cy-point[1]))
            hits.append((earliest, contact, number))
        if hits:
            return min(hits, key=lambda hit: (hit[0], hit[2]))
    return None


def initial(level):
    return State(level["dock"], (level["dock"],), False, False, False, 0,
                 "ready", level["dock"], (0, -1),level.get("guard_start"),False)


def body_blocker(level, state, destination):
    width, height = level["size"]
    if not (BODY_RADIUS <= destination[0] <= width-BODY_RADIUS
            and BODY_RADIUS <= destination[1] <= height-BODY_RADIUS):
        return destination
    for left, top, right, bottom in level["obstacles"]:
        expanded = ((left-BODY_RADIUS, top-BODY_RADIUS, right+BODY_RADIUS, bottom+BODY_RADIUS),)
        if not segment_clear(state.rover, destination, expanded):
            return (max(left, min(right, destination[0])), max(top, min(bottom, destination[1])))
    return None


def body_cutter_hit(level, start, destination):
    hits = []
    for number, (cx, cy, radius) in enumerate(level["cutters"]):
        if not disc_segment((cx, cy), radius+BODY_RADIUS, start, destination):
            continue
        low, high = 0., 1.
        for _ in range(36):
            middle = (low+high)/2
            if disc_segment((cx, cy), radius+BODY_RADIUS, start, position_at(start, destination, middle)):
                high = middle
            else:
                low = middle
        hits.append((high, (cx, cy), number))
    return min(hits, default=None)


def plan_step(level,state,direction):
    destination=(state.rover[0]+direction[0],state.rover[1]+direction[1])
    guard=state.guard
    if guard is not None and not state.latched and destination==guard:
        next_guard=(guard[0]+direction[0],guard[1]+direction[1])
        rail=level["guard_rail"]
        connected=any((guard==first and next_guard==last) or (guard==last and next_guard==first)
                      for first,last in zip(rail,rail[1:]))
        if not connected or body_blocker(level,state._replace(rover=guard),next_guard) is not None:
            return None,guard,"guard-stop"
        guard=next_guard
    blocker=body_blocker(level,state,destination)
    if blocker is not None:
        return None,blocker,"bumper"
    return destination,guard,None


def exposed_intervals(cutter,guard_start,guard_end):
    """Exact fractions during which a translating square hood exposes the disc."""
    if guard_start is None:
        return ((0.,1.),)
    margin=GUARD_HALF-cutter[2]
    if margin<0:
        return ((0.,1.),)
    low,high=0.,1.
    for dimension in (0,1):
        offset=guard_start[dimension]-cutter[dimension]
        delta=guard_end[dimension]-guard_start[dimension]
        if abs(delta)<EPS:
            if abs(offset)>margin+EPS:
                return ((0.,1.),)
        else:
            first,last=sorted(((-margin-offset)/delta,(margin-offset)/delta))
            low,high=max(low,first),min(high,last)
    if low>high+EPS:
        return ((0.,1.),)
    intervals=[]
    if low>EPS:intervals.append((0.,min(1.,low)))
    if high<1-EPS:intervals.append((max(0.,high),1.))
    return tuple(intervals)


def motion_contact(level,state,destination,guard_destination):
    """First actual exposed-blade contact; hood motion never grants early safety."""
    contacts=[]
    for number,cutter in enumerate(level["cutters"]):
        for low,high in exposed_intervals(cutter,state.guard,guard_destination):
            start=position_at(state.rover,destination,low)
            finish=position_at(state.rover,destination,high)
            one=dict(cutters=(cutter,))
            body=body_cutter_hit(one,start,finish)
            path=tighten(state.path+(start,),level["obstacles"])
            possibilities=[(body,"blade"),
                           (cable_sweep_hit(path,finish,level["obstacles"],(cutter,)),"cut")]
            for contact,kind in possibilities:
                if contact is None:continue
                fraction=low+(high-low)*contact[0]
                # At the closing boundary the entire blade is already enclosed.
                if high<1-EPS and fraction>=high-EPS:continue
                contacts.append((fraction,contact[1],number,kind))
    return min(contacts,key=lambda item:(item[0],item[3],item[2]),default=None)


def move(level, state, direction):
    destination,guard,refusal=plan_step(level,state,direction)
    if refusal is not None:
        return state._replace(feedback=refusal,focus=guard,facing=direction)
    path = tighten(state.path+(destination,), level["obstacles"])
    if cable_length(path) > level["cable"]+EPS:
        return state._replace(feedback="taut", focus=path[-2] if len(path)>1 else state.rover, facing=direction)
    contact=motion_contact(level,state,destination,guard)
    if contact is not None:
        fraction,focus,number,kind=contact
        stopped = position_at(state.rover, destination, fraction)
        path = tighten(state.path+(stopped,), level["obstacles"])
        stopped_guard=position_at(state.guard,guard,fraction) if guard is not None else None
        return state._replace(rover=stopped,path=path,guard=stopped_guard,dead=True,feedback=kind,focus=focus,facing=direction)
    latched=state.latched or (guard is not None and not exposed_intervals(
        level["cutters"][level["guard_target"]],guard,guard))
    feedback="latch" if latched and not state.latched else "push" if guard!=state.guard else "move"
    return state._replace(rover=destination,path=path,guard=guard,latched=latched,feedback=feedback,focus=destination,
                          facing=direction, done=state.carrying and destination == level["dock"])


def reel_direction(level, state):
    if len(state.path) < 2:
        return None
    target, length = state.path[-2], cable_length(state.path)
    choices = []
    for action, direction in DIRECTIONS.items():
        toward = ((target[0]-state.rover[0])*direction[0]+(target[1]-state.rover[1])*direction[1])
        destination,guard,refusal=plan_step(level,state,direction)
        if toward <= EPS or refusal is not None:
            continue
        path = tighten(state.path+(destination,), level["obstacles"])
        if cable_length(path) < length-EPS:
            choices.append((cable_length(path), action, direction))
    if choices:
        return min(choices, key=lambda option: (option[0], option[1]))[2]
    return None


def reel(level, state):
    direction = reel_direction(level, state)
    if direction is not None:
        selected = move(level, state, direction)
        return selected if selected.dead else selected._replace(feedback="reel")
    target = state.path[-2] if len(state.path)>1 else level["dock"]
    return state._replace(feedback="reel-stop", focus=target)


def transition(level, state, action, point=None):
    if state.done or state.dead:
        return state
    state = state._replace(pulse=1-state.pulse)
    if action in DIRECTIONS:
        return move(level, state, DIRECTIONS[action])
    if action == 5:
        return reel(level, state)
    if action == 6:
        core = level["core"]
        if point is None or hypot(point[0]-core[0], point[1]-core[1]) > .7:
            return state._replace(feedback="miss", focus=state.rover if point is None else point)
        if state.carrying:
            return state._replace(feedback="loaded", focus=state.rover)
        if (hypot(state.rover[0]-core[0], state.rover[1]-core[1]) > 1.05
                or not segment_clear(state.rover, core, level["obstacles"])):
            return state._replace(feedback="far", focus=core)
        return state._replace(carrying=True, feedback="pickup", focus=state.rover)
    return state._replace(feedback="refused", focus=state.rover)



def pixel(point):
    return OX+CELL*point[0], OY+CELL*point[1]


def rect(frame, left, top, width, height, color):
    x1, y1 = max(0, round(left)), max(0, round(top))
    x2, y2 = min(64, round(left+width)), min(64, round(top+height))
    if x1 < x2 and y1 < y2:
        frame[y1:y2, x1:x2] = color


def line(frame, first, second, color):
    count = max(1, round(hypot(second[0]-first[0], second[1]-first[1])*2))
    for fraction in np.linspace(0, 1, count+1):
        point = position_at(first, second, fraction)
        rect(frame, *point, 1, 1, color)


def disc(frame, center, radius, color):
    for dy in range(-int(radius)-1, int(radius)+2):
        for dx in range(-int(radius)-1, int(radius)+2):
            if hypot(dx, dy) <= radius:
                rect(frame, center[0]+dx, center[1]+dy, 1, 1, color)




# =====================================================================================================================
# ART. Nothing below decides a rule: it only draws the state the functions above produced. Every object on screen is a
# named engine Sprite (name, tags, layer); sprites are moved whole and their pictures are swapped, never repainted
# onto a finished frame. Layers: -10 floor, -9 floor decals, -8 frame and shelf, -7 shelf props and drifting life,
# 1 posts, 2 rails, 3 blades, 4 dock, 5 cable, 6 reel, 7 cover, 8 core, 9 rover, 10 cue, 11 effects.
# =====================================================================================================================
LEGEND = {'.': -1, 'W': 0, 'K': 5, 'M': 6, 'P': 7, 'R': 8, 'B': 9, 'S': 10, 'Y': 11, 'O': 12, 'N': 13, 'G': 14, 'V': 15}
MAGENTA, PINK, MAROON, PURPLE = 6, 7, 13, 15
ARENA_W = 10 * CELL                                   # every stage is ten cells wide, nine or ten tall
PALE = (WHITE, SKY, YELLOW, PINK, ORANGE, GREEN)      # light colours turn red when the run is over, dark ones maroon


def pic(rows, swap=None):
    """Letters to colour indices; `swap` recolours letters (and fills placeholders) for one use of a shared picture."""
    swap = swap or {}
    assert len({len(row) for row in rows}) == 1, rows
    return np.array([[LEGEND[swap.get(ch, ch)] for ch in row] for row in rows], dtype=np.int8)


def stamp(canvas, art, x, y):
    """Copy the opaque pixels of `art` onto `canvas` at (x, y), clipped to the canvas."""
    for dy, row in enumerate(art):
        for dx, value in enumerate(row):
            if value >= 0 and 0 <= y + dy < canvas.shape[0] and 0 <= x + dx < canvas.shape[1]:
                canvas[y + dy, x + dx] = value


# --- rows shared by several frames: animals that blink and plants that sway reuse one drawing, shifted or edited ---
CAT_OPEN = ('.K.......K.', '.KOK...KOK.', '.KOOKKKOOK.', '.KOWOOOWOK.', '.KOKOPOKOK.', '.KOOOKOOOK.', '..KKOOOKK..',
            '.KOOOWOOOK.', '.KOOOWOOOKK', '.KOOOOOOOOK', '..KKKKKKKK.')
CAT_BLINK = CAT_OPEN[:3] + ('.KOKOOOKOK.', '.KOOOPOOOK.') + CAT_OPEN[5:]
SEAWEED = ('...K.', '..KGK', '..KGK', '.KGK.', '.KGK.', 'KGK..', 'KGK..', '.KGK.', '.KGK.', '..KGK', '..KGK', '.KGK.', '.KGK.', 'KGGGK')
SUNFLOWER = ('..Y.Y.Y..', '.YYKKKYY.', 'Y.KNNNK.Y', 'YYKNNNKYY', 'Y.KNNNK.Y', '.YYKKKYY.', '..Y.Y.Y..',
             '....G....', '..G.G.G..', '...GGG...', '....G....', '....G....', '....G....')
SUNFLOWER_SWAY = tuple('.' + row[:-1] for row in SUNFLOWER[:7]) + SUNFLOWER[7:]
EYES_OPEN = ('.YY...YY.', 'YKY...YKY', '.YY...YY.')
EYES_SHUT = ('.........', 'YYY...YYY', '.........')
BUNNY = ('.KK...KK.', '.KWK.KWK.', '.KPKKKPK.', '.KWWWWWK.', 'KWKWWWKWK', 'KWWWPWWWK', 'KWWWWWWWK', '.KWWWWWK.')


# --- the picture library: shelf props and floor life. Each entry is a tuple of frames; 'E' and 'L' are placeholders ---
LIB = {
    # workshop
    'toolbox': (('..KYYYK..', '..K...K..', 'KKKKKKKKK', 'KRWRRRRRK', 'KRRRKKRRK', 'KRRRRRRRK', 'KKKKKKKKK'),),
    'lamp': (('.KYYYK.', 'KYWYYYK', 'KYYYYYK', '.KKKKK.', '...K...', '...K...', '..KKK..'),
             ('.KOOOK.', 'KOYOOOK', 'KOOOOOK', '.KKKKK.', '...K...', '...K...', '..KKK..')),
    'buddy': (('...K...', '..KRK..', '.KSSSK.', 'KSKSKSK', 'KSSSSSK', 'KSWWWSK', '.KKKKK.'),
              ('...K...', '..KRK..', '.KSSSK.', 'KSSSSSK', 'KSSSSSK', 'KSWWWSK', '.KKKKK.')),
    'gear': (('...K...', '.K.Y.K.', '..KYK..', 'KYYKYYK', '..KYK..', '.K.Y.K.', '...K...'),
             ('K.....K', '.KY.YK.', '..KYK..', '.YKKKY.', '..KYK..', '.KY.YK.', 'K.....K')),
    'spray': (('.KK.', '.KR.', 'KSSK', 'KSWK', 'KSSK', 'KSSK', 'KKKK'),),
    # kitchen
    'pot': (('.....K.....', '.K..KRK..K.', '..K.KK..K..', 'KKKKKKKKKKK', 'KRWRRRRRRRK', 'KRRRRRRRRRK', '.KKKKKKKKK.'),
            ('..K..K..K..', '.K..K..K.K.', '..K..K..K..', 'KKKKKKKKKKK', 'KRWRRRRRRRK', 'KRRRRRRRRRK', '.KKKKKKKKK.')),
    'cake': (('...R...', '..KRK..', '.KWWWK.', 'KWPWPWK', 'KPPPPPK', 'KWWWWWK', 'KKKKKKK'),),
    'cups': (('..........', '..........', '..........', 'KKKK..KKKK', 'KYYK..KOOK', 'KYWK..KOWK', '.KKK..KKKK'),),
    'jar': (('.KKKK.', '.KYYK.', 'KSSSSK', 'KSOOSK', 'KSOOSK', 'KSSSSK', '.KKKK.'),),
    'bottle': (('..KK..', '..KR..', '.KSSK.', '.KSWK.', '.KSSK.', '.KSSK.', '.KKKK.'),),
    # power plant
    'tesla': (('...Y...', '..KYK..', '.KSWSK.', '.KSSSK.', '..KBK..', '.KBBBK.', 'KKKKKKK'),
              ('.Y.Y.Y.', '..KYK..', '.KSWSK.', '.KSSSK.', '..KBK..', '.KBBBK.', 'KKKKKKK')),
    'fuse': (('KKKKKK', 'KRKYKG', 'KRKYKG', 'KKKKKK', 'KBBBBK', 'KBWBBK', 'KKKKKK'),
             ('KKKKKK', 'KRKYKG', 'KOKYKG', 'KKKKKK', 'KBBBBK', 'KBWBBK', 'KKKKKK')),
    'battery': (('.KKK.', 'KYYYK', 'KKKKK', 'KRRRK', 'KRWRK', 'KRRRK', 'KKKKK'),),
    'bulb': (('.KKK.', 'KWYWK', 'KYYYK', 'KYYYK', '.KYK.', '.KKK.', '.KKK.'),
             ('.KKK.', 'KOYOK', 'KOOOK', 'KOOOK', '.KOK.', '.KKK.', '.KKK.')),
    'beacon': (('..KKK..', '.KRRRK.', 'KRWRRRK', 'KRRRRRK', 'KKKKKKK', '.KBBBK.', '.KKKKK.'),
               ('..KKK..', '.KNNNK.', 'KNRNNNK', 'KNNNNNK', 'KKKKKKK', '.KBBBK.', '.KKKKK.')),
    # candy
    'jar-red': (('.KYYK.', 'KKKKKK', 'KRRPRK', 'KRPRRK', 'KRRRPK', 'KRRRRK', '.KKKK.'),),
    'jar-green': (('.KYYK.', 'KKKKKK', 'KGGWGK', 'KGWGGK', 'KGGGWK', 'KGGGGK', '.KKKK.'),),
    'lolly': (('.KKK.', 'KMWMK', 'KWMWK', 'KMWMK', '.KKK.', '..K..', '..K..'),
              ('.KKK.', 'KWMWK', 'KMWMK', 'KWMWK', '.KKK.', '..K..', '..K..')),
    'cupcake': (('..KPK..', '.KPPPK.', 'KPWPWPK', 'KKKKKKK', '.KOOOK.', '.KOOOK.', '..KKK..'),),
    'gummy': (('.K...K.', 'KRK.KRK', '.KRRRK.', 'KRKRKRK', 'KRRRRRK', '.KRWRK.', '.KKKKK.'),
              ('.K...K.', 'KRK.KRK', '.KRRRK.', 'KRRRRRK', 'KRRRRRK', '.KRWRK.', '.KKKKK.')),
    'cane': (('.KKK.', 'KWRWK', 'K.KRK', '..KWK', '..KRK', '..KWK', '..KKK'),),
    # floor life
    'star': (('.W.', 'WYW', '.W.'), ('...', '.W.', '...'), ('...', '.Y.', '...')),
    'saucer': (('..KKKKK..', '.KSSWSSK.', 'KRRYRRYRK', '.K.K.K.K.'), ('..KKKKK..', '.KSSWSSK.', 'KRYRRYRRK', '.K.K.K.K.')),
    'bubble': (('.W.', 'W.W', '.W.'), ('...', '.W.', '...')),
    'fish': (('..K.KKKK..', '.KOKOOOOK.', 'KOOOOWOKOK', '.KOKOOOOK.', '..K.KKKK..'),
             ('.K..KKKK..', '.KOKOOOOK.', 'KOOOOWOKOK', '.KOKOOOOK.', '.K..KKKK..')),
    'ripple': (('..WWWWW..', '.W.....W.', '..WWWWW..'), ('...WWW...', '..W...W..', '...WWW...'), ('....W....', '...W.W...', '....W....')),
    'tuft': (('.Y.Y.', 'Y.Y.Y', '..Y..'),),
    'shell': (('.KKK.', 'KYOYK', '.KOK.'),),
    'flower': (('.PRP.', 'PYYYP', '.PRP.', '..K..', '.KK..'), ('.PRP.', 'PYWYP', '.PRP.', '..K..', '..KK.')),
    'mushroom': (('.KRRK.', 'KRWRWK', 'KKKWKK', '..KWK.'),),
    'wing': (('W...W', '.W.W.', '..K..'), ('.....', 'WWKWW', '..K..')),
    'crystal': (('..W..', '.WSS.', 'WSSBS', 'WSBBS', '.SBBS', '.SBB.', '..B..'), ('..S..', '.WSS.', 'WSWBS', 'WSBBS', '.SBBS', '.SBB.', '..B..')),
    'glow': (('.Y.', 'YWY', '.Y.'), ('...', '.Y.', '...')),
    'bolt': (('..YY.', '.YY..', 'YYYY.', '..YY.', '.YY..', '.Y...'), ('.....', '.....', '.....', '.....', '.....', '.....')),
    'spark': (('.Y.', 'YWY', '.Y.'), ('Y.Y', '.W.', 'Y.Y')),
    'sprinkle': (('YY.', '...', '.SS'), ('GG.', '...', '.RR'), ('WW.', '...', '.OO')),
    # workshop
    'crate': (('KKKKKKK', 'KOYYYOK', 'KYOYOYK', 'KYYOYYK', 'KYOYOYK', 'KOYYYOK', 'KKKKKKK'),),
    'barrel': (('.KKKKK.', 'KOOOOOK', 'KKKKKKK', 'KOYOOOK', 'KOOOOOK', 'KKKKKKK', 'KOOOOOK', '.KKKKK.'),),
    'welder': (('..KKKKK....', '.KOOOOOK.W.', 'KOKKKKKOKWY', 'KOOYYYOKKY.', 'KOOOOOOK...', '.KOOOOOK...', '.KKKKKKK...'),
               ('..KKKKK....', '.KOOOOOK..W', 'KOKKKKKOK.W', 'KOOYYYOKKYW', 'KOOOOOOK...', '.KOOOOOK...', '.KKKKKKK...')),
    'puddle': (('...VVVVVV....', '.VVVVMVVVVV..', 'VVVSVVVVVVVV.', '.VVVVVVVMVV..', '...VVVVVV....'),
               ('...VVVVVV....', '.VVVVVVVMVV..', 'VVVVVVSVVVVV.', '.VVVMVVVVVV..', '...VVVVVV....')),
    'nut': (('.KKK.', 'KYYYK', 'KYKYK', 'KYYYK', '.KKK.'),),
    # kitchen
    'mouse': (('.......KK.', '..KKKKKPPK', 'K.KWWWWWWK', 'KKKWWWWKWK', '..K.KK.KK.'),
              ('.......KK.', '..KKKKKPPK', '.KKWWWWWWK', 'K.KWWWWKWK', '..KK.KK.K.')),
    'orange': (('.KKK.', 'KOWOK', 'KOOOK', 'KOOOK', '.KKK.'), ('.KKK.', 'KOOOK', 'KOOWK', 'KOOOK', '.KKK.')),
    'splat': (('..R...R..', '.RRRRRRR.', 'RRWRRRRRR', '.RRRRRRR.', '..RR.R...', '.....R...'),),
    'cat': (CAT_OPEN, CAT_OPEN, CAT_OPEN, CAT_OPEN, CAT_OPEN, CAT_BLINK),
    'fly': (('W.W', '.K.'), ('...', 'WKW')),
    # power plant
    'gauge': (('.KKKKK.', 'KSSYSSK', 'KGKSSRK', 'KSSKSSK', 'KSSSSSK', 'KSSSSSK', '.KKKKK.'),
              ('.KKKKK.', 'KSSYSSK', 'KGSKSRK', 'KSSKSSK', 'KSSSSSK', 'KSSSSSK', '.KKKKK.'),
              ('.KKKKK.', 'KSSYSSK', 'KGSSKRK', 'KSSKSSK', 'KSSSSSK', 'KSSSSSK', '.KKKKK.')),
    'vent': (('KKKKKKKKK', 'KOKOKOKOK', 'KKKKKKKKK'),),
    'puff': (('.WWW.', 'WWWWW', '.WWW.', '..W..'), ('..W..', '.WWW.', '..W..')),
    # space
    'sat': (('......Y......', '......K......', 'KKKK.KKK.KKKK', 'KSBK.KYK.KBSK', 'KBSK.KYK.KSBK', 'KSBKKKKKKKBSK', 'KKKK.KKK.KKKK'),
            ('......Y......', '......K......', 'KKKK.KKK.KKKK', 'KBSK.KYK.KSBK', 'KSBK.KYK.KBSK', 'KBSKKKKKKKSBK', 'KKKK.KKK.KKKK')),
    'rocket': (('..R..', '.KRK.', 'KWWWK', 'KWSWK', 'KWWWK', 'KRRRK', 'KR.RK', '.Y.Y.', '..Y..'),
               ('..R..', '.KRK.', 'KWWWK', 'KWSWK', 'KWWWK', 'KRRRK', 'KR.RK', '.O.O.', '.OYO.')),
    'astro': (('..KKKKK..', '.KWWWWWK.', 'KWSSSSSWK', 'KWSKSKSWK', 'KWSSSSSWK', '.KWWWWWK.', '.KWRWYWK.', 'KWWWWWWWK', '.KWK.KWK.', '.KKK.KKK.'),),
    'asteroid': (('.KKK.', 'KOYOK', 'KONOK', 'KNOOK', '.KKK.'),),
    'moon': (('..KKK..', '.KWWWK.', 'KWSWWWK', 'KWWWSWK', 'KWSWWWK', '.KWWWK.', '..KKK..'),),
    'comet': (('.........SWW..', '....BBSSSWYWW.', '..BBSSSWWYYWW.', '....BBSSSWYWW.', '.........SWW..'),),
    # candy
    'donut': (('..KKKKK..', '.KPPYPPK.', 'KPPPPPSPK', 'KPSKKKPPK', 'KPPK.KPYK', 'KPYKKKPPK', 'KPPPPSPPK', '.KPPPPPK.', '..KKKKK..'),),
    'gumball': (('.KKK.', 'KGWGK', 'KGGGK', 'KGGGK', '.KKK.'),),
    'ginger': (('...KKKKK...', '..KOOOOOK..', '..KOWOWOK..', '..KOWWWOK..', '.KKOOOOOKK.', 'KOOOOOOOOOK', 'KOOKOROKOOK',
                '.KKKOOOKKK.', '...KOROK...', '..KOOOOOK..', '..KOK.KOK..', '..KKK.KKK..'),),
    'cookie': (('..KKK..', '.KOOOK.', 'KONOOOK', 'KOOOONK', 'KONOOOK', '.KOOOK.', '..KKK..'),),
    # aquarium
    'seaweed': (SEAWEED, tuple(row[::-1] for row in SEAWEED)),
    'chest': (('.KKKKKKKKK.', 'KOOOOOOOOOK', 'KOOOOOOOOOK', 'KKKKKYKKKKK', 'KNNNNYNNNNK', 'KNNNNNNNNNK', 'KNNNNNNNNNK', '.KKKKKKKKK.'),) * 4
             + (('..YWY.YWY..', '.KYYYYYYYK.', 'KYYYYYYYYYK', 'KKKKKYKKKKK', 'KNNNNYNNNNK', 'KNNNNNNNNNK', 'KNNNNNNNNNK', '.KKKKKKKKK.'),) * 2,
    'starfish': (('...K...', '..KOK..', 'KKKOKKK', '.KOYOK.', '.KOOOK.', 'KOK.KOK', 'KK...KK'),),
    'jelly': (('..KKKKK..', '.KPPPPPK.', 'KPWPPPPPK', 'KPKPPPKPK', 'KPPPPPPPK', '.KKKKKKK.', '.P.P.P.P.', '.P.P.P.P.', '..P.P.P..'),
              ('..KKKKK..', '.KPPPPPK.', 'KPWPPPPPK', 'KPKPPPKPK', 'KPPPPPPPK', '.KKKKKKK.', 'P.P.P.P..', '.P.P.P.P.', 'P.P.P.P..')),
    'crab': (('.K.....K.', '.W.....W.', 'KKOOOOOKK', 'KOOOKOOOK', '.K.K.K.K.'), ('.K.....K.', '.W.....W.', 'KKOOOOOKK', 'KOOOKOOOK', 'K..K.K..K')),
    'bubble2': (('.WWW.', 'W...W', 'W...W', 'W...W', '.WWW.'),),
    # meadow
    'frog': (('.KK.KK.', 'KWKGKWK', 'KGGGGGK', 'KGKKKGK', '.KGGGK.'), ('.KK.KK.', 'KGKGKGK', 'KGGGGGK', 'KGKKKGK', '.KGGGK.')),
    'lily': (('.KKKKK.', 'KGGGGGK', '.KKKKK.'),),
    'dragonfly': (('..W.W..', 'SSBBBBK', '..W.W..'), ('.......', 'SSBBBBK', '.WW.WW.')),
    'sunflower': (SUNFLOWER, SUNFLOWER_SWAY),
    'bunny': (BUNNY + ('.KKK.KKK.',), BUNNY[:4] + ('KWWWWWWWK',) + BUNNY[5:] + ('KK.K.K.KK',)),
    'bee': (('.W.W.', 'YKYKY', 'YKYKY', '..K..'), ('.....', 'YKYKY', 'YKYKY', '.W.W.')),
    'butterfly': (('MM.K.MM', 'MPMKMPM', '.MPKPM.', '.MMKMM.', '..K.K..'), ('..MKM..', '..MKM..', '..MKM..', '..MKM..', '..K.K..')),
    'bush': (('...KKKKK...', '.KKGGGGGKK.', 'KGGGGMGGGGK', 'KGMGGGGGMGK', 'KGGGGGGGGGK', '.KKKKKKKKK.'),),
    # crystal cave
    'stalactite': (('KVVVVVK', '.KVMVK.', '.KVVVK.', '..KVK..', '..KVK..', '...K...'),),
    'stalagmite': (('...K...', '..KVK..', '..KVK..', '.KVVVK.', '.KVMVK.', 'KVVVVVK'),),
    'bat': (('NN.....NN', 'NMN.K.NMN', 'NMMYNYMMN', '.NMNNNMN.', '..N.N.N..'),
            ('....K....', '.N.NNN.N.', 'NMNYNYNMN', 'NMMNNNMMN', 'N.N...N.N')),
    'eyes': (EYES_OPEN,) * 6 + (EYES_SHUT,),
    'orb': (('..S..', '.SWS.', 'SWWWS', '.SWS.', '..S..'), ('.....', '..S..', '.SWS.', '..S..', '.....')),
    'glowshroom': (('.SWS.', 'SSSSS', 'KKKKK', '..V..', '..V..', '.VVV.'), ('.BSB.', 'BBBBB', 'KKKKK', '..V..', '..V..', '.VVV.')),
}


# --- drawn-by-rule pictures: too big or too round to type out, so a few lines of drawing code make them (still named sprites) ---
def blank(width, height):
    return np.full((height, width), -1, dtype=np.int8)


def gen_belt():
    """The workshop conveyor, sixty pixels wide: steel rails, a dark belt and yellow chevrons that slide two pixels a frame."""
    frames = []
    for shift in range(0, 8, 2):
        art = blank(60, 6)
        art[0, :], art[5, :], art[1, :], art[4, :], art[2:4, :] = BLACK, BLACK, SKY, PURPLE, BLACK
        for x in range(60):
            if (x - shift) % 8 in (0, 1):
                art[2, x] = YELLOW
            if (x - shift) % 8 in (1, 2):
                art[3, x] = YELLOW
        frames.append(art)
    return tuple(frames)


def gen_pipe():
    """A blue steam pipe along the top of the power plant, lit on top, with a riveted flange every fifteen pixels."""
    art = blank(60, 7)
    art[1, :], art[5, :], art[2, :], art[3, :], art[4, :] = BLACK, BLACK, SKY, BLUE, PURPLE
    for x in range(60):
        if x % 15 in (6, 7, 8):
            art[0, x], art[6, x] = BLACK, BLACK
            art[1:6, x] = YELLOW if x % 15 == 7 else ORANGE
    return (art,)


def gen_fan():
    """A turbine seen from above: blue housing, four yellow blades turned a quarter-eighth each frame, a red hub."""
    frames = []
    for turn in range(4):
        art = blank(13, 13)
        for y in range(13):
            for x in range(13):
                dx, dy = x - 6, y - 6
                radius = hypot(dx, dy)
                if radius > 6.4:
                    continue
                if radius > 5.5:
                    art[y, x] = BLACK
                elif radius > 4.5:
                    art[y, x] = BLUE
                else:
                    art[y, x] = MAROON
                    quarter = ((np.arctan2(dy, dx) - turn * pi / 8) * 2 / pi + .5) % 1 - .5
                    if radius > 1.6 and abs(quarter) * radius * pi / 2 < 1.4:
                        art[y, x] = YELLOW
                    if radius <= 1.6:
                        art[y, x] = RED if radius > .8 else BLACK
        frames.append(art)
    return tuple(frames)


def planet_art(radius, body, light, dark, ring=None):
    """A shaded ball with a lit upper-left, a dark lower-right and a couple of cloud bands; `ring` = (front, back) colours."""
    width, height = int(radius * (4.4 if ring else 2)) + 3, 2 * radius + 3 + (2 if ring else 0)
    art = blank(width, height)
    cx, cy = (width - 1) / 2, (height - 1) / 2

    def on_ring(x, y):
        return .62 <= ((x - cx) / (2.1 * radius)) ** 2 + ((y - cy) / (.55 * radius)) ** 2 <= 1.0

    for y in range(height):
        for x in range(width):
            if ring and y < cy and on_ring(x, y) and hypot(x - cx, y - cy) > radius + .5:
                art[y, x] = ring[1]
    for y in range(height):
        for x in range(width):
            distance = hypot(x - cx, y - cy)
            if distance <= radius + .5:
                tilt = (x - cx + y - cy)
                colour = light if tilt < -.55 * radius else dark if tilt > .6 * radius else body
                if int(y + radius) % 5 == 3 and colour == body:
                    colour = dark
                art[y, x] = colour
    for y in range(height):
        for x in range(width):
            if ring and y >= cy and on_ring(x, y):
                art[y, x] = ring[0]
    return art


def gen_galaxy():
    """A small spiral galaxy: a bright core and two sky-blue arms in half-tone, the half-tone flipping so it seems to turn."""
    frames = []
    for flip in range(2):
        art = blank(15, 15)
        for y in range(15):
            for x in range(15):
                dx, dy = x - 7, y - 7
                radius = hypot(dx, dy)
                if radius > 7.4:
                    continue
                arm = abs(np.sin((np.arctan2(dy, dx) + radius * .55) * 2))
                if radius < 1.6:
                    art[y, x] = WHITE
                elif radius < 3:
                    art[y, x] = YELLOW
                elif arm > .55 and (x + y + flip) % 2 == 0:
                    art[y, x] = SKY if radius < 5.5 else BLUE
                elif arm > .85:
                    art[y, x] = PURPLE
        frames.append(art)
    return tuple(frames)


def gen_rug():
    """The kitchen rug: black edge, red border, blue field with a white lattice, yellow fringe at both ends."""
    width, height = 24, 15
    art = blank(width, height)
    for y in range(height):
        for x in range(2, width - 2):
            edge = min(x - 2, width - 3 - x, y, height - 1 - y)
            art[y, x] = BLACK if edge == 0 else RED if edge in (1, 2) else YELLOW if edge == 3 else BLUE
            if edge > 3 and ((x + y) % 6 == 0 or (x - y) % 6 == 0):
                art[y, x] = WHITE
            reach = abs(x - 11.5) + 1.4 * abs(y - 7)               # a diamond medallion in the middle of the field
            if edge > 3 and reach < 6.5:
                art[y, x] = BLACK if reach > 5.5 else YELLOW if reach > 3.5 else RED if reach > 1.8 else YELLOW
        if y % 2 == 0:
            art[y, 0], art[y, width - 1] = YELLOW, YELLOW
    return (art,)


def water_art(width, height, water, light, shore, frame):
    """An oval of water with a ring of shore and shimmering highlights that shift with the frame."""
    art = blank(width, height)
    for y in range(height):
        for x in range(width):
            e = ((x - (width - 1) / 2) / (width / 2)) ** 2 + ((y - (height - 1) / 2) / (height / 2)) ** 2
            if e > 1:
                continue
            art[y, x] = shore if e > .8 else water
            if e < .62 and (x // 2 + y * 2 + frame * 3) % 9 == 0:
                art[y, x] = light
    return art


def gen_pond():
    return tuple(water_art(24, 15, BLUE, WHITE, YELLOW, frame) for frame in range(3))


def gen_pool():
    return tuple(water_art(13, 8, SKY, WHITE, BLUE, frame) for frame in range(3))


def gen_swirl():
    """A big spiral lollipop top: purple and yellow arms that turn half an arm each frame."""
    frames = []
    for turn in range(2):
        art = blank(19, 19)
        for y in range(19):
            for x in range(19):
                dx, dy = x - 9, y - 9
                radius = hypot(dx, dy)
                if radius > 9.4:
                    continue
                phase = (np.arctan2(dy, dx) / (2 * pi) * 3 + radius / 4.2 + turn * .5) % 1
                art[y, x] = BLACK if radius > 8.4 else WHITE if radius < 1.5 else YELLOW if phase < .5 else PURPLE
        frames.append(art)
    return tuple(frames)


def gen_whale():
    """A big purple whale with a white belly, an eye, a flipper and a tail that flicks up and down between two frames."""
    tail = ('K......', 'KK.....', 'KBK....', 'KBBK...', '.KBBKKK', '..KBBBB', '..KBBBB', '..KKKKK')
    frames = []
    for flip in (False, True):
        art = blank(24, 12)
        for y in range(12):
            for x in range(24):
                e = ((x - 15) / 8.6) ** 2 + ((y - 5.5) / 4.8) ** 2
                if e <= 1:
                    art[y, x] = BLACK if e > .74 else WHITE if y >= 8 else PURPLE
        for y, row in enumerate(tail):
            for x, ch in enumerate(row):
                if ch != '.':
                    art[11 - y if flip else y, x] = BLACK if ch == 'K' else PURPLE
        art[4:6, 20:22], art[7, 19:23] = BLACK, BLACK    # a two-pixel eye with a glint
        art[4, 20] = WHITE
        art[8, 12:16], art[9, 13:15], art[10, 13] = BLACK, PURPLE, BLACK
        frames.append(art)
    return tuple(frames)


GEN = {'belt': gen_belt, 'pipe': gen_pipe, 'fan': gen_fan, 'galaxy': gen_galaxy, 'rug': gen_rug, 'pond': gen_pond, 'pool': gen_pool,
       'swirl': gen_swirl, 'whale': gen_whale,
       'mars': lambda: (planet_art(5, ORANGE, YELLOW, MAROON, ring=(WHITE, SKY)),),
       'ice': lambda: (planet_art(4, SKY, WHITE, BLUE),), 'rock': lambda: (planet_art(3, MAGENTA, PINK, PURPLE),)}


def lib(name, swap=None):
    if name in GEN:
        return GEN[name]()
    return tuple(pic(rows, swap) for rows in LIB[name])


# --- floors, frame and posts -------------------------------------------------------------------------------------
# Pass 3: no more checkers. Each stage lays its own floor. A floor is one flat sprite; these functions get the pixel coordinates
# of the whole floor (xx, yy) and return the colour of every pixel, so a texture is a rule, not thousands of typed numbers.
def floor_slab(xx, yy):
    """Workshop: painted concrete slabs with lit, bevelled joints, paint chips and a dashed yellow safety line inside the wall."""
    art = np.full(xx.shape, BLUE, dtype=np.int8)
    art[(xx % 24 == 0) | (yy % 24 == 0)] = PURPLE          # one quiet joint line a step darker than the slab, no speckle
    right, bottom = xx.max() - 3, yy.max() - 3
    along = ((yy == 3) | (yy == bottom)) & (xx >= 3) & (xx <= right)
    down = ((xx == 3) | (xx == right)) & (yy >= 3) & (yy <= bottom)
    art[(along | down) & ((xx + yy) % 8 < 3)] = YELLOW
    return art


def floor_tiles(xx, yy):
    """Kitchen: big white tiles with pale-blue grout, a blue plus where four meet and a small yellow diamond in every other tile."""
    art = np.full(xx.shape, WHITE, dtype=np.int8)
    art[(xx % 18 == 0) | (yy % 18 == 0)] = SKY            # pale grout only: no pluses, no diamonds
    return art


def floor_icing(xx, yy):
    """Candy: pink frosting with a wavy magenta piping line every twelve pixels, a white gloss above it and a little drip under it."""
    art = np.full(xx.shape, PINK, dtype=np.int8)
    line = (yy + np.round(2 * np.sin(xx / 5.0)).astype(int)) % 24
    art[line == 0] = MAGENTA                                # one wavy piping line, widely spaced; no gloss
    return art


def floor_grate(xx, yy):
    """Power plant: black steel grating, maroon bars every third pixel, black plate seams every twelve and a yellow rivet at each crossing."""
    art = np.full(xx.shape, BLACK, dtype=np.int8)
    art[xx % 6 == 1] = MAROON                               # a bar every sixth pixel; no rivets, no seams
    return art


def floor_nebula(xx, yy):
    """Space: deep black with half-toned haze of purple, magenta and blue drifting in broad patches."""
    cloud = np.sin(xx * .13 + 1) + np.sin(yy * .11) + np.sin((xx + yy) * .07) + np.sin((xx - yy) * .05 + 2)
    art = np.full(xx.shape, BLACK, dtype=np.int8)
    art[(cloud > 1.3) & ((xx + yy) % 2 == 0)] = PURPLE      # one hue, only in the densest patches
    return art


def floor_water(xx, yy):
    """Aquarium: light water with rows of blue ripples and white glints, never in a grid."""
    art = np.full(xx.shape, SKY, dtype=np.int8)
    shifted = yy + np.round(1.5 * np.sin(xx / 4.0)).astype(int)         # the ripple rows bend with the wave, band by band
    band, line = shifted // 8, shifted % 8
    art[(line == 0) & (band % 2 == 0) & ((xx + band * 5) % 16 < 6)] = BLUE
    return art


def floor_lawn(xx, yy):
    """Meadow: green grass in mown stripes; every other stripe is flecked yellow where the sun hits it."""
    art = np.full(xx.shape, GREEN, dtype=np.int8)
    return art


def floor_cobble(xx, yy):
    """Crystal cave: rough paving, courses of purple stones (a few blue) with a pink lit top edge, maroon underside and black mortar."""
    shifted = xx + (yy // 6 % 2) * 5
    across, down = shifted % 10, yy % 6
    art = np.full(xx.shape, PURPLE, dtype=np.int8)
    art[(across == 9) | (down == 0)] = MAROON               # plain purple stones with one maroon mortar line
    return art


FLOORS = {'slab': floor_slab, 'tiles': floor_tiles, 'icing': floor_icing, 'grate': floor_grate, 'nebula': floor_nebula,
          'water': floor_water, 'lawn': floor_lawn, 'cobble': floor_cobble}
# When the run is over every floor is re-coloured, pattern kept: light colours turn red or maroon, dark ones black.
ALARM_COLOURS = {WHITE: RED, SKY: MAROON, YELLOW: MAROON, PINK: MAROON, ORANGE: MAROON, GREEN: MAROON, MAGENTA: MAROON,
                 BLUE: BLACK, PURPLE: BLACK, MAROON: BLACK}


def floor_art(width, height, scene, alarm=False):
    """One flat sprite the size of the room: the stage's own texture plus a one-pixel inset shadow along the top and left."""
    yy, xx = np.mgrid[0:height * CELL, 0:width * CELL]
    art = FLOORS[scene['floor']](xx, yy).astype(np.int8)
    if alarm:
        art = np.vectorize(lambda value: ALARM_COLOURS.get(int(value), int(value)), otypes=[np.int8])(art)
    art[0, :], art[:, 0] = BLACK, BLACK
    return art


def rim_colour(kind, one, two, x, y):
    if kind == 'hazard':
        return YELLOW if ((x + y) // 2) % 2 else BLACK
    if kind == 'stripe':
        return RED if ((x + y) // 2) % 2 else WHITE
    if kind == 'dash':
        return one if (x + y) % 4 < 2 else two
    return one


def frame_art(height, scene, alarm=False):
    """The two-pixel border and, on nine-tall stages, the shelf wall that fills the strip under the floor."""
    art = np.full((64, 64), -1, dtype=np.int8)
    bottom = 2 + CELL * height
    kind, one, two = scene['rim']
    for y in range(64):
        for x in range(64):
            if 2 <= x < 62 and 2 <= y < bottom:
                continue
            ring = min(x, y, 63 - x, 63 - y if bottom >= 62 else 99)
            if bottom < 62 and y >= bottom:
                wall, line, board = scene['shelf']['wall']
                colour = board if y == 63 else shade_of(wall) if y == bottom else wall
                if y not in (bottom, 63) and (x + 2 * (y // 3)) % 6 == 0:
                    colour = line
            elif ring == 0:
                colour = BLACK
            else:
                colour = rim_colour(kind, one, two, x, y)
            art[y, x] = colour
    if alarm:
        art = np.where(art < 0, art, np.where(np.isin(art, PALE), RED, np.where(art == BLACK, BLACK, MAROON))).astype(np.int8)
    return art


def shade_of(colour):
    return {WHITE: SKY, SKY: BLUE, YELLOW: ORANGE, ORANGE: MAROON, BLUE: PURPLE, PURPLE: BLACK, MAROON: BLACK,
            MAGENTA: PURPLE, RED: MAROON, PINK: MAGENTA, GREEN: BLACK}.get(colour, BLACK)


def post_art(width, height, style):
    """One standing column: the lit left edge, the shaded right edge and a material that changes with the stage."""
    kind, body, light, dark, mark = style
    art = np.full((height, width), body, dtype=np.int8)
    for y in range(height):
        for x in range(width):
            if kind in ('hazard', 'candy'):
                art[y, x] = mark if ((x + y) // 2) % 2 else body
            elif kind == 'bands' and y % 8 in (3, 4):
                art[y, x] = mark
            elif kind == 'windows' and y % 5 == 2 and 0 < x < width - 1:
                art[y, x] = mark
            elif kind == 'bark' and (x + 2 * (y // 3)) % 3 == 0:
                art[y, x] = mark
            elif kind == 'facets' and (y + 2 * x) % 7 == 0:
                art[y, x] = mark
            elif kind == 'coral' and (x * 3 + y * 5) % 7 == 0:
                art[y, x] = mark
    art[:, 0], art[:, -1] = light, dark
    art[0, :], art[-1, :] = light, dark
    if width > 3:
        art[0, 1:-1] = mark if kind in ('bands', 'bark') else light
    return art


# --- the cast -----------------------------------------------------------------------------------------------------
# Pass 2: the rover is nine pixels wide (it was seven) so its face can really show happy, blinking, wincing, cheering and
# sad. Rows: antenna, top edge, eyes (two rows), cheeks and smile corners, mouth bar, belt, bottom edge, feet.
#   G body (swapped per stage so it never melts into the floor), Z belt, P cheek, S tear, R mouth or lamp.
FACES = {
    'ok':    ('KWKWGKWGK', 'KGKKGKKGK', 'KPKGGGKPK', 'KGGKKKGGK', 'KZZZZZZZK'),
    'blink': ('KWGGGGGGK', 'KGKKGKKGK', 'KPKGGGKPK', 'KGGKKKGGK', 'KZZZZZZZK'),
    'wince': ('KWKGGGKGK', 'KGGKGKGGK', 'KPGKKKGPK', 'KGKGGGKGK', 'KZZZZZZZK'),
    'dead':  ('KWKGGGKGK', 'KGGKGKGSK', 'KPGKKKGPK', 'KGKGGGKGK', 'KZZZZZZZK'),
    'win':   ('KWGKGKGGK', 'KGKGGGKGK', 'KPKRRRKPK', 'KGGKKKGGK', 'KZZZZZZZK'),
}
BACK = {'ok': ('KWKKGKKGK', 'KGKWGKWGK'), 'blink': ('KWGGGGGGK', 'KGGGGGGGK')}
BACK_TAIL = ('KGGGGGGGK', 'KGKYYYKGK', 'KZZZZZZZK')
FEET = ('.KOK.KOK.', '..KOKOK..')


@lru_cache(maxsize=None)
def rover_art(facing, carrying, expression, foot, body='G', lamp='R', squash=False):
    """The robot at nine pixels: a face that looks where it is going and reacts (blink, wince at a refused move, cheer on a win,
    droop and cry when the run is over), feet that alternate, and the glowing core on its head while it carries it."""
    head = ('..KYWYK..' if carrying else '...K' + (lamp if expression != 'win' else 'Y') + 'K...', '.KKKKKKK.')
    if facing == (0, -1):
        face = (BACK.get(expression) or FACES[expression][:2]) + BACK_TAIL
    else:
        face = FACES[expression]
    rows = list(head + tuple(face) + ('.KKKKKKK.', FEET[foot]))
    if facing in ((-1, 0), (1, 0)):
        # Profile: the whole face slides one pixel toward the way the robot is heading.
        rows = rows[:2] + ['K' + row[2:8] + 'G' + 'K' for row in rows[2:7]] + rows[7:]
        if facing == (1, 0):
            rows = [row[::-1] for row in rows]
    if squash:
        rows.pop(1)            # a squashed rover loses its top outline row: eight pixels tall, feet kept on the ground
    dead = expression == 'dead'
    return pic(rows, {'G': 'R' if dead else body, 'Z': 'O' if dead else 'Y'})


CORE = (('..KKKKK..', '.KYWWYYK.', 'KYWYYYYYK', 'KYKWYKWYK', 'KYKKYKKYK', 'KOYYYYYOK', 'KOKYYYKOK', '.KOKKKOK.', '..KKKKK..'),
        ('W.KKKKK.W', '.KYWWYYK.', 'KYWYYYYYK', 'KYKWYKWYK', 'KYKKYKKYK', 'KOYYYYYOK', 'KOKYYYKOK', '.KOKKKOK.', 'W.KKKKK.W'),
        ('..KKKKK..', '.KYWWYYK.', 'KYWYYYYYK', 'KYYYYYYYK', 'KYKKYKKYK', 'KOYYYYYOK', 'KOKYYYKOK', '.KOKKKOK.', '..KKKKK..'))
# The dock is a charging bay with a face. Pass 3: it is fifteen pixels tall and the rover (nine) parks in the lower nine rows, so the
# canopy with its two lamp eyes and vent mouth is always in view. 'E' is the lamp colour (amber, red when the run is over, green on a win).
DOCK = ('..KKKKKKKKK..', '.KSSSSSSSSSK.', 'KSWWSSSSSSSVK', 'KSEEESSSEEEVK', 'KSEKESSSEKEVK', 'KSEEESSSEEEVK', 'KSSSKKKKKSSVK',
        'KSBBBBBBBBBVK', 'KSBBBBBBBBBVK', 'KSBBBBBBBBBVK', 'KSBBBBBBBBBVK', 'KSBBBBBBBBBVK', 'KSBBBBBBBBBVK', 'KSYKYKYKYKYVK',
        'KKKKKKKKKKKKK')
HOOD = ('..KKKKK..', '.KSWWSSK.', 'KSWSSSSSK', 'KKKKKKKKK', 'KKLKKKLKK', 'KKKKKKKKK', 'KSSSSSSSK', 'KYKOKYKOK', '.KKKKKKK.')
BLADE_DEAD_ROWS = ('..KKK..', '.KRRRK.', 'KRWRWRK', 'KRRKRRK', 'KRKRKRK', '.KRRRK.', '..KKK..')


def blade_frames():
    """Spinning saw, 7 pixels like the old one: the same disc twice, teeth and body swapped so the edge seems to turn."""
    first = pic(('..KKK..', '.KWRWK.', 'KWRRRWK', 'KRRKRRK', 'KWRRRWK', '.KWRWK.', '..KKK..'))
    second = first.copy()
    for y in range(7):
        for x in range(7):
            if 2 <= x <= 4 and 2 <= y <= 4:
                continue
            second[y, x] = {WHITE: RED, RED: WHITE}.get(int(first[y, x]), first[y, x])
    return first, second


# Pass 3: a saw is drawn as wide as it hits. The big ones (hit radius .35) stay seven pixels; the little ones (.25) are five.
SMALL_BLADES = (pic(('.KKK.', 'KWRWK', 'KRKRK', 'KWRWK', '.KKK.')), pic(('.KKK.', 'KRWRK', 'KWKWK', 'KRWRK', '.KKK.')),
                pic(('.KKK.', 'KRRRK', 'KRWRK', 'KRRRK', '.KKK.')))


BLADE_PICS = blade_frames()


def blade_set(radius):
    """(frame a, frame b, run-over picture) for a saw of this hit radius."""
    return SMALL_BLADES if radius < .3 else BLADE_PICS + (BLADE_DEAD_PIC,)


CORE_PICS = tuple(pic(rows) for rows in CORE)
BLADE_DEAD_PIC = pic(BLADE_DEAD_ROWS)


def scene_body(scene):
    """The robot's body colour: green everywhere except the meadow, where it would vanish, so it is sky blue there."""
    return 'S' if scene['name'] == 'meadow' else 'G'


def hood_pic(latched, blink):
    rows = list(HOOD)
    if latched or blink:
        rows[4] = 'KKKKKKKKK'
    return pic(rows, {'L': 'G' if latched else 'O'})


def spool_art(remaining):
    """The cable reel is the counter: a real reel seen from the side, two flanges around a barrel of wound cable, with a plug that
    reaches down to the dock canopy. The cable left on it fills the barrel from the bottom up, one wound pixel at a time."""
    art = np.full((11, 9), -1, dtype=np.int8)
    art[:9] = pic(('KKKKKKKKK', 'KSSSSSSSK', 'KKBBBBBKK', 'KKBBBBBKK', 'KKBBBBBKK', 'KKBBBBBKK', 'KKBBBBBKK', 'KSSSSSSSK', 'KKKKKKKKK'))
    wound = round(35 * remaining)
    for n in range(wound):
        row, column = 6 - n // 5, 2 + n % 5
        art[row, column] = ORANGE if (row + column) % 2 else YELLOW
    art[1, 1:3] = WHITE
    art[9, 3:6], art[10, 3:6] = (BLACK, ORANGE, BLACK), (BLACK, BLACK, BLACK)
    return art


def cue_art(dead, radius, colour, beat):
    """Contact marks: a spark burst where the blade struck; corner brackets where a move was refused."""
    art = np.full((9, 9), -1, dtype=np.int8)
    if dead:
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            art[4 + dy, 4 + dx] = RED
        for dx, dy in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            art[4 + dy, 4 + dx] = YELLOW if beat else WHITE
        return art
    for sx in (-1, 1):
        for sy in (-1, 1):
            art[4 + sy * radius, 4 + sx * radius] = WHITE
            art[4 + sy * radius, 4 + sx * (radius - 1)] = colour
            art[4 + sy * (radius - 1), 4 + sx * radius] = colour
    return art


def pad_art(outer, inner, size):
    """A floor plate under the core: two rings, the middle left open so the tiles show."""
    art = np.full((size, size), -1, dtype=np.int8)
    for y in range(size):
        for x in range(size):
            ring = min(x, y, size - 1 - x, size - 1 - y)
            corner = min(x, size - 1 - x) + min(y, size - 1 - y) < 2
            if not corner and ring == 0:
                art[y, x] = outer
            elif ring == 1 and (x + y) % 2 == 0 and not corner:
                art[y, x] = inner
    return art


STARS = (YELLOW, WHITE, SKY, ORANGE, GREEN, YELLOW, WHITE, SKY)
STAR_SHAPES = (('..C..', '.CWC.', 'CWWWC', '.CWC.', '..C..'), ('.....', '.C.C.', '..W..', '.C.C.', '.....'),
               ('..W..', '..W..', 'WWCWW', '..W..', '..W..'))


def spark_art(kind):
    """Win sparkles at five pixels (they were three): a fat star that shrinks to an x and a cross, in many colours."""
    shape = STAR_SHAPES[kind % 3]
    return np.array([[-1 if ch == '.' else (STARS[kind % 8] if ch == 'C' else WHITE) for ch in row] for row in shape], dtype=np.int8)


def smoke_art(size):
    return pic((('..WW..', '.WWWW.', 'WWWWWW', '.WWWW.'), ('..W..', '.WWW.', '..W..'))[size % 2])


CONFETTI = (YELLOW, SKY, PINK, GREEN, ORANGE, WHITE, MAGENTA, RED)


def confetti_art(kind):
    """A two-by-three paper scrap for the level-clear shower, in eight colours, two shapes."""
    colour = CONFETTI[kind % 8]
    return np.array([[colour, colour], [colour, -1], [-1, colour]] if kind % 2 else [[colour, colour], [colour, colour], [-1, -1]], dtype=np.int8)


SHARD_COLOURS = (YELLOW, WHITE, RED, ORANGE, YELLOW, WHITE)


# Round B motion pieces. Dust puffs: a plus, an x, then two last specks, all white.
DUST = tuple(pic_rows for pic_rows in (
    np.array([[-1 if ch == '.' else (WHITE if ch == 'W' else BLACK) for ch in row] for row in rows], dtype=np.int8)
    for rows in (('.KKK.', 'KWWWK', 'KWWWK', '.KKK.'),
                 ('KK...KK', 'KWK.KWK', 'KK...KK'),
                 ('K...K', '.....', 'K...K'))))
FRACTIONS = (0., .3, .8, 1.)           # how far along its step the rover is on each animation frame (ease-out)
HOP = (0, 0, -2, 0)                    # the leap, in pixels: crouch, up, then landing (squashed) on the last animation frame
SQUASH = (False, True, False, True)    # the rover is flattened by a pixel on the crouch and on the landing
SHAKE = ((0, 0), (2, 1), (-2, -1), (2, 0), (-1, 1), (1, 0), (0, 0))   # the whole screen shudders when the run is lost
TWANG = (3, -3, 2, -1, 1, 0)           # how far a plucked cable bows sideways, frame by frame
BUMP = (2, -1, 1, 0)                   # the nudge of a refused move, in pixels toward the way it was pushing
SIDEWAYS_REFUSALS = ('far', 'loaded', 'refused', 'undo-empty', 'reel-stop')
QUIET_FEEDBACK = ('ready', 'move', 'reel', 'pickup', 'push', 'latch')
WIPE_RADIUS = {4: 30, 5: 16, 6: 5}     # the closing iris on the last frames of a level clear
OPEN_RADIUS = {2: 6, 1: 22}            # ...and the opening iris on the next stage


def wipe_art(centre, radius):
    """A black screen with a round hole: an iris. Everything outside `radius` of `centre` is black."""
    yy, xx = np.ogrid[:64, :64]
    return np.where((xx - centre[0]) ** 2 + (yy - centre[1]) ** 2 > radius ** 2, BLACK, -1).astype(np.int8)


def corner_art(scene, alarm):
    """A riveted corner plate, drawn over the frame: gives the ten-tall stages (which have no shelf) a finished edge too."""
    colour = scene['rim'][1]
    art = pic(('KKKKK', 'KWCCK', 'KCKCK', 'KCCCK', 'KKKKK'), {'C': {YELLOW: 'Y', RED: 'R', WHITE: 'W', BLUE: 'B', MAROON: 'N'}.get(colour, 'Y')})
    if alarm:
        art = np.where(art == BLACK, BLACK, np.where(art == WHITE, RED, MAROON)).astype(np.int8)
    return art


# --- one scene per stage ------------------------------------------------------------------------------------------
def spread(name, count, seed, box, period=0, move=None, layer=-9, swap=None):
    """Scatter `count` copies of a library picture over a pixel box, reproducibly."""
    rng = random.Random(seed)
    return [dict(name=name, x=rng.randint(box[0], box[2]), y=rng.randint(box[1], box[3]), period=period,
                 phase=rng.randint(0, 5), move=move, layer=layer, swap=swap) for _ in range(count)]


def item(name, x, y, period=0, move=None, layer=-9, phase=0, swap=None):
    return dict(name=name, x=x, y=y, period=period, phase=phase, move=move, layer=layer, swap=swap)


def shelf(*stock):
    """Props standing on the shelf board of a nine-tall stage (bottom edge on row 62)."""
    return [item(name, x, 62 - len(LIB[name][0]) + 1, period=period, layer=-7, swap=swap)
            for name, x, period, swap in stock]


BOX = (4, 4, 56, 50)
SCENES = [
    # 1. WORKSHOP: concrete slabs, a conveyor of crates across the top, drums, an oil puddle, a welding robot, nuts on the floor.
    dict(name='workshop', pad=(YELLOW, BLACK), floor='slab', rim=('hazard', YELLOW, BLACK), bulbs=(YELLOW, WHITE),
         post=('hazard', YELLOW, WHITE, BLACK, BLACK),
         shelf=dict(wall=(MAROON, ORANGE, ORANGE)),
         decor=[item('belt', 2, 12, period=1),
                item('crate', 6, 6, move=('slide', 1, -8, 66)), item('crate', 36, 6, move=('slide', 1, -8, 66), swap={'Y': 'G', 'O': 'S'}),
                item('puddle', 14, 44, period=4), item('barrel', 52, 44), item('welder', 28, 44, period=1),
                item('nut', 34, 22), item('nut', 10, 38)]
         + shelf(('toolbox', 4, 0, None), ('lamp', 18, 4, None), ('buddy', 28, 4, None), ('gear', 44, 2, None))),
    # 2. KITCHEN: white tile, a rug, a cat that blinks, a mouse running the bottom, a rolling orange, a fly, a jam splat.
    dict(name='kitchen', pad=(RED, YELLOW), floor='tiles', rim=('stripe', RED, WHITE), bulbs=(RED, YELLOW),
         post=('bands', RED, WHITE, MAROON, YELLOW),
         shelf=dict(wall=(YELLOW, ORANGE, MAROON)),
         decor=[item('rug', 36, 40), item('cat', 4, 6, period=3),
                item('orange', 24, 24, period=1, move=('slide', .5, 4, 56)), item('mouse', 0, 48, period=1, move=('slide', 1, -10, 64)),
                item('fly', 30, 14, period=1, move=('loop', 9, 5, 28), layer=-7)]
         + shelf(('pot', 3, 2, None), ('cake', 18, 0, None), ('cups', 28, 0, None), ('bottle', 50, 0, None))),
    # 3. POWER PLANT: grating, a steam pipe along the top, dials with swinging needles, a turbine, steam vents, flickering bolts.
    dict(name='power-plant', pad=(YELLOW, BLACK), floor='grate', rim=('hazard', YELLOW, BLACK), bulbs=(RED, YELLOW),
         post=('bands', BLUE, SKY, BLACK, YELLOW),
         shelf=dict(wall=(BLUE, SKY, YELLOW)),
         decor=[item('pipe', 2, 3), item('gauge', 14, 12, period=3), item('gauge', 36, 12, period=3, phase=2),
                item('fan', 42, 40, period=1), item('vent', 25, 46),
                item('puff', 26, 44, period=3, move=('rise', 16)), item('puff', 27, 44, period=3, move=('rise', 16), phase=3)]
         + spread('bolt', 2, 5, BOX, period=3)
         + shelf(('tesla', 3, 1, None), ('fuse', 15, 3, None), ('battery', 28, 0, None), ('beacon', 46, 2, None))),
    # 4. SPACE: nebula haze, a spiral galaxy, a ringed planet with a moon that goes round it, a comet, a rocket, a satellite, an astronaut.
    dict(name='space', pad=(SKY, BLUE), floor='nebula', rim=('dash', BLUE, PURPLE), bulbs=(SKY, WHITE),
         post=('windows', PURPLE, WHITE, BLACK, SKY), shelf=None,
         decor=[item('galaxy', 8, 8, period=3), item('ice', 24, 6), item('rock', 52, 32), item('mars', 33, 42), item('moon', 42, 46, move=('loop', 14, 6, 40)),
                item('comet', -14, 6, period=1, move=('glide', 2, -14, 66, .3)),
                item('rocket', 26, 56, period=1, move=('drift', -1, -12, 66)),
                item('astro', 26, 30, move=('loop', 3, 5, 36)),
                item('saucer', 8, 30, period=2, move=('slide', 1, 6, 56))]
         + spread('asteroid', 2, 23, BOX, move=('loop', 3, 2, 30))
         + spread('star', 5, 21, BOX, period=1) + spread('star', 4, 22, BOX, period=1, swap={'Y': 'S'})),
    # 5. CANDY: frosting floor, a spinning lollipop swirl, a donut, a gingerbread man, cookies, gumballs bobbing about.
    dict(name='candy', pad=(WHITE, YELLOW), floor='icing', rim=('stripe', WHITE, RED), bulbs=(YELLOW, WHITE),
         post=('candy', WHITE, WHITE, MAROON, RED),
         shelf=dict(wall=(SKY, WHITE, YELLOW)),
         decor=[item('swirl', 6, 4, period=2), item('donut', 28, 8), item('ginger', 50, 42), item('cookie', 24, 48),
                item('gumball', 26, 22, swap={'G': 'S'}, move=('bob', 2, 10)),
                item('gumball', 50, 34, swap={'G': 'Y'}, move=('bob', 2, 10), phase=4),
                ]
         + shelf(('jar-red', 3, 0, None), ('cupcake', 22, 0, None), ('jar-green', 40, 0, None),
                 ('cane', 53, 0, None))
         + spread('sprinkle', 4, 8, BOX, period=3)),
    # 6. AQUARIUM: water light on the floor, a big whale gliding by, a crab, a chest that opens, seaweed, starfish, jellyfish, fish, bubbles.
    dict(name='aquarium', pad=(WHITE, YELLOW), floor='water', rim=('dash', YELLOW, ORANGE), bulbs=(WHITE, SKY),
         post=('coral', MAGENTA, PINK, PURPLE, YELLOW), shelf=None,
         decor=spread('bubble', 4, 32, BOX, period=1, move=('rise', 24))
         + [item('whale', -8, 22, period=1, move=('slide', .5, -26, 64)),
            item('seaweed', 26, 46, period=3), item('seaweed', 38, 47, period=3, phase=2), item('seaweed', 56, 34, period=3, phase=1),
            item('chest', 50, 52, period=3), item('starfish', 36, 54),
            item('jelly', 24, 12, period=3, move=('bob', 3, 14)),
            item('crab', 0, 56, period=2, move=('slide', 1, -9, 64)),
            item('fish', 6, 12, period=2, move=('slide', 1, 4, 56))]),
    # 7. MEADOW: mown lawn, a pond with lily pads, a frog and a dragonfly, sunflowers, a hopping bunny, a bee, butterflies, bushes, flowers.
    dict(name='meadow', pad=(WHITE, MAROON), floor='lawn', rim=('dash', WHITE, MAROON), bulbs=(WHITE, YELLOW),
         post=('bark', MAROON, ORANGE, BLACK, BLACK), shelf=None,
         decor=[item('pond', 4, 6, period=3), item('lily', 8, 11, layer=-8), item('lily', 16, 9, layer=-8),
                item('frog', 16, 5, period=5, layer=-7), item('dragonfly', 18, 14, period=1, move=('loop', 8, 3, 18), layer=-7),
                item('sunflower', 38, 8, period=3), item('sunflower', 54, 38, period=3, phase=2),
                item('bunny', 0, 46, period=2, move=('slide', .5, -10, 68)),
                item('bee', 28, 30, period=1, move=('loop', 6, 4, 22), layer=-7),
                item('butterfly', 44, 22, period=2, move=('loop', 10, 6, 34), swap={'M': 'S'}, layer=-7),
                item('bush', 30, 52), item('bush', 52, 52)]
         + spread('flower', 2, 41, BOX, period=3, swap={'P': 'W', 'R': 'O'}) + spread('flower', 2, 44, BOX, period=3, swap={'P': 'S', 'R': 'B'})
         + spread('tuft', 2, 46, BOX) + spread('mushroom', 1, 42, BOX)),
    # 8. CRYSTAL CAVE: cobbles, stalactites and stalagmites, crystals in three colours, bats, a glowing pool, glow-mushrooms, eyes in the dark.
    dict(name='crystal-cave', pad=(SKY, MAGENTA), floor='cobble', rim=('dash', MAROON, BLACK), bulbs=(SKY, MAGENTA),
         post=('facets', BLUE, SKY, BLACK, PURPLE), shelf=None,
         decor=[item('stalactite', 4, 2), item('stalactite', 30, 2), item('stalactite', 53, 2),
                item('stalagmite', 26, 56), item('stalagmite', 40, 56), item('eyes', 25, 36, period=3), item('pool', 37, 46, period=3),
                item('bat', 0, 12, period=1, move=('slide', 1.5, -9, 64)), item('bat', 30, 30, period=1, move=('slide', 1, -9, 64), phase=4),
                item('orb', 12, 20, period=2, move=('loop', 4, 6, 30)), item('orb', 44, 14, period=2, move=('loop', 5, 4, 24), phase=3)]
         + spread('crystal', 2, 51, BOX, period=3) + spread('crystal', 1, 53, BOX, period=3, swap={'S': 'M', 'B': 'V'})
         + spread('glowshroom', 2, 56, BOX, period=3) + spread('glow', 3, 52, BOX, period=1)),
]
for scene in SCENES:
    for entry in scene['decor']:
        entry.setdefault('swap', None)


def perimeter():
    """Every pixel of the outer ring, clockwise from the top-left corner."""
    return ([(x, 0) for x in range(64)] + [(63, y) for y in range(1, 64)]
            + [(x, 63) for x in range(62, -1, -1)] + [(0, y) for y in range(62, 0, -1)])


def bulb_frames(scene, alarm):
    """Chasing marquee bulbs on the outer ring: three phases normally, a red blink when the run is over."""
    frames = []
    for phase in range(3 if not alarm else 2):
        art = np.full((64, 64), -1, dtype=np.int8)
        for index, (x, y) in enumerate(perimeter()):
            if alarm:
                art[y, x] = RED if (index // 4 + phase) % 2 == 0 else -1
            elif (index + phase) % 12 == 0:
                art[y, x] = scene['bulbs'][(index // 12) % 2]
        frames.append(art)
    return frames


class Te02(ARCBaseGame):
    def __init__(self):
        self.lvl, self.st = LEVELS[0], initial(LEVELS[0])
        self.animation, self.history, self.objects, self.keys, self.home, self.shaken = None, [], {}, {}, {}, False
        self.fx, self.tick, self.look, self.scene, self.life = None, 0, 'calm', SCENES[0], []
        self.intro, self.pending_intro = 0, 0
        levels = [Level(sprites=[], grid_size=(64, 64), data={}, name=level['name']) for level in LEVELS]
        super().__init__(game_id='te02', levels=levels, camera=Camera(0, 0, 64, 64, BLACK, BLACK),
                         win_score=len(levels), available_actions=[1, 2, 3, 4, 5, 6, 7])

    # --- sprite plumbing --------------------------------------------------------------------------------------
    def put(self, name, pixels, x, y, layer, tags=(), key=None):
        """Create the named sprite once, then only swap its picture (when `key` says it changed) and move it."""
        sprite = self.objects.get(name)
        self.home[name] = (round(x), round(y))       # where it belongs, so a screen shake can always put it back
        if sprite is None:
            sprite = Sprite(np.array(pixels, dtype=np.int8), name=name, x=round(x), y=round(y), layer=layer,
                            collidable=False, tags=list(tags))
            self.objects[name] = sprite
            self.keys[name] = key
            self.current_level.add_sprite(sprite)
        else:
            if key is None or self.keys.get(name) != key:
                sprite.pixels = np.array(pixels, dtype=np.int8)
                self.keys[name] = key
            sprite.set_position(round(x), round(y))
        return sprite

    def centered(self, name, pixels, point, layer, tags=(), key=None, shift=(0, 0)):
        art = np.asarray(pixels, dtype=np.int8)
        x, y = pixel(point)
        return self.put(name, art, x - art.shape[1] // 2 + shift[0], y - art.shape[0] // 2 + shift[1], layer, tags, key)

    # --- building a stage -------------------------------------------------------------------------------------
    def on_set_level(self, level):
        """All per-level state is made here, so the engine's own RESET refills the cable and restarts the stage."""
        self.lvl, self.scene = LEVELS[self.level_index], SCENES[self.level_index]
        self.st, self.animation, self.history = initial(self.lvl), None, []
        self.objects, self.keys, self.home, self.shaken, self.fx, self.tick, self.look = {}, {}, {}, False, None, 0, 'calm'
        self.intro, self.pending_intro = self.pending_intro, 0
        level.remove_all_sprites()
        width, height = self.lvl['size']
        scene = self.scene
        self.calm_floor = floor_art(width, height, scene)
        self.alarm_floor = floor_art(width, height, scene, alarm=True)
        self.calm_frame, self.alarm_frame = frame_art(height, scene), frame_art(height, scene, alarm=True)
        self.bulbs, self.bulbs_alarm = bulb_frames(scene, False), bulb_frames(scene, True)
        self.put('workshop-floor', self.calm_floor, OX, OY, -10, ('terrain',))
        self.put('border-frame', self.calm_frame, 0, 0, -8, ('scenery',))
        self.centered('core-pad', pad_art(*scene['pad'], 11), self.lvl['core'], -6, ('scenery',), key=0)
        # Riveted corner plates: all four on the ten-tall stages (no shelf), the top two where a shelf fills the bottom strip.
        self.calm_corner, self.alarm_corner = corner_art(scene, False), corner_art(scene, True)
        for number, (cx, cy) in enumerate(((0, 0), (59, 0), (0, 59), (59, 59))):
            if cy == 59 and height == 9:
                continue
            self.put(f'corner-{number}', self.calm_corner, cx, cy, -7, ('scenery',), key='calm')
        self.put('border-lights', self.bulbs[0], 0, 0, -8, ('scenery', 'lights'), key=0)
        self.life = []
        for number, entry in enumerate(scene['decor']):
            frames = lib(entry['name'], entry['swap'])
            name = f"{scene['name']}-{entry['name']}-{number}"
            self.put(name, frames[0], entry['x'], entry['y'], entry['layer'], ('scenery',), key=0)
            self.life.append((name, frames, entry))
        for number, (left, top, right, bottom) in enumerate(self.lvl['obstacles']):
            x, y = pixel((left, top))
            w, h = max(2, round((right - left) * CELL)), max(2, round((bottom - top) * CELL))
            self.put(f'post-{number}', post_art(w, h, scene['post']), x, y, 1, ('post', 'solid'))
            # a two-pixel half-tone shadow falls to the lower right of every post (hidden under the post itself)
            shadow = np.full((h + 2, w + 2), -1, dtype=np.int8)
            for sy in range(2, h + 2):
                for sx in range(2, w + 2):
                    if (sx + sy) % 2 == 0:
                        shadow[sy, sx] = BLACK
            self.put(f'post-shadow-{number}', shadow, x, y, 0, ('scenery',))
        if self.st.guard is not None:
            self.build_rail()
        self.blades = [blade_set(radius) for _, _, radius in self.lvl['cutters']]
        for number, (cx, cy, radius) in enumerate(self.lvl['cutters']):
            self.centered(f'blade-{number}', self.blades[number][0], (cx, cy), 3, ('blade', 'hazard'), key='a')
        for number in range(12):
            self.put(f'sparkle-{number}', spark_art(0), 0, 0, 11, ('effect',), key=0).set_visible(False)
        for number in range(16):
            self.put(f'confetti-{number}', confetti_art(number), 0, 0, 11, ('effect',), key=number).set_visible(False)
        for number in range(6):
            self.put(f'shard-{number}', np.full((2, 2), SHARD_COLOURS[number], dtype=np.int8), 0, 0, 11, ('effect',), key=number).set_visible(False)
        for number in range(2):
            self.put(f'tear-{number}', pic((('S.', 'SB', '.B'))), 0, 0, 11, ('effect',), key=0).set_visible(False)
        for number in range(3):
            self.put(f'smoke-{number}', smoke_art(0), 0, 0, 11, ('effect',), key=0).set_visible(False)
        for number in range(2):
            self.put(f'dust-{number}', DUST[0], 0, 0, 6, ('effect',), key=0).set_visible(False)
        for number in range(4):
            self.put(f'pop-{number}', spark_art(1), 0, 0, 11, ('effect',), key=0).set_visible(False)
        self.put('wipe', wipe_art((32, 32), 64), 0, 0, 12, ('effect',)).set_visible(False)
        self.sync()

    def build_rail(self):
        """The track the cover rolls along: two steel rails (lit sky blue, black underneath) either side of the line, with
        wooden sleepers across, each sleeper lit on top. Drawn once as one named sprite; the cover rolls over it."""
        art = np.full((64, 64), -1, dtype=np.int8)
        points = list(map(pixel, self.lvl['guard_rail']))
        for first, second in zip(points, points[1:]):
            horizontal = first[1] == second[1]
            count = max(1, round(hypot(second[0] - first[0], second[1] - first[1])))
            for step in range(count + 1):
                x, y = position_at(first, second, step / count)
                if step % 3 == 0:
                    for offset in range(-4, 5):
                        rect(art, x + (0 if horizontal else offset), y + (offset if horizontal else 0), 1, 1,
                             ORANGE if offset in (-4, 4) else MAROON)
                for offset, colour in ((-5, BLACK), (-4, SKY), (4, SKY), (5, BLACK)):
                    rect(art, x + (0 if horizontal else offset), y + (offset if horizontal else 0), 1, 1, colour)
        self.put('cover-rail', art, 0, 0, 2, ('rail',))

    # --- drawing the current instant --------------------------------------------------------------------------
    def animate_life(self):
        """Gentle life that does nothing: bulbs chase, shelf toys blink, stars twinkle, bubbles rise, fish drift."""
        tick, calm = self.tick, self.look == 'calm'
        lights = self.bulbs if calm else self.bulbs_alarm
        self.put('border-lights', lights[tick % len(lights)], 0, 0, -8, ('scenery', 'lights'), key=('l', calm, tick % len(lights)))
        for name, frames, entry in self.life:
            index = ((tick + entry['phase']) // entry['period']) % len(frames) if entry['period'] else 0
            x, y, move = entry['x'], entry['y'], entry['move']
            if move and move[0] == 'rise':
                y = entry['y'] - (tick + entry['phase'] * 3) % move[1]
            elif move and move[0] == 'slide':
                x = move[2] + (entry['x'] - move[2] + tick * move[1] * 2) % (move[3] - move[2])
            elif move and move[0] == 'drift':                       # straight up or down, wrapping round
                y = move[2] + (entry['y'] - move[2] + tick * move[1] * 2) % (move[3] - move[2])
            elif move and move[0] == 'glide':                       # a slanting slide (the comet): x wraps, y follows
                x = move[2] + (entry['x'] - move[2] + tick * move[1] * 2) % (move[3] - move[2])
                y = entry['y'] + (x - move[2]) * move[4]
            elif move and move[0] == 'bob':                         # bobs gently up and down in place
                y = entry['y'] + move[1] * sin(2 * pi * (tick + entry['phase']) / move[2])
            elif move and move[0] == 'loop':                        # wanders round a lazy ellipse
                angle = 2 * pi * (tick + entry['phase'] * 3) / move[3]
                x, y = entry['x'] + move[1] * cos(angle), entry['y'] + move[2] * sin(angle)
            self.put(name, frames[index], x, y, entry['layer'], ('scenery',), key=index)

    def sync(self):
        state, level = self.st, self.lvl
        animation, fx = self.animation, self.fx
        before = animation['before'] if animation else state
        step_no = min(3, animation['index']) if animation else 0
        fraction = FRACTIONS[step_no] if animation else 1.
        rover = position_at(before.rover, state.rover, fraction)
        guard = position_at(before.guard, state.guard, fraction) if state.guard is not None else None
        path = tighten(before.path + (rover,), level['obstacles']) if animation else state.path
        tick = self.tick
        look = 'alarm' if state.dead else 'calm'
        if look != self.look:
            self.look = look
            self.put('workshop-floor', self.alarm_floor if state.dead else self.calm_floor, OX, OY, -10, key=look)
            self.put('border-frame', self.alarm_frame if state.dead else self.calm_frame, 0, 0, -8, key=look)
            for number in range(4):
                if f'corner-{number}' in self.objects:
                    self.put(f'corner-{number}', self.alarm_corner if state.dead else self.calm_corner, 0, 0, -7, key=look)
        self.animate_life()
        lamp = 'G' if state.done else 'R' if state.dead else 'O' if tick % 2 else 'Y'
        self.centered('dock', pic(DOCK, {'E': lamp}), level['dock'], 4, ('dock', 'goal'), key=lamp, shift=(0, -3))
        # The cable is one named flexible object. Its transparent pixel mask comes from the same exact path the movement
        # rules use: a dark shadow one row below, then the orange wire with a bright current that runs along it.
        wire = np.full((64, 64), -1, dtype=np.int8)
        for first, second in zip(path, path[1:]):
            line(wire, (pixel(first)[0], pixel(first)[1] + 1), (pixel(second)[0], pixel(second)[1] + 1), BLACK)
        count = 0
        for first, second in zip(path, path[1:]):
            a, b = pixel(first), pixel(second)
            steps = max(1, round(hypot(b[0] - a[0], b[1] - a[1]) * 2))
            for fraction_along in np.linspace(0, 1, steps + 1):
                point = position_at(a, b, fraction_along)
                colour = YELLOW if (count + tick) % 9 == 0 else ORANGE
                if fx and fx['kind'] == 'bump' and state.feedback == 'taut':
                    if fx['i'] <= 1:
                        colour = RED if fx['i'] % 2 == 0 else WHITE      # the cable flashes when it is pulled tight...
                    length = max(1., hypot(b[0] - a[0], b[1] - a[1]))
                    # ...then rings like a plucked string: bowed sideways, the bow shrinking frame by frame
                    side = TWANG[min(5, fx['i'])] * sin(pi * fraction_along)
                    point = (point[0] - round(side * (b[1] - a[1]) / length), point[1] + round(side * (b[0] - a[0]) / length))
                rect(wire, point[0], point[1], 1, 1, colour)
                count += 1
        self.put('cable', wire, 0, 0, 5, ('cable',))
        dock_x, dock_y = pixel(level['dock'])
        remaining = max(0, level['cable'] - cable_length(path)) / level['cable']
        # the reel hangs above the dock canopy (nothing overlaps it any more); its plug touches the canopy roof
        self.put('cable-spool', spool_art(remaining), dock_x - 4, dock_y - 21, 6, ('cable-budget',), key=round(32 * remaining))
        if guard is not None:
            settled = state.latched and fraction >= 1
            self.centered('rolling-cover', hood_pic(settled, tick % 7 == 3), guard, 7, ('cover',), key=(settled, tick % 7 == 3))
        for number in range(len(level['cutters'])):
            frame = 'dead' if state.dead else 'ab'[(tick + number) % 2]
            art = self.blades[number][2] if state.dead else self.blades[number]['ab'.index(frame)]
            sprite = self.objects[f'blade-{number}']
            if self.keys[f'blade-{number}'] != frame:
                sprite.pixels, self.keys[f'blade-{number}'] = art, frame
        pickup = animation is not None and state.feedback == 'pickup'
        core_position = position_at(level['core'], rover, fraction) if pickup else level['core']
        core_frame = 2 if tick % 11 == 4 else (tick // 2) % 2          # now and then the core blinks
        core_sprite = self.centered('core', CORE_PICS[core_frame], core_position, 8, ('core', 'sys_click'), key=core_frame)
        core_sprite.set_visible(not state.carrying or pickup)
        shake = (0, HOP[step_no]) if animation else (0, 0)
        squash = bool(animation) and SQUASH[step_no]
        expression = 'blink' if tick % 13 == 5 else 'ok'
        if state.feedback in ('taut', 'bumper', 'guard-stop', 'undo-empty') and not state.dead and not animation:
            expression = 'wince'                       # a refused move: the robot squeezes its eyes shut for a moment
        if fx and fx['kind'] == 'lose':
            shake = (fx['i'] % 2 * 2 - 1, min(2, fx['i'] // 2))      # shudder, then droop
        elif fx and fx['kind'] == 'win':
            shake = (0, (0, -3, -4, -2, 0, 0, 0, 0)[min(7, fx['i'])])      # a happy hop
        elif fx and fx['kind'] == 'bump':
            nudge = BUMP[min(3, fx['i'])]                                # a refused move: a shove back and a wobble
            shake = (nudge * fx['dir'][0], nudge * fx['dir'][1])
        if state.dead:
            expression = 'dead'
        elif fx and fx['kind'] == 'win':
            expression = 'win'
        art = rover_art(state.facing, bool(state.carrying and not pickup), expression,
                        tick % 2 if (state.rover != before.rover or animation) else 0, scene_body(self.scene),
                        'R' if tick % 6 < 3 else 'O', squash)
        self.centered('rover', art, rover, 9, ('player',), shift=(shake[0], shake[1] + squash))
        radius = (4, 3, 2, 2)[min(3, fx['i'])] if fx and fx['kind'] == 'bump' else 2 + state.pulse     # brackets close in on a refusal
        quiet = state.feedback in QUIET_FEEDBACK
        cue = self.centered('contact-feedback', cue_art(state.dead, radius, YELLOW if state.feedback == 'undo' else RED, tick % 2),
                            state.focus, 10, ('feedback',), key=(state.dead, radius, state.feedback == 'undo', tick % 2, quiet))
        if quiet and not state.dead:
            cue.set_visible(False)
        else:
            cue.set_visible(True)
        self.play_motion(before, rover, guard, step_no)
        self.play_effects(rover)
        self.shake_screen()

    def shake_screen(self):
        """When the run is lost every drawn piece (not the effects) is knocked a pixel or two together, then settles."""
        fx = self.fx
        knock = SHAKE[min(6, fx['i'])] if fx and fx['kind'] == 'lose' else (0, 0)
        if knock == (0, 0) and not self.shaken:
            return
        self.shaken = knock != (0, 0)
        for name, sprite in self.objects.items():
            if 'effect' not in sprite.tags:
                home = self.home[name]
                sprite.set_position(home[0] + knock[0], home[1] + knock[1])

    def play_motion(self, before, rover, guard, step_no):
        """Dust at the feet of a moving rover (at the cover when it is shoved), a star pop on pickup and latch, and the level iris."""
        state, animation = self.st, self.animation
        moved = bool(animation) and state.rover != before.rover
        for number in range(2):
            sprite = self.objects[f'dust-{number}']
            if moved and step_no >= 1:
                if number == 0:
                    point = before.rover
                elif state.feedback == 'push' and before.guard is not None:
                    point = before.guard
                else:
                    point = position_at(before.rover, rover, .5)
                x, y = pixel(point)
                puff = DUST[min(2, step_no - 1 + number)]
                sprite.pixels = puff
                sprite.set_position(max(0, min(64 - puff.shape[1], round(x) - puff.shape[1] // 2)),
                                    max(0, min(64 - puff.shape[0], round(y) + 5 - puff.shape[0])))
                sprite.set_visible(True)
            else:
                sprite.set_visible(False)
        popping = bool(animation) and state.feedback in ('pickup', 'latch') and step_no >= 1
        centre = pixel(guard if state.feedback == 'latch' and guard is not None else rover)
        for number in range(4):
            sprite = self.objects[f'pop-{number}']
            angle, reach = pi / 4 + number * pi / 2, 4 + 3 * step_no
            x, y = centre[0] + reach * cos(angle) - 2, centre[1] + reach * sin(angle) - 2
            sprite.set_position(max(0, min(59, round(x))), max(0, min(59, round(y))))
            sprite.set_visible(popping and 0 <= x <= 59 and 0 <= y <= 59)
        radius, hole = None, pixel(rover)
        if self.fx and self.fx['kind'] == 'win' and not self.is_last_level():
            radius = WIPE_RADIUS.get(self.fx['i'])
        elif self.intro:
            radius, hole = OPEN_RADIUS.get(self.intro), pixel(self.lvl['dock'])
        wipe = self.objects['wipe']
        if radius is None:
            wipe.set_visible(False)
        else:
            wipe.pixels = wipe_art(hole, radius)
            wipe.set_visible(True)

    def play_effects(self, rover):
        """Win sparkle and loss smoke: two small families of named sprites, hidden until an effect runs."""
        fx, centre = self.fx, pixel(rover)
        for number in range(12):
            sprite = self.objects[f'sparkle-{number}']
            if fx and fx['kind'] == 'win':
                # two rings of stars flying outward, the outer ring turning the other way
                inner = number < 6
                angle = number * (pi / 3 if inner else pi / 3 + .5) + fx['i'] * (.4 if inner else -.3)
                reach = (4 + 3 * fx['i']) if inner else (9 + 4 * fx['i'])
                x, y = centre[0] + reach * cos(angle) - 2, centre[1] + reach * sin(angle) * .85 - 2
                sprite.pixels = spark_art(number + fx['i'])
                sprite.set_position(max(0, min(59, round(x))), max(0, min(59, round(y))))
                sprite.set_visible(2 <= x <= 57 and 2 <= y <= 57)
            else:
                sprite.set_visible(False)
        for number in range(16):
            sprite = self.objects[f'confetti-{number}']
            if fx and fx['kind'] == 'win':
                # a shower of paper falls from the top of the screen, each scrap swaying on its own beat
                x = 4 + (number * 43) % 52 + round(2 * sin(fx['i'] + number))
                y = -6 + fx['i'] * 9 + (number * 7) % 13
                sprite.set_position(x, max(0, y))
                sprite.set_visible(0 <= y <= 60)
            else:
                sprite.set_visible(False)
        shown = bool(fx and fx['kind'] == 'lose')
        focus = pixel(self.st.focus) if shown else centre
        for number in range(6):
            sprite = self.objects[f'shard-{number}']
            if shown:
                # bits of blade fly out from where the saw struck
                angle, reach = number * pi / 3 + .4, 2 + 3 * fx['i']
                x, y = focus[0] + reach * cos(angle), focus[1] + reach * sin(angle)
                sprite.set_position(max(0, min(61, round(x))), max(0, min(61, round(y))))
                sprite.set_visible(2 <= x <= 60 and 2 <= y <= 60 and fx['i'] < 5)
            else:
                sprite.set_visible(False)
        for number in range(2):
            sprite = self.objects[f'tear-{number}']
            if fx and fx['kind'] == 'lose':
                sprite.set_position(max(0, min(61, round(centre[0] - 3 + number * 5))), max(0, min(60, round(centre[1] - 1 + fx['i'] * 2 + number))))
                sprite.set_visible(True)
            else:
                sprite.set_visible(False)
        for number in range(3):
            sprite = self.objects[f'smoke-{number}']
            if fx and fx['kind'] == 'lose':
                lift = 3 + fx['i'] * 2 + number * 3
                sprite.pixels = smoke_art(number + fx['i'])
                sprite.set_position(max(0, min(60, round(centre[0] - 2 + (number - 1) * 3))), max(0, round(centre[1] - 3 - lift)))
                sprite.set_visible(True)
            else:
                sprite.set_visible(False)

    # --- turning one input into frames ------------------------------------------------------------------------
    def finish_action(self):
        self.animation = None
        self.sync()
        if self.st.dead:
            self.fx = {'kind': 'lose', 'i': 0, 'n': 6}
            self.sync()
        elif self.st.done:
            self.fx = {'kind': 'win', 'i': 0, 'n': 6}
            self.sync()
        elif self.st.feedback not in QUIET_FEEDBACK:
            # a refused or missed input: a short drawn reaction (shove, head-shake or just closing brackets) before control returns
            side = (1, 0) if self.st.feedback in SIDEWAYS_REFUSALS else (0, 0)
            direction = self.st.facing if self.st.feedback in ('taut', 'bumper', 'guard-stop') else side
            self.fx = {'kind': 'bump', 'i': 0, 'n': 5 if self.st.feedback == 'taut' else 3, 'dir': direction}
            self.sync()
        else:
            self.complete_action()

    def step(self):
        self.tick += 1
        if self.action.id.value == 0:
            self.sync()
            self.complete_action()
            return
        if self.intro:
            self.intro -= 1
            self.sync()
            if not self.intro:
                self.complete_action()
            return
        if self.fx is not None:
            self.fx['i'] += 1
            self.sync()
            if self.fx['i'] >= self.fx['n']:
                kind, self.fx = self.fx['kind'], None
                if kind == 'lose':
                    self.lose()
                elif kind == 'win':
                    if self.is_last_level():
                        self.next_level()
                    else:
                        self.pending_intro = 2          # the next stage opens with an iris before play returns
                        self.next_level()
                        return
                self.complete_action()
            return
        if self.animation is not None:
            self.animation['index'] += 1
            if self.animation['index'] >= 4:
                self.finish_action()
            else:
                self.sync()
            return
        before, action = self.st, self.action.id.value
        if action == 7:
            if self.history:
                self.st = self.history.pop()._replace(feedback='undo', pulse=1 - before.pulse)
                self.st = self.st._replace(focus=self.st.rover)
            else:
                self.st = before._replace(feedback='undo-empty', focus=before.rover, pulse=1 - before.pulse)
        else:
            point = None
            if action == 6:
                data = self.action.data or {}
                x, y = data.get('x'), data.get('y')
                if all(isinstance(value, (int, float)) and isfinite(value) for value in (x, y)) and 0 <= x < 64 and 0 <= y < 64:
                    point = ((x - OX) / CELL, (y - OY) / CELL)
            self.history.append(before)
            self.st = transition(self.lvl, before, action, point)
        if self.st.rover != before.rover or self.st.feedback == 'pickup':
            self.animation = {'before': before, 'index': 1}
            self.sync()
            return
        self.finish_action()
