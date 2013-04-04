#!/usr/bin/python

import sqlite3
import steamodd as steam
import ConfigParser
import codecs
import os, sys
import time
from mako.template import Template

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

class Backpack():
    def __init__(self, bp, account):
        self.bp = bp
        self.account = account
        self.counts = {}
        self.db = DB('items.db')
        accitems = self.db.get_account_items_steamids(account)

        bpitems = []
        try:
            for i in bp:
                item = Item(i, self.account)
                if item.id not in accitems:
                    if not self.db.item_exists(item):
                        self.db.insert_to_item_and_account(item, account)
                    else:
                        self.db.insert_to_account(item, account)
                bpitems.append(item.id)
            for itemid in accitems:
                if itemid not in bpitems:
                    self.db.remove_from_account_by_steamitemid(itemid)
                    # remove from item if no accounts associated
                    if not self.db.get_accounts_by_itemid(itemid):
                        self.db.remove_from_item_by_id(itemid)

            self.db.close()
        except Exception as e:
            print 'backpack error: ', e


class Item():
    def __init__(self, i, account):
        self.name = i.get_name()
        self.quality = i.get_quality()['prettystr']
        self.material = self.get_material(i)
        self.classes = ','.join(j for j in i.get_equipable_classes())
        self.name2 = '%s %s' % (self.quality, self.name)
        self.image = i.get_image(i.ITEM_IMAGE_SMALL)
        self.id = i.get_id()

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

    def __repr__(self):
        s = u'%s %s' % (self.quality, self.name)
        return s.encode('utf-8')


class DB():
    def __init__(self, db):
        self.db = db
        self.conn = sqlite3.connect(self.db)
        self.c = self.conn.cursor()

    def initialize_db(self):
        self.c.execute('drop table if exists item')
        self.c.execute('''create table item (id integer primary key, quality text, name text, type text, class text, image text)''')
        self.c.execute('drop table if exists account')
        self.c.execute('''create table account (id integer primary key, account text, itemId integer, steamItemId)''')
        self.conn.commit()

    def get_account_items_steamids(self, account):
        r = self.c.execute('''select steamItemId from account where account=?''', [account])
        rows = [i[0] for i in r.fetchall()]
        return rows

    def insert_to_item_and_account(self, item, account):
        self.c.execute('''insert into item values (null, ?, ?, ?, ?, ?)''', (item.quality, item.name, item.material, item.classes, item.image))
        last = self.c.lastrowid
        self.c.execute('''insert into account values (null, ?, ?, ?)''', (account, last, item.id))
        self.conn.commit()

    def insert_to_account(self, item, account):
        r = self.c.execute('''select id from item where quality=? and name=?''', (item.quality, item.name))
        itemid = r.fetchone()[0]
        self.c.execute('''insert into account 
            values (null, ?, ?, ?)''', (account, itemid, item.id))
        self.conn.commit()

    def remove_from_account_by_steamitemid(self, itemid):
        self.c.execute('''delete from account where steamItemId=?''', [itemid])
        self.conn.commit()

    def remove_from_item_by_id(self, itemid):
        self.c.execute('''delete from item where id=?''', [itemid])
        self.conn.commit()

    def item_exists(self, item):
        exists = False
        results = self.c.execute('''select i.* from item i, account a 
                where i.quality=? and i.name=?''', (item.quality, item.name))
        if self.c.fetchall() != []:
            exists = True
        return exists

    def get_accounts_by_itemid(self, itemid):
        r = self.c.execute('''select account, count(account) from account where itemid=? group by account''', [itemid])
        return r.fetchall()

    # gets the item and also appends the accounts that have the item, along with the count
    def get_item_by_type(self, type):
        r = self.c.execute('''select * from item where type=?''', [type])
        tmp = r.fetchall()
        results2 = []

        # sorting
        results = []
        for q in ['Unusual', 'Strange', 'Genuine', 'Vintage', 'Haunted', 
                  'Community', 'Self-Made', 'Valve', 'Unique', 'Normal']:
            tmp2 = [i for i in tmp if i[1] == q]
            results = results + tmp2
            
        for i in results:
            accounts = self.get_accounts_by_itemid(i[0])
            accs = []
            for a in accounts:
                tmp = '%s: %s' % (a[0], a[1])
                accs.append(tmp)
            i = i + (accs,)
            results2.append(i)
        return results2

    def close(self):
        self.conn.close()

def generate_html():
    itemdb = os.path.join(os.path.dirname(sys.argv[0]), 'items.db')
    db = DB(itemdb)
    template = os.path.join(os.path.dirname(sys.argv[0]), 'makotemplate.txt')
    fullpath = os.path.join(options.htmldir, options.filename)

    miscs = db.get_item_by_type('misc')
    hats = db.get_item_by_type('hat')
    weapons = db.get_item_by_type('weapon')
    crates = db.get_item_by_type('crate')
    tools = db.get_item_by_type('tool')
    metal = db.get_item_by_type('metal')
    
    html = Template(filename=template).render(miscs=miscs, hats=hats, weapons=weapons, crates=crates, tools=tools, metal=metal)
    with codecs.open(fullpath, 'w', 'utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    options = Options()
    steam.base.set_api_key(options.apiKey)
    itemdb = os.path.join(os.path.dirname(sys.argv[0]), 'items.db')

    db = DB(itemdb)
    db.initialize_db()
    db.close()
    
    generate_html()
    
    while True:
        for steamId in options.accounts:
            try:
                backpack = steam.tf2.backpack(steamId)
                print 'bp query done: ', steamId
                Backpack(backpack, steamId)
                print 'loop done for: ', steamId
            except Exception as e:
                print 'Error getting backpack:', e
        generate_html()
        print 'HTML generated.'
        time.sleep(60*options.pollMinutes)
