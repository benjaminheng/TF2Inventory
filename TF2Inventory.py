#!/usr/bin/python

import steamodd as steam
import os, sys
import codecs
import ConfigParser
import time

class Item():
    def __init__(self, i, account):
        self.name = i.get_name()
        self.quality = i.get_quality()['prettystr']
        self.material = self.get_material(i)
        self.count = {account: 1}
        self.image = i.get_image(i.ITEM_IMAGE_SMALL)
        countname = '%s %s' % (self.quality, self.name)

        self.add_to_list(i, account)

    def add(self, list_, account):
        for index, item in enumerate(list_):
            if item.name == self.name and item.quality == self.quality:
                if account in item.count.keys():
                    self.count[account] = item.count[account] + 1
                self.count = dict(item.count.items() + self.count.items())
                list_[index] = self
                break
        else:
            list_.append(self)

    def add_to_list(self, i, account):
        classes = i.get_equipable_classes()

        if len(classes) == 9:
            self.add(allClass, account)
        elif len(classes) == 0:
            #filter to tools and crates
            if i.get_craft_material_type() == 'supply_crate':
                self.add(crates, account)
            else:
                self.add(tools, account)
        else:
            if "Scout" in classes:
                self.add(scout, account)
            if "Soldier" in classes:
                self.add(soldier, account)
            if "Pyro" in classes:
                self.add(pyro, account)
            if "Demoman" in classes:
                self.add(demo, account)
            if "Heavy" in classes:
                self.add(heavy, account)
            if "Engineer" in classes:
                self.add(engi, account)
            if "Medic" in classes:
                self.add(medic, account)
            if "Sniper" in classes:
                self.add(sniper, account)
            if "Spy" in classes:
                self.add(spy, account)

    def get_material(self, i):
        material = i.get_craft_material_type()
                    
        if material != None:
            if material == 'supply_crate':
                # Stick crate series on end of crate item name
                if i.get_name() == 'Mann Co. Supply Crate':
                    crateseries = str(int(i.get_attributes()[0].get_value()))
                    self.name = i.get_name() + ' #' + crateseries
                material = 'crate'
            elif material == 'hat':
                if i.get_slot() == 'misc':
                    material = 'misc'
            elif material == 'craft_bar':
                material = 'metal'
        else:
            slot = i.get_slot()
            class_ = i.get_class()
            if slot == 'head':
                material = 'hat'
            elif slot == 'misc':
                material = 'misc'
            elif slot == 'primary' or slot == 'secondary' or slot == 'melee' or slot == 'pda2':
                material = 'weapon'
            elif class_ == 'supply_crate':
                # Stick crate series on end of crate item name
                if i.get_name() == 'Mann Co. Supply Crate':
                    crateseries = str(int(i.get_attributes()[0].get_value()))
                    self.name = i.get_name() + ' #' + crateseries
                material = 'crate'
            elif class_ == 'tool' or slot == 'action' or class_ == 'craft_item':
                material = 'tool'
            else:
                # Catch all
                material = 'tool'
        return material

    def get_nice_count(self):
        tmp = 'Total: %s'
        total = 0
        for i in self.count:
            total = total + self.count[i]
            tmp = tmp + '<br/>%s: %s' % (i, self.count[i])
        tmp = tmp % total
        return tmp


class Options:
    def __init__(self):
        self.conf = ConfigParser.ConfigParser()
        self.accounts = []
        self.apiKey = ''
        self.pollMinutes = 10
        self.htmldir = ''
        self.filename = ''
        self.get_config_options()

    def get_config_options(self):
        try:
            self.conf.read(os.path.join(os.path.dirname(sys.argv[0]), 'config.ini'))
            self.accounts = self.conf.get('General', 'accounts').split(',')
            self.apiKey = self.conf.get('General', 'api_key')
            self.pollMinutes = int(self.conf.get('General', 'poll_minutes'))
            self.htmldir = self.conf.get('General', 'html_dir')
            self.filename = self.conf.get('General', 'file_name')
        except Exception as e:
            print 'Options Error:', e
            return

def get_qualities(list_):
    qualities = ['unusual', 'strange', 'vintage', 'genuine', 'haunted'] 
    unusual = [i for i in list_ if i.quality.lower() == qualities[0]]
    strange = [i for i in list_ if i.quality.lower() == qualities[1]]
    vintage = [i for i in list_ if i.quality.lower() == qualities[2]]
    genuine = [i for i in list_ if i.quality.lower() == qualities[3]]
    haunted = [i for i in list_ if i.quality.lower() == qualities[4]]
    # uniques
    others = [i for i in list_ if i.quality.lower() not in qualities]
    return unusual, strange, vintage, genuine, haunted, others

def generate_rows(list_, content, rowMarker):
    rowHtml = '<tr class="%s-quality"><td><img src="%s"/></td><td>%s</td><td>%s</td><td class="count-col">%s</td></tr>\n%s'
    qualities = get_qualities(list_)
    for quality in qualities:
        for i in quality:
            if i.quality != 'Unique':
                displayName = '%s %s' % (i.quality, i.name)
            else:
                displayName = i.name
            row = rowHtml % (i.quality.lower(), i.image, i.material.capitalize(), displayName, i.get_nice_count(), rowMarker)
            content = content.replace(rowMarker, row)
    return content

def sort_and_generate_rows(title, list_, content):
    sectionHeaderHtml = '<tr><td class="table-section-header" colspan="4">%s</td></tr>\n%s'
    rowMarker = '<!--APPENDROWHERE-->'

    header = sectionHeaderHtml % (title, rowMarker)
    content = content.replace(rowMarker, header)

    # sorting according to material
    types = ['hat', 'misc', 'weapon', 'crate', 'metal', 'tool']
    hat = [i for i in list_ if i.material.lower() == types[0]]
    misc = [i for i in list_ if i.material.lower() == types[1]]
    weapon = [i for i in list_ if i.material.lower() == types[2]]
    crate = [i for i in list_ if i.material.lower() == types[3]]
    metal = [i for i in list_ if i.material.lower() == types[4]]
    tool = [i for i in list_ if i.material.lower() == types[5]]
    others = [i for i in list_ if i.material.lower() not in types]
    # generating according to quality
    content = generate_rows(metal, content, rowMarker)
    content = generate_rows(crate, content, rowMarker)
    content = generate_rows(tool, content, rowMarker)
    content = generate_rows(hat, content, rowMarker)
    content = generate_rows(misc, content, rowMarker)
    content = generate_rows(weapon, content, rowMarker)
    content = generate_rows(others, content, rowMarker)
    return content

if __name__ == '__main__':
    options = Options()
    steam.base.set_api_key(options.apiKey);

    template = os.path.join(os.path.dirname(sys.argv[0]), 'template.html')
    fullpath = os.path.join(options.htmldir, options.filename)

    


    while True:
        tools = []
        crates = []
        scout = []
        soldier = []
        pyro = []
        demo = []
        heavy = []
        engi = []
        medic = []
        sniper = []
        spy = []
        allClass = []
        with codecs.open(fullpath, 'w', 'utf-8') as f:
            content = ''
            with open(template) as main:
                content = main.read()

            for steamId in options.accounts:
                try:
                    backpack = steam.tf2.backpack(steamId)
                    for i in backpack:
                        Item(i, steamId)
                except:
                    pass

            
            ############################
            # Begin table population

            # crates
            content = sort_and_generate_rows('Crates', crates, content)
            # tools
            content = sort_and_generate_rows('Tools', tools, content)

            # all classes
            content = sort_and_generate_rows('All Classes', allClass, content)
            
            # scout
            content = sort_and_generate_rows('Scout', scout, content)

            # Soldier
            content = sort_and_generate_rows('Soldier', soldier, content)

            # Pyro
            content = sort_and_generate_rows('Pyro', pyro, content)

            # Demo
            content = sort_and_generate_rows('Demoman', demo, content)

            # Heavy
            content = sort_and_generate_rows('Heavy', heavy, content)
            
            # Engi
            content = sort_and_generate_rows('Engineer', engi, content)

            # Medic
            content = sort_and_generate_rows('Medic', medic, content)

            # Sniper
            content = sort_and_generate_rows('Sniper', sniper, content)

            # Spy
            content = sort_and_generate_rows('Spy', spy, content)

            # End table population
            ###########################
            
            f.write(content)
        print 'Generated.'
        time.sleep(60*options.pollMinutes)

