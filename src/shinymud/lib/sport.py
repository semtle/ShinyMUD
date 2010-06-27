from shinymud.models.area import Area
from shinymud.models.room import Room
from shinymud.models.item import BuildItem
from shinymud.models.npc import Npc
from shinymud.lib.world import World
from shinymud.data.config import AREAS_IMPORT_DIR, AREAS_EXPORT_DIR, VERSION

import os
import re
import json
import traceback

class SPort(object):
    """Export and import areas (and their objects) to a file."""
    def __init__(self, import_dir=AREAS_IMPORT_DIR, export_dir=AREAS_EXPORT_DIR):
        self.world = World.get_world()
        self.import_dir = import_dir
        self.export_dir = export_dir
    
    def import_list(self, area_list):
        """Import a batch of area files from area_list.
        area_list can either be a list of area-names to be imported,
        or the string 'all'. If the string 'all' is given, import_list will
        attempt to import all areas in self.import_dir
        """
        results = ''
        if area_list == 'all':
            area_list = [area.replace('.txt', '') for area in\
                         os.listdir(self.import_dir) if\
                         area.endswith('.txt')]
            if not area_list:
                return "I couldn't find any pre-packaged areas.\n"
        for area in area_list:
            results += 'Importing %s.txt... ' % area
            area_obj = self.world.get_area(area)
            if area_obj:
                results += 'Aborted: area %s already exists.\n' % area_obj.name
            else:
                try:
                    status = self.import_from_shiny(area)
                except SPortImportError, e:
                    results += 'Failed: ' + str(e) + '\n'
                else:
                    results += status + '\n'
        if not results:
            return 'No pre-packaged areas were found.\n'
        return results
                
    
    @classmethod
    def list_importable_areas(cls, import_dir=AREAS_IMPORT_DIR):
        if not os.path.exists(import_dir):
            return 'There are no area files in your import directory.'
        # Give the player a list of names of all the area files in their import directory
        # and trim off the .txt extension for readibility. Ignore all files that aren't txt
        # files
        alist = [area.replace('.txt', '') for area in os.listdir(import_dir) if area.endswith('.txt')]
        if alist:
            string = ' Available For Import '.center(50, '-')
            string += '\n' + '\n'.join(alist) + '\n' + ('-' * 50)
            return string
        else:
            return 'There are no area files in your import directory.'
    
    def check_export_path(self):
        """Make sure the path to the export directory exists. If it doesn't,
        create it and return an empty string. If there's an error, log it and
        return an error message."""
        if not os.path.exists(self.export_dir):
            try:
                os.mkdir(self.export_dir)
            except Exception, e:
                self.world.log.error('EXPORT FAILED: ' + str(e))
                # TODO: reraise an SPortExportError here...
                return 'Export failed; something went wrong accessing the export directory for areas.'
        return ''
    
    def get_import_data(self, filename):
        """Retrieve the area data from the file specified by filename.
        Raise an SPortImportError if the file doesn't exist or opening the file
        fails.
        filename -- the name of the file the area data should be read from
        """
        filepath = os.path.join(self.import_dir, filename)
        if not os.path.exists(filepath):
            raise SPortImportError('Error: %s does not exist.' % filename)
            
        try:
            f = open(filepath, 'r')
        except IOError, e:
            self.world.log.debug(str(e))
            raise SPortImportError('Error: opening the area file failed. '
                                   'Check the logfile for details.')
        else:
            area_txt = f.read()
        finally: 
            f.close()
            
        return area_txt
    
    def save_to_file(self, file_content, file_name):
        """Write out the file contents under the given file_name."""
        filepath = os.path.join(self.export_dir, file_name)
        try:
            f = open(filepath, 'w')
        except IOError, e:
            self.world.log.debug(str(e))
            raise SPExportError('Error writing your area to file. '
                                'Check the logfile for details')
        else:
            f.write(file_content)
        finally:
            f.close()
        return 'Export complete! Your area can be found at:\n%s' % filepath
    

class SPortImportError(Exception):
    """The umbrella exception for errors that occur during area import.
    """
    pass
    

class SPortExportError(Exception):
    """The umbrella exception for errors that occur during area export.
    """
    pass


class ShinyAreaFormat(SPort):
    """ Export and Import areas in ShinyAreaFormat.
    """
    def export(self, area):
        """Export an area to a text file in ShinyAreaFormat.
        area -- the area object to be exported
        """
        error = self.check_export_path()
        if error:
            return error
        shiny_area = ('[ShinyMUD Version "%s"]\n' % VERSION +
                      self._prep_area(area) +
                      self._prep_scripts(area) +
                      self._prep_items(area) +
                      self._prep_npcs(area) +
                      self._prep_rooms(area)
                     )
        return self.save_to_file(shiny_area, area.name + '.txt')
    
    def inport(self, areaname):
        """Import an area from a text file in ShinyAreaFormat."""
        txt = self.get_import_data(areaname + '.txt')
        # Assemble the data structures from the file text
        area = json.loads(self._match_shiny_tag('Area', txt))
        scripts = json.loads(self._match_shiny_tag('Scripts', txt))
        items = json.loads(self._match_shiny_tag('Items', txt))
        itypes = json.loads(self._match_shiny_tag('Item Types', txt))
        npcs = json.loads(self._match_shiny_tag('Npcs', txt))
        npc_events = json.loads(self._match_shiny_tag('Npc Events', txt))
        rooms = json.loads(self._match_shiny_tag('Rooms', txt))
        room_exits = json.loads(self._match_shiny_tag('Room Exits', txt))
        room_spawns = json.loads(self._match_shiny_tag('Room Spawns', txt))
        # Build the area from the assembled dictionary data
        try:
            new_area = Area.create(area)
            for script in scripts:
                new_area.new_script(script)
            self.world.log.debug('Finished Scripts.')
            for item in items:
                self.world.log.debug('In item, %s' % item['id'])
                new_area.new_item(item)
            self.world.log.debug('Finished Items.')
            for itype in itypes:
                # Get this itype's item by that item's id
                my_item = new_area.get_item(itype['item'])
                my_item.build_add_type(itype['item_type'], itype)
            self.world.log.debug('Finished Item types.')
            for npc in npcs:
                new_area.new_npc(npc)
            for event in npc_events:
                my_script = new_area.get_script(str(event['script']))
                event['script'] = my_script
                my_npc = new_area.get_npc(event['prototype'])
                my_npc.new_event(event)
            for room in rooms:
                new_room = new_area.new_room(room)
                my_spawns = room_spawns.get(new_room.id)
                if my_spawns:
                    new_room.load_spawns(my_spawns)
            for exit in room_exits:
                self.world.log.debug(exit['room'])
                my_room = new_area.get_room(str(exit['room']))
                my_room.new_exit(exit)
        except Exception, e:
            # if anything went wrong, make sure we destroy whatever parts of
            # the area that got created. This way, we won't run into problems
            # if they try to import it again, and we won't leave orphaned or
            # erroneous data in the db.
            self.world.log.error(traceback.format_exc())
            self.world.destroy_area(areaname, 'SPort Error')
            raise SPortImportError('There was a horrible error on import! '
                                   'Aborting! Check logfile for details.')
        new_area.reset()
        
        return '%s has been successfully imported.' % new_area.title
    
    def _match_shiny_tag(self, tag, text):
        """Match a ShinyTag from the ShinyAreaFormat.
        tag -- the name of the tag you wish to match
        text -- the text to be searched for the tags
        Returns the string between the tag and its matching end-tag.
        Raises an exception if the tag is not found.
        """
        exp = r'\[' + tag + r'\](\n)?(?P<tag_body>.*?)(\n)?\[End ' + tag +\
              r'\](\n)?'
        match = re.search(exp, text, re.I | re.S)
        if not match:
            raise SPortImportError('Corrupted file: missing or malformed %s tag.' % tag)
        return match.group('tag_body')
    
    def _prep_area(self, area):
        d = area.create_save_dict()
        del d['dbid']
        return '\n[Area]\n' + json.dumps(d) + '\n[End Area]\n'
    
    def _prep_scripts(self, area):
        s = []
        for script in scripts.values():
            d = script.create_save_dict()
            del d['dbid']
            s.append(d)
        return '\n[Scripts]\n' + json.dumps(s) + '\n[End Scripts]\n'
    
    def _prep_items(self, area):
        item_list = []
        itypes_list = []
        
        for item in area.items.values():
            d = item.create_save_dict()
            del d['dbid']
            item_list.append(d)
            for key,value in item.item_types.items():
                d = value.create_save_dict()
                d['item'] = item.id
                del d['dbid']
                d['item_type'] = key
                itypes_list.append(d)
        s = '\n[Items]\n' + json.dumps(item_list) + '\n[End Items]\n'
        s += '\n[Item Types]\n' + json.dumps(itypes_list) + '\n[End Item Types]\n'
        return s
    
    def _prep_npcs(self, area):
        npc_list = []
        npc_elist = []
        
        for npc in area.npcs.values():
            d = npc.create_save_dict()
            del d['dbid']
            npc_list.append(d)
            event_list = []
            for elist in npc.events.values():
                event_list.extend(elist)
            for event in event_list:
                d = event.create_save_dict()
                del d['dbid']
                d['prototype'] = npc.id
                d['script'] = event.script.id
                npc_elist.append(d)
        s = '\n[Npcs]\n' + json.dumps(npc_list) + '\n[End Npcs]\n'
        s += '\n[Npc Events]\n' + json.dumps(npc_elist) + '\n[End Npc Events]\n'
        return s
    
    def _prep_rooms(self, area):
        r_list = []
        r_exits = []
        r_spawns = {} # r_spawns is a dictionary of lists of dictionaries!
        for room in area.rooms.values():
            d = room.create_save_dict()
            # d['room'] = room.id
            del d['dbid']
            r_list.append(d)
            r_spawns[room.id] = []
            for exit in room.exits.values():
                if exit:
                    d = exit.create_save_dict()
                    d['room'] = room.id
                    d['to_id'] = exit.to_room.id
                    d['to_area'] = exit.to_room.area.name
                    d['to_room'] = None
                    del d['dbid']
                    r_exits.append(d)
            for spawn in room.spawns.values():
                d = spawn.create_save_dict()
                del d['dbid']
                r_spawns[room.id].append(d)
        s = '\n[Rooms]\n' + json.dumps(r_list) + '\n[End Rooms]\n'
        s += '\n[Room Exits]\n' + json.dumps(r_exits) + '\n[End Room Exits]\n'
        s += '\n[Room Spawns]\n' + json.dumps(r_spawns) + '\n[End Room Spawns]\n'
        return s
    

