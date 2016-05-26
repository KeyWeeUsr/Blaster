# -*- coding: utf-8 -*-
# Blaster
# Version: 0.1.0
# Copyright (C) 2016, KeyWeeUsr(Peter Badida) <keyweeusr@gmail.com>
# License: GNU GPL v3.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# More info in LICENSE.txt
#
# The above copyright notice, warning and additional info together with
# LICENSE.txt file shall be included in all copies or substantial portions
# of the Software.

# levels will be in json format(blocks)

import json
import random
import os.path as op
from kivy import require
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
require('1.9.2')
'''
App.map without breakable: (left -> right)
[[0,0,0,0,0],     bottom(y=0)
 [0,2,0,2,0],       |
 [0,0,0,0,0],       |
 [0,2,0,2,0],       v
 [0,0,0,0,0]      top(y=top)
]
'''


class Game(ScreenManager):
    '''Root widget of the game.'''
    def __init__(self, **kw):
        super(Game, self).__init__(**kw)
        self.transition = SlideTransition(direction='up')
        self.current = 'menu'


class Bomber(Widget):
    '''Player with stats. Always spawns at [0, 0].'''
    place = [0, 0]

    def __init__(self, **kw):
        super(Bomber, self).__init__(**kw)
        self.app = App.get_running_app()
        self.app.player = self
        self.extra_pos = []
        self.keyboard = Window.request_keyboard(self.keyboard_close, self)
        self.keyboard.bind(on_key_down=self.on_keyboard_down)
        self.keyboard.bind(on_key_up=self.on_key_up)

    def reset(self):
        '''Reset stats here - e.g. death, level reset, etc.'''
        pass

    def collide_npc(self):
        '''Collision with npc i.e. death handling.'''
        for t in self.app.touchable:
            if t.place == self.place:
                pass

    def collide_extra(self):
        '''Collision with extra item.'''
        if self.pos in self.extra_pos:
            pass

    def update_pos(self, direction):
        '''Walking function.'''
        if direction == 'up':
            if self.pos[1] < self.arch['size'][1] and self.get_block('up'):
                self.place[1] += 1
                self.pos = self.pos[0], self.pos[1] + 50
        elif direction == 'down':
            if self.pos[1] > 50 and self.get_block('down'):
                self.place[1] -= 1
                self.pos = self.pos[0], self.pos[1] - 50
        elif direction == 'left':
            if self.pos[0] > 50 and self.get_block('left'):
                self.place[0] -= 1
                self.pos = self.pos[0] - 50, self.pos[1]
        elif direction == 'right':
            if self.pos[0] < self.arch['size'][0] and self.get_block('right'):
                self.place[0] += 1
                self.pos = self.pos[0] + 50, self.pos[1]
        self.collide_npc()
        self.collide_extra()

    def get_block(self, direction):
        '''
        Get block from 2D array to check if there is something
        in front of the player.
        '''
        if direction == 'up':
            if not self.app.map[self.place[1]+1][self.place[0]]:
                return True
        elif direction == 'down':
            if not self.app.map[self.place[1]-1][self.place[0]]:
                return True
        elif direction == 'left':
            if not self.app.map[self.place[1]][self.place[0]-1]:
                return True
        elif direction == 'right':
            if not self.app.map[self.place[1]][self.place[0]+1]:
                return True

    def keyboard_close(self):
        self.keyboard.unbind(on_key_down=on_keyboard_down)
        self.keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        '''Do something when a key is pressed.'''
        # continuous smooth movement later
        if keycode[1] == 'up' or keycode[1] == 'w':
            self.update_pos('up')
        elif keycode[1] == 'down' or keycode[1] == 's':
            self.update_pos('down')
        elif keycode[1] == 'left' or keycode[1] == 'a':
            self.update_pos('left')
        elif keycode[1] == 'right' or keycode[1] == 'd':
            self.update_pos('right')
        elif keycode[1] == 'spacebar':
            self.parent.add_widget(Bomb(pos=self.pos))
            # place a condition - if there is special extra,
            # you will go through bombs
            self.app.map[self.place[1]][self.place[0]] = 1
        elif keycode[1] == 'enter':
            pass
        elif keycode[1] == 'escape':
            exit()
        elif keycode[1] == 'p':
            pass  # self.pause_game() that pauses Clocks
        return True

    def on_key_up(self, keyboard, keycode):
        '''Do something when a key is released.'''
        if keycode[1] == 'up' or keycode[1] == 'w':
            pass
        elif keycode[1] == 'down' or keycode[1] == 's':
            pass
        elif keycode[1] == 'left' or keycode[1] == 'a':
            pass
        elif keycode[1] == 'right' or keycode[1] == 'd':
            pass


class Monster(object):
    '''Monster instance. Will take form&stats from json(probably).'''
    pass


class Bonus(object):
    '''
    An item which will spawn in a wall and will be highlighted
    at the end of a level.(Extra item)
    '''
    pass


class Gate(object):
    '''An exit from level'''
    pass


class Wall(Image):
    '''Basic block for a game - borders, columns, breakable, background.'''
    def __init__(self, **kw):
        super(Wall, self).__init__(**kw)
        self.text = kw.get('text', '')
        self.place = kw.get('place', '')


class Column(Wall):
    '''
    Concrete, non-destroyable block.
    Block fire widgets only, or the fire too?
    '''
    def __init__(self, **kw):
        super(Column, self).__init__(**kw)
        self.source = 'column.png'


class Fire(Wall):  # pun, hehe
    '''
    Fire, spawns after a bomb explodes, changes image over time and collides
    with player (and maybe other bombs).
    '''
    def __init__(self, **kw):
        super(Fire, self).__init__(**kw)
        self.stage = 0
        self.dir = kw.get('dir', '')
        self.place = kw.get('place', '')
        self.burn()
        Clock.schedule_interval(self.burn, .1)

    def burn(self, dt=0):
        if self.stage == 6:
            Clock.unschedule(self.burn)
            self.parent.remove_widget(self)
        if self.dir == '':
            self.source = 'fire/' + str(self.stage) + 'c.png'
        elif self.dir == 'up':
            self.source = 'fire/' + str(self.stage) + 'eu.png'
        elif self.dir == 'down':
            self.source = 'fire/' + str(self.stage) + 'ed.png'
        elif self.dir == 'left':
            self.source = 'fire/' + str(self.stage) + 'el.png'
        elif self.dir == 'right':
            self.source = 'fire/' + str(self.stage) + 'er.png'
        elif self.dir == 'ud':
            self.source = 'fire/' + str(self.stage) + 'ud.png'
        elif self.dir == 'lr':
            self.source = 'fire/' + str(self.stage) + 'lr.png'
        self.stage += 1


class Bomb(Wall):
    '''
    A bomb which will spawn when player <space>. Clock, then boom.
    '''
    def __init__(self, **kw):
        super(Bomb, self).__init__(**kw)
        self.app = App.get_running_app()
        self.source = 'bomb1.png'
        self.time = 300
        self.place = self.app.player.place
        self.range = kw.get('range', 3)
        self.tick = Clock.schedule_interval(self.countdown, 1)
        self.gif = Clock.schedule_interval(self.sparkle, 0.25)

    def sparkle(self, dt):
        '''Changing pictures of a bomb to make the knot burning.'''
        if self.source != 'bomb2.png' and not self.time % 12.5:
            self.source = 'bomb2.png'
        else:
            if self.source != 'bomb1.png':
                self.source = 'bomb1.png'

    def countdown(self, dt):
        '''Countdown until the bomb detonates and spawns Fire widgets'''
        self.time -= 100
        if not self.time > 0:
            Clock.unschedule(self.tick)
            x, y = [p/50 - 1 for p in self.pos]
            self.app.map[y][x] = 0
            self.fire()
            self.destroy()
            self.parent.remove_widget(self)

    def clear(self, breakable, r, purge=False):
        if r == 'purge':
            for r in xrange(len(self.app.breakable)):
                try:
                    if (breakable[r].place[0] == 'x' and
                            breakable[r].place[1] == 'x'):
                        breakable.remove(breakable[r])
                except IndexError:
                    pass
            self.app.breakable = breakable[:]
            return
        breakable[r].place[0] = 'x'
        breakable[r].place[1] = 'x'

    def fire(self):
        self.parent.add_widget(Fire(pos=self.pos, place=self.place))

    def destroy(self):
        i = self.app.breakable[:]
        g_pos = [g_pos/50-1 for g_pos in self.pos]  # [0,0] left down
        where = ['up', 'down', 'right', 'left']  # fire directions(max 1 shot)
        # replace with single characters
        cnt = 1
        while where:
            if cnt <= self.range or not where:
                for r in xrange(len(self.app.breakable)):
                    # check if flame hits column first(blocks fire range)
                    # up and right need to be at the bottom, or IndexError
                    try:
                        if self.app.map[g_pos[1]][g_pos[0] - cnt] == 2:
                            if 'left' in where:
                                where.remove('left')
                        if self.app.map[g_pos[1] - cnt][g_pos[0]] == 2:
                            if 'down' in where:
                                where.remove('down')
                        if self.app.map[g_pos[1] + cnt][g_pos[0]] == 2:
                            if 'up' in where:
                                where.remove('up')
                        if self.app.map[g_pos[1]][g_pos[0] + cnt] == 2:
                            if 'right' in where:
                                where.remove('right')
                    except IndexError:
                        pass  # end of map

                    # check if flame hits breakable wall
                    if ((g_pos[0] + cnt == i[r].place[0]) and
                            (g_pos[1] == i[r].place[1]) and
                            ('right' in where)):
                        where.remove('right')
                        self.app.map[g_pos[1]][g_pos[0]+cnt] = 0
                        fire_right = Fire(pos=[self.pos[0] + 50 * cnt,
                                               self.pos[1]],
                                          dir='right',
                                          place=[self.place[0] + cnt,
                                                 self.place[1]])
                        self.parent.add_widget(fire_right)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)
                    if ((g_pos[0] - cnt == i[r].place[0]) and
                            (g_pos[1] == i[r].place[1]) and
                            ('left' in where)):
                        where.remove('left')
                        self.app.map[g_pos[1]][g_pos[0]-cnt] = 0
                        fire_left = Fire(pos=[self.pos[0] - 50 * cnt,
                                              self.pos[1]],
                                         dir='left',
                                         place=[self.place[0] - cnt,
                                                self.place[1]])
                        self.parent.add_widget(fire_left)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)
                    if ((g_pos[0] == i[r].place[0]) and
                            (g_pos[1] + cnt == i[r].place[1]) and
                            ('up' in where)):
                        where.remove('up')
                        self.app.map[g_pos[1] + cnt][g_pos[0]] = 0
                        fire_up = Fire(pos=[self.pos[0],
                                            self.pos[1] + 50 * cnt],
                                       dir='up',
                                       place=[self.place[0],
                                              self.place[1] + cnt])
                        self.parent.add_widget(fire_up)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)
                    if ((g_pos[0] == i[r].place[0]) and
                            (g_pos[1] - cnt == i[r].place[1]) and
                            ('down' in where)):
                        where.remove('down')
                        self.app.map[g_pos[1] - cnt][g_pos[0]] = 0
                        fire_down = Fire(pos=[self.pos[0],
                                              self.pos[1] - 50 * cnt],
                                         dir='down',
                                         place=[self.place[0],
                                                self.place[1] - cnt])
                        self.parent.add_widget(fire_down)
                        self.parent.remove_widget(i[r])
                        self.clear(i, r)

                # check for borders and increase
                if (self.pos[1]+50*(cnt) < self.app.player.arch['size'][1]+50 and
                        'up' in where):
                    fire_ud_up = Fire(pos=[self.pos[0],
                                           self.pos[1]+50*(cnt)],
                                      dir='ud' if cnt != self.range else 'up',
                                      place=[self.place[0],
                                             self.place[1]+1*(cnt)])
                    self.parent.add_widget(fire_ud_up)
                if self.pos[1]-50*(cnt) > 0 and 'down' in where:
                    fire_ud_down = Fire(pos=[self.pos[0],
                                             self.pos[1]-50*(cnt)],
                                        dir='ud' if cnt != self.range else 'down',
                                        place=[self.place[0],
                                               self.place[1]-1*(cnt)])
                    self.parent.add_widget(fire_ud_down)

                if (self.pos[0]+50*cnt < self.app.player.arch['size'][0]+50 and
                        'right' in where):
                    fire_lr_right = Fire(pos=[self.pos[0]+50*(cnt),
                                              self.pos[1]],
                                         dir='lr' if cnt != self.range else 'right',
                                         place=[self.place[0]+1*(cnt),
                                                self.place[1]])
                    self.parent.add_widget(fire_lr_right)
                if self.pos[0]-50*(cnt) > 0 and 'left' in where:
                    fire_lr_left = Fire(pos=[self.pos[0]-50*(cnt),
                                             self.pos[1]],
                                        dir='lr' if cnt != self.range else 'left',
                                        place=[self.place[0]-1*(cnt),
                                               self.place[1]])
                    self.parent.add_widget(fire_lr_left)
                cnt += 1
            else:
                self.clear(i, 'purge')
                del i
                break


class Level(Screen):
    '''Level screen'''
    def __init__(self, **kw):
        super(Level, self).__init__(**kw)
        self.app = App.get_running_app()
        self.path = self.app.path
        self.app.level = self
        self.app.breakable = []  # Walls
        self.app.touchable = []  # NPC
        self.texture = Image(source='grass.png').texture
        self.texture.wrap = 'repeat'

    def load_level(self, start=False):
        '''Json loading'''
        if not op.exists(self.path+'/stats.json'):
            stats = {'level': 1}
            level = 1
            with open(self.path+'/stats.json', 'w') as f:
                f.write(json.dumps(stats))
        else:
            with open(self.path+'/stats.json') as f:
                level = json.load(f)['level']
        with open(self.path+'/levels/'+str(level)+'.json') as f:
            self.set_level(json.load(f))
            self.manager.current = 'level'

    def create_borders(self, arch):
        # border size
        border_top = (arch['size'][0] + 100) / 50
        border_left = (arch['size'][1]) / 50
        border_right = border_left
        border_bottom = border_top
        width = arch['size'][0]
        height = arch['size'][1]

        # border spawn
        for top in xrange(border_top):
            self.ids.lvlwindow.add_widget(Column(pos=[50*top, height+50]))
        for left in xrange(border_left):
            self.ids.lvlwindow.add_widget(Column(pos=[0, 50+50*left]))
        for right in xrange(border_right):
            self.ids.lvlwindow.add_widget(Column(pos=[width+50, 50+50*right]))
        for bot in xrange(border_bottom):
            self.ids.lvlwindow.add_widget(Column(pos=[50*bot, 0]))
        self.create_columns(arch, border_left, border_top)

    def create_columns(self, arch, border_left, border_top):
        block_left = border_left - int(str(arch['size'][1])[:-2]) - 1
        block_top = border_top - int(str(arch['size'][0])[:-2]) - 3
        for h in xrange(block_left):
            for w in xrange(block_top):
                col = Column(pos=[100+w*100, 100+h*100])
                self.ids.lvlwindow.add_widget(col)

    def set_level(self, arch):
        '''
        Setting the level architecture from json:
            width x height
            id of extra + count
            id of npc + count
            boss maybe?
        '''
        self.app.player.arch = arch
        # increase the size of level by borders + move it
        self.ids.lvlwindow.size_hint = None, None
        self.ids.lvlwindow.size = [i + 100 for i in arch['size']]
        self.ids.lvlwindow.pos = [p + 50 for p in self.ids.lvlwindow.pos]
        self.create_borders(arch)

        # spawn npc somewhere
        # minimum_pos [50, 50]
        # maximum_pos [ arch['size'][0], arch['size'][1] ]
        npc_top = arch['size'][0] / 50
        npc_left = arch['size'][1] / 50
        # generate zero map
        self.app.map = [[0 for x in xrange(npc_top)] for y in range(npc_left)]
        for h in xrange(npc_left):
            for w in xrange(npc_top):
                # leave out wall
                if self.roll() and ((h+1) % 2 or (w+1) % 2):
                    wall = Wall(text='[%s, %s]' % (w, h),
                                pos=[50+50*w, 50+50*h],
                                place=[w, h])
                    self.app.map[h][w] = 1
                    self.app.breakable.append(wall)
                    self.ids.lvlwindow.add_widget(wall)
                elif not (h+1) % 2 and not (w+1) % 2:
                    # unbreakable blocks(columns)
                    self.app.map[h][w] = 2
        self.spawn('npc', arch['c_npc'])
        self.spawn('extra', arch['c_extra'])

    def roll(self, percent=20):
        '''Simple random counter'''
        return random.randrange(100) < percent

    def spawn(self, what, count):
        breakable = self.app.breakable[:]
        if what == 'gate':
            pass
        elif what == 'extra':
            for i in xrange(count):
                random.shuffle(self.app.breakable)
                x, y = self.app.breakable.pop().place
                extra_pos = [50 + 50 * x, 50 + 50 * y]
                extra = Wall(pos=extra_pos, color=[0, 1, 0, 1], place=[x, y])
                wall = Wall(pos=extra_pos, place=[x, y])
                self.app.map[y][x] = 1
                self.app.breakable.append(wall)
                self.app.player.extra_pos.append(extra_pos)
                self.ids.lvlwindow.add_widget(extra)
                self.ids.lvlwindow.add_widget(wall)
            del breakable
        elif what == 'npc':
            # append to touchable
            pass
        elif what == 'boss':
            pass


class Menu(Screen):
    def __init__(self, **kw):
        self.app = App.get_running_app()
        self.level = self.app.level
        super(Menu, self).__init__(**kw)

    def start_game(self):
        self.level.load_level(True)

    def load_game(self):
        self.level.load_level()


class Blaster(App):
    path = op.dirname(op.abspath(__file__))

    def build(self):
        return Game()

if __name__ == '__main__':
    Blaster().run()
