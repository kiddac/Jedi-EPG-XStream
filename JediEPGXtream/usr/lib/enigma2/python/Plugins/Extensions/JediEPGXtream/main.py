#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _

from .plugin import skin_directory, screenwidth, hdr, epg_file, sourcelist, json_file, cfg
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from difflib import get_close_matches
from enigma import eTimer
from os import system, chmod
from Screens.Console import Console
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox

import gzip
import json
import os
import re
import sys
import shutil

try:
    pythonVer = sys.version_info.major
except:
    pythonVer = 2

try:
    from urlparse import urlparse, parse_qs
except:
    from urllib.parse import urlparse, parse_qs

divider = "═══════════ ALL ═══════════"


class JediEPGXtream_Main(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self.setup_title = (_('Jedi EPG XStream'))

        skin = skin_directory + 'epgmain.xml'

        if os.path.exists('/var/lib/dpkg/status'):
            skin = skin_directory + 'DreamOS/epgmain.xml'

        with open(skin, 'r') as f:
            self.skin = f.read()

        self['bouquet'] = Label(_("Bouquet"))
        self['channel'] = Label(_("Channel"))
        self['epgsource'] = Label(_("EPG Source"))
        self['epgselection'] = Label(_("EPG Selection"))

        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText('')
        self['key_yellow'] = StaticText('')
        self['key_blue'] = StaticText('')

        self["selection"] = Label()
        self["description"] = Label()
        self["extrainfo"] = Label()

        self.list1 = []
        self.list2 = []
        self.list3 = []
        self.list4 = []

        self.lastindex = 0

        self["list1"] = List(self.list1, enableWrapAround=True)
        self["list2"] = List(self.list2, enableWrapAround=True)
        self["list3"] = List(self.list3, enableWrapAround=True)
        self["list4"] = List(self.list4, enableWrapAround=True)

        self["list1"].onSelectionChanged.append(self.selection1Changed)
        self["list2"].onSelectionChanged.append(self.selection2Changed)
        self["list3"].onSelectionChanged.append(self.selection3Changed)
        self["list4"].onSelectionChanged.append(self.selection4Changed)

        self.selectedList = self["list1"]

        self["actions"] = ActionMap(["SetupActions", "DirectionActions", "WizardActions", "ColorActions", "MenuActions", "MoviePlayerActions"], {
            "ok": self.ok,
            "back": self.exit,
            "cancel": self.exit,
            "red": self.exit,
            "green": self.keygreen,
            "yellow": self.keyyellow,
            "blue": self.keyblue,
            "left": self.goLeft,
            "right": self.goRight,
            "up": self.goUp,
            "down": self.goDown,
            "channelUp": self.pageUp,
            "channelDown": self.pageDown,
            "prevBouquet": self.pageUp,
            "nextBouquet": self.pageDown,
            "0": self.reset,
            "2": self.prevLetter,
            "8": self.nextLetter
        }, -1)

        self.clear_caches()

        self.onFirstExecBegin.append(self.check_dependencies)
        self.onLayoutFinish.append(self.__layoutFinished)

    def enablelist1(self):
        instance1 = self["list1"].master.master.instance
        instance1.setSelectionEnable(1)

    def enablelist2(self):
        instance2 = self["list2"].master.master.instance
        instance2.setSelectionEnable(1)

    def enablelist3(self):
        instance3 = self["list3"].master.master.instance
        instance3.setSelectionEnable(1)

    def enablelist4(self):
        instance4 = self["list4"].master.master.instance
        instance4.setSelectionEnable(1)

    def disablelist1(self):
        instance1 = self["list1"].master.master.instance
        instance1.setSelectionEnable(0)

    def disablelist2(self):
        instance2 = self["list2"].master.master.instance
        instance2.setSelectionEnable(0)

    def disablelist3(self):
        instance3 = self["list3"].master.master.instance
        instance3.setSelectionEnable(0)

    def disablelist4(self):
        instance4 = self["list4"].master.master.instance
        instance4.setSelectionEnable(0)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

        self.enablelist1()
        self.disablelist2()
        self.disablelist3()
        self.disablelist4()

    def check_dependencies(self):
        dependencies = True
        if os.path.exists('/var/lib/dpkg/status'):
            try:
                import requests
                print("** *dependancies passed ***")
            except Exception as e:
                print(e)
                dependencies = False
        else:
            try:
                import requests
                from fuzzywuzzy import fuzz
                from fuzzywuzzy import process
                print("** *dependancies passed ***")
            except Exception as e:
                print(e)
                dependencies = False

        if dependencies is False:
            chmod("/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/dependencies.sh", 0o0755)
            cmd1 = ". /usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/dependencies.sh"
            self.session.openWithCallback(self.start, Console, title="Checking Python Dependencies", cmdlist=[cmd1], closeOnSuccess=False)
        else:
            self.start()

    def clear_caches(self):
        try:
            system("echo 1 > /proc/sys/vm/drop_caches")
            system("echo 2 > /proc/sys/vm/drop_caches")
            system("echo 3 > /proc/sys/vm/drop_caches")
        except:
            pass

    def start(self):
        self.getJsonFile()
        self.getJediSources()
        self.getSources()
        self.getBouquets()

    def getJsonFile(self):

        if not os.path.isfile(json_file):
            open(json_file, 'a').close()

        temp = {"Bouquets": [], "Sources": []}

        if not os.stat(json_file).st_size > 0:
            with open(json_file, "w") as f:
                json.dump(temp, f)

        self.epg_json = None

        with open(json_file) as f:
            try:
                self.epg_json = json.load(f)
            except:
                print("***** json fail ***** ")

        self.checkJsonFile()

    def checkJsonFile(self):
        for bouquet in self.epg_json['Bouquets']:
            bouquetfile = bouquet['bouquet']
            if os.path.exists(('/etc/enigma2/' + bouquetfile).encode("utf-8")):
                continue
            else:
                self.epg_json['Bouquets'].remove(bouquet)

        if self.epg_json['Bouquets'] == [{}]:
            self.epg_json['Bouquets'] = []

        if self.epg_json['Bouquets'] == []:
            self.epg_json['Sources'] = []

        with open(json_file, "w") as f:
            json.dump(self.epg_json, f)

    def getBouquets(self):
        self.list1 = []
        if os.path.isfile('/etc/enigma2/bouquets.tv') and os.stat('/etc/enigma2/bouquets.tv').st_size > 0:
            with open('/etc/enigma2/bouquets.tv') as f:
                for line in f:
                    bouquetname = ''
                    hassubbouquet = False

                    if line.startswith('#SERVICE') and "FROM BOUQUET" in line:
                        if "userbouquet.abm" in line or "#SERVICE 1:519" in line or "userbouquet.favourites" in line or "userbouquet.LastScanned.tv" in line or "_vod_" in line or "_series_" in line:
                            continue
                        else:
                            try:
                                bouquetpath = line.split('"')[1::2][0]
                                with open('/etc/enigma2/' + bouquetpath, "r") as userbouquetfile:
                                    for item in userbouquetfile:
                                        if "#NAME" in item:
                                            bouquetname = ' '.join(item.split()[1:])
                                            if " - " in bouquetname:
                                                bouquetname = bouquetname.partition(" - ")[-1]

                                        if "subbouquet" in item:
                                            hassubbouquet = True

                                            if bouquetname != "":
                                                break
                            except:
                                pass

                            self.list1.append(buildList1(bouquetname, hassubbouquet, bouquetpath, "Level1"))

        self["list1"].setList(self.list1)

    def getSubBouquets(self, subbouquet):
        self.list1 = []

        with open('/etc/enigma2/' + subbouquet, "r") as f:
            for line in f:
                bouquetname = ''
                if line.startswith('#SERVICE'):
                    bouquetpath = line.split('"')[1::2][0]
                    with open('/etc/enigma2/' + bouquetpath, "r") as userbouquetfile:
                        for item in userbouquetfile:
                            if "#NAME" in item:
                                bouquetname = ' '.join(item.split()[1:])
                                if " - " in bouquetname:
                                    bouquetname = bouquetname.partition(" - ")[-1]

                                if bouquetname != "":
                                    break

                    self.list1.append(buildList1(bouquetname, False, bouquetpath, "Level2"))
        self["list1"].setList(self.list1)

    def getChannels(self, bouquet):
        self.list2 = []
        with open('/etc/enigma2/' + bouquet, "r") as f:
            channelname = ''
            serviceref = ''
            epgid = ''

            for line in f:
                if line.startswith('#SERVICE'):
                    serviceref = line.split(' ')[1:][0].split('http')[0]

                if line.startswith('#DESCRIPTION'):
                    channelname = line.replace("#DESCRIPTION ", "").lstrip("~").lstrip("#").lstrip("-").lstrip("~").lstrip("<").lstrip("^").strip()
                    for bouq in self.epg_json['Bouquets']:
                        if bouq['bouquet'] == bouquet:
                            for channel in bouq['channel']:
                                if channel['description'] == channelname.strip():
                                    epgid = channel['epgid']
                                    break
                                else:
                                    epgid = ''

                    self.list2.append(buildList2(str(channelname).strip(), str(serviceref).strip(), str(epgid).strip()))
        self.list2.sort(key=lambda y: y[0].lower())
        self["list2"].setList(self.list2)

        self.disablelist2()

    def getJediSources(self):
        try:
            cfg_location = cfg.location.value
        except:
            cfg_location = '/etc/enigma2/jediplaylists/'

        if os.path.isfile(cfg_location + "playlists.txt") and os.stat(cfg_location + "playlists.txt").st_size > 0:
            with open(cfg_location + "playlists.txt", "r") as f:

                iptvs = []
                lines = f.readlines()
                f.seek(0)
                for line in lines:

                    if not line.startswith("http"):
                        continue

                    url = line.split(" ")[0]

                    scheme = 'http'
                    hostname = ''
                    domain = ''
                    username = ''
                    password = ''
                    port = 80
                    xmltv_api = ''

                    parsed = urlparse(url)
                    scheme = parsed.scheme
                    hostname = parsed.hostname
                    port = parsed.port or (443 if scheme == 'https' else 80)
                    domain = str(scheme) + "://" + str(hostname) + ":" + str(port) + "/"

                    query = parse_qs(parsed.query, keep_blank_values=True)

                    if "username" in query:
                        username = query['username'][0].strip()

                    if "password" in query:
                        password = query['password'][0].strip()

                    xmltv_api = str(domain) + 'xmltv.php?username=' + str(username) + '&password=' + str(password)

                    if 'get.php' in line and username != '' and password != '':
                        iptvline = "\n" + str(hostname) + " " + str(xmltv_api)
                        if iptvline.strip() not in iptvs:
                            iptvs.append(iptvline)

                for iptv in iptvs:
                    exists = False
                    with open(epg_file, "r") as f:
                        for line in f:
                            if iptv.strip() in line.strip():
                                exists = True
                                break

                    if exists is False:
                        with open(epg_file, "a") as f:
                            f.write(iptv)

    def getSources(self):
        self.list3 = []
        if os.path.isfile(epg_file) and os.stat(epg_file).st_size > 0:
            with open(epg_file) as f:
                for line in f:
                    if line != "\n" and not line.startswith("#") and len(line.strip()) != 0:
                        if " " in line:
                            name = line.split(" ")[0]
                            source = line.split(" ")[1].strip()
                            self.list3.append(buildList3(name, source))

        # self.list3.sort(key=lambda y: y[0].lower())
        self["list3"].setList(self.list3)
        self.disablelist3()

    def downloadSource(self, name, url):
        import requests
        try:
            r = requests.get(url, headers=hdr, stream=True, timeout=10)
            r.raise_for_status()
            if r.status_code == requests.codes.ok:

                if "xmltv.php" in url:
                    print("*** xmltv.php ***")
                    with open(sourcelist + "/" + name + ".xml", 'wb') as fd:
                        for chunk in r.iter_content(chunk_size=1024):
                            fd.write(chunk)
                else:
                    print("*** not xmltv.php ***")
                    extension = url.split(".")[-1]
                    with open(sourcelist + "/" + name + "." + extension, 'wb') as fd:
                        for chunk in r.iter_content(chunk_size=1024):
                            fd.write(chunk)

                self["extrainfo"].text = (_("Extracting source...please wait."))
                self.timer = eTimer()
                try:
                    self.timer_conn = self.timer.timeout.connect(boundFunction(self.openSource, name, url))
                except:
                    try:
                        self.timer.callback.append(boundFunction(self.openSource, name, url))
                    except:
                        self.openSource(name, url)
                self.timer.start(5, True)
            else:
                print("**** bad response ***")

        except requests.exceptions.ConnectionError as e:
            print(("Error Connecting: %s" % e))
            self["extrainfo"].text = (_("Download failed. Try again later."))

        except requests.exceptions.RequestException as e:
            print(e)
            self["extrainfo"].text = (_("Download failed. Try again later."))

    def openSource(self, name, url):
        haslzma = False

        if url.endswith('xz') or url.endswith('gz'):
            try:
                import lzma
                print('\nlzma success')
                haslzma = True

            except ImportError:
                try:
                    from backports import lzma
                    print("\nbackports lzma success")
                    haslzma = True

                except ImportError:
                    print("\nlzma failed")
                    pass

                except:
                    print("\n ***** missing lzma module ***** ")
                    pass

            if url.endswith('xz') and haslzma and os.path.isfile(str(sourcelist) + "/" + str(name) + ".xz"):
                with lzma.open(str(sourcelist) + "/" + str(name) + ".xz", mode='rt', encoding='utf-8') as f:
                    output = f.read()

                with open(str(sourcelist) + "/" + str(name) + ".xml", 'w') as outfile:
                    outfile.write(output)

            elif url.endswith('gz') and haslzma and os.path.isfile(str(sourcelist) + "/" + str(name) + ".gz"):
                decompressedFile = gzip.GzipFile(str(sourcelist) + "/" + str(name) + ".gz", mode='rb')
                with open(str(sourcelist) + "/" + str(name) + ".xml", 'wb') as outfile:
                    shutil.copyfileobj(decompressedFile, outfile)

        self["extrainfo"].text = (_("Parsing XML...please wait."))
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(boundFunction(self.parseXMLFile, name, url))
        except:
            try:
                self.timer.callback.append(boundFunction(self.parseXMLFile, name, url))
            except:
                self.parseXMLFile(name, url)
        self.timer.start(5, True)

    def parseXMLFile(self, name, url):
        epgidlist = []
        self.list4 = []

        pattern = re.compile(r'id="(?P<value>[^\"]+)"')

        with open(str(sourcelist) + "/" + str(name) + ".xml", 'r') as f:
            for txt in pattern.finditer(f.read()):
                channelid = txt.group('value').strip()
                epgidlist.append(channelid)

        epgidlist = list(set(epgidlist))
        epgidlist.sort(key=lambda y: y.lower())

        # output simple channel list to .txt file
        with open(str(sourcelist) + "/" + str(name) + ".txt", 'w') as textfile:
            for line in epgidlist:
                textfile.write(line + "\n")

        # remove xml, gz, xz files

        if os.path.isfile(str(sourcelist) + "/" + str(name) + ".xz"):
            os.remove(str(sourcelist) + "/" + str(name) + ".xz")
        if os.path.isfile(str(sourcelist) + "/" + str(name) + ".gz"):
            os.remove(str(sourcelist) + "/" + str(name) + ".gz")
        if os.path.isfile(str(sourcelist) + "/" + str(name) + ".xml"):
            os.remove(str(sourcelist) + "/" + str(name) + ".xml")

        self["extrainfo"].text = (_("Finding closest matches."))
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(boundFunction(self.getMatchList, name))
        except:
            try:
                self.timer.callback.append(boundFunction(self.getMatchList, name))
            except:
                self.getMatchList(name)
        self.timer.start(5, True)

    def getMatchList(self, name):
        try:
            from fuzzywuzzy import fuzz
            from fuzzywuzzy import process
            fuzzy = True
        except:
            fuzzy = False

        self.list4 = []
        epgidlist = []
        originallist = []

        namelist = []
        sourcelistpath = str(sourcelist) + "/" + str(name) + ".txt"

        fulllist = []

        if os.path.isfile(sourcelistpath) and os.stat(sourcelistpath).st_size > 0:
            self["extrainfo"].text = (_("Finding closest matches."))
            text = ""

            with open(sourcelistpath, 'r') as epglist:
                for line in epglist:
                    epgidlist.append(str(line).lower().strip())
                    originallist.append(str(line).strip())

                    fulllist.append(buildList4(str(line).lower().strip(), False, str(line).strip()))

            matchlist = []
            namelist = []

            if fuzzy:
                matchlist = process.extract(self["list2"].getCurrent()[0], epgidlist, limit=42, scorer=fuzz.token_sort_ratio)

                for match in matchlist:
                    if match[1] >= 40:
                        namelist.append(match[0])
            else:
                current = self["list2"].getCurrent()[0].lower().lstrip("~").lstrip("#").lstrip("-").lstrip("~").lstrip("<").lstrip("^").replace(" ", "")
                namelist = get_close_matches(current, epgidlist, n=42, cutoff=0.20)

            if not namelist:
                text = (_("No close matches"))
                namelist.append(text)

            namelist = [[i, True] for i in namelist]

            for item in namelist:
                original = ""
                for entry in originallist:
                    if str(item[0]).lower() == str(entry).lower():
                        original = str(entry)
                        break
                self.list4.append(buildList4(str(item[0]), str(item[1]), str(original)))

            self.list4.append(buildList4(str(divider), False, str("")))

            for item in epgidlist:
                original = ""
                for entry in originallist:
                    if str(item).lower() == str(entry).lower():
                        original = str(entry)
                        break
                self.list4.append(buildList4(str(item), False, str(original)))

        else:
            text = (_("Press Yellow to refresh source"))
            namelist.append(text)

            namelist = [[i, True] for i in namelist]

            for item in namelist:
                original = ""
                for entry in originallist:
                    if str(item[0]).lower() == str(entry).lower():
                        original = str(entry)
                        break
                self.list4.append(buildList4(str(item[0]), str(item[1]), str(original)))

        self["list4"].setList(self.list4)

        self.disablelist4()
        self["extrainfo"].text = ("")

    def hideSource(self):
        item = self["list3"].getCurrent()
        if item:
            name = item[0]
            url = item[1]

        if os.path.isfile(epg_file) and os.stat(epg_file).st_size > 0:
            with open(epg_file, 'r+') as f:
                new_f = f.readlines()
                f.seek(0)
                for line in new_f:
                    if name in line and url in line:
                        line = line = "#" + line
                    f.write(line)
                f.truncate()

        self.getSources()
        self.enablelist3()

    def assignEPG(self):
        bouquet = self["list1"].getCurrent()[3]
        channelname = self["list2"].getCurrent()[0]
        serviceref = self["list2"].getCurrent()[2]
        sourcename = self["list3"].getCurrent()[0]
        sourceurl = self["list3"].getCurrent()[1]
        epgid = self["list4"].getCurrent()[2]

        # add source to source list
        sourceexists = False
        if self.epg_json['Sources'] == []:
            self.epg_json['Sources'].append({"name": sourcename, "source": sourceurl})
        else:
            for source in self.epg_json['Sources']:
                if source['name'] == sourcename and source['source'] == sourceurl:
                    sourceexists = True

            if sourceexists is False:
                self.epg_json['Sources'].append({"name": sourcename, "source": sourceurl})

        # if bouquet doesn't exist create new entry
        if self.epg_json['Bouquets'] == []:
            new_bouquet = {"bouquet": bouquet, "channel": [{"serviceid": serviceref, "description": channelname, "epgid": epgid, "source": sourceurl, "sourcename": sourcename}]}
            self.epg_json['Bouquets'].append(new_bouquet)
        else:
            bouquetexists = False

            for jsonbouquet in self.epg_json['Bouquets']:
                channelexists = False

                if jsonbouquet["bouquet"] == bouquet:
                    bouquetexists = True

                    for channel in jsonbouquet["channel"]:
                        if channel["serviceid"] == serviceref and channel["description"] == channelname:
                            channelexists = True
                            channel["epgid"] = epgid
                            channel["source"] = sourceurl
                            channel["sourcename"] = sourcename
                            break

                    if not channelexists:
                        new_channel = {"serviceid": serviceref, "description": channelname, "epgid": epgid, "source": sourceurl, "sourcename": sourcename}
                        jsonbouquet['channel'].append(new_channel)

                    break

            if not bouquetexists:
                new_bouquet = {"bouquet": bouquet, "channel": [{"serviceid": serviceref, "description": channelname, "epgid": epgid, "source": sourceurl, "sourcename": sourcename}]}
                self.epg_json['Bouquets'].append(new_bouquet)

        # remove sources from source list
        if self.epg_json['Sources'] != []:
            sourcelist = []
            if self.epg_json['Bouquets'] != []:
                for jsonbouquet in self.epg_json['Bouquets']:
                    if "channel" in jsonbouquet:
                        if jsonbouquet["channel"] != []:
                            for channel in jsonbouquet["channel"]:
                                if channel['source'] not in sourcelist:
                                    sourcelist.append(channel['source'])

            for source in self.epg_json['Sources']:
                if source['source'] not in sourcelist:
                    self.epg_json['Sources'].remove(source)

        with open(json_file, "w") as f:
            json.dump(self.epg_json, f)

        self.buildXMLSourceFile()
        self.buildXMLChannelFile()

        self.goLeft()
        self.goLeft()
        self.getChannels(bouquet)
        self.enablelist2()
        self.selectedList.setIndex(self.lastindex)

    def unassignEPG(self):
        bouquet = self["list1"].getCurrent()[3]
        channelname = self["list2"].getCurrent()[0]
        serviceref = self["list2"].getCurrent()[2]

        for jsonbouquet in self.epg_json['Bouquets']:
            if jsonbouquet['bouquet'] == bouquet:
                for channel in jsonbouquet["channel"]:
                    if channel["serviceid"] == serviceref and channel["description"] == channelname:
                        jsonbouquet["channel"].remove(channel)
                        if jsonbouquet["channel"] == []:
                            self.epg_json['Bouquets'].remove(jsonbouquet)
                        break

                if self.epg_json['Bouquets'] == [{}]:
                    self.epg_json['Bouquets'] = []

                if self.epg_json['Bouquets'] == []:
                    self.epg_json['Sources'] = []

                break

        # remove sources from source list
        if self.epg_json['Sources'] != []:
            sourcelist = []
            if self.epg_json['Bouquets'] != []:
                for jsonbouquet in self.epg_json['Bouquets']:
                    if "channel" in jsonbouquet:
                        if jsonbouquet["channel"] != []:
                            for channel in jsonbouquet["channel"]:
                                if channel['source'] not in sourcelist:
                                    sourcelist.append(channel['source'])

            for source in self.epg_json['Sources']:
                if source['source'] not in sourcelist:
                    self.epg_json['Sources'].remove(source)

        with open(json_file, "w") as f:
            json.dump(self.epg_json, f)

        self.buildXMLSourceFile()
        self.buildXMLChannelFile()
        self.getChannels(bouquet)
        self.enablelist2()
        self.selectedList.setIndex(self.lastindex)

    def unassignBouquet(self):
        bouquet = self["list1"].getCurrent()[3]

        for jsonbouquet in self.epg_json['Bouquets']:
            if jsonbouquet['bouquet'] == bouquet:
                self.epg_json['Bouquets'].remove(jsonbouquet)
                break

        with open(json_file, "w") as f:
            json.dump(self.epg_json, f)

        self.buildXMLSourceFile()
        self.buildXMLChannelFile()
        self.getChannels(bouquet)
        self.enablelist2()
        self.selectedList.setIndex(self.lastindex)

    def buildXMLSourceFile(self):
        filepath = '/etc/epgimport/'
        epgfilename = 'jex.channels.xml'
        filename = 'jex.sources.xml'
        sourcepath = filepath + filename

        with open(sourcepath, 'w') as f:
            xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
            xml_str += '<sources>\n'
            xml_str += '<sourcecat sourcecatname="Jedi EPG">\n'

            if 'Sources' in self.epg_json:
                for epgsources in self.epg_json['Sources']:
                    xml_str += '<source type="gen_xmltv" nocheck="1" channels="' + str(epgfilename) + '">\n'
                    xml_str += '<description>' + str(epgsources["name"]) + '</description>\n'
                    xml_str += '<url><![CDATA[' + str(epgsources["source"]) + ']]></url>\n'
                    xml_str += '</source>\n'

            xml_str += '</sourcecat>\n'
            xml_str += '</sources>\n'
            f.write(xml_str)

    def buildXMLChannelFile(self):
        filepath = '/etc/epgimport/'
        epgfilename = 'jex.channels.xml'
        channelpath = filepath + epgfilename
        with open(channelpath, 'w') as f:
            xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
            xml_str += '<channels>\n'

            if 'Bouquets' in self.epg_json:
                for bouquet in self.epg_json['Bouquets']:
                    if "channel" in bouquet:
                        for channel in bouquet["channel"]:
                            serviceid = str(channel["serviceid"])
                            convertedserviceid = serviceid.replace(serviceid.split(":")[0], "1")
                            xml_str += '<channel id="' + str(channel["epgid"]) + '">' + str(convertedserviceid) + 'http%3a//example.m3u8</channel> <!-- ' + str(channel["description"]) + '-->\n'

            xml_str += '</channels>\n'
            f.write(xml_str)

    def moveToAssigned(self):
        pos = 0
        current_bouquet = self["list1"].getCurrent()[3]
        current_channel = self["list2"].getCurrent()[0]
        current_ref = self["list2"].getCurrent()[2]

        for jsonbouquet in self.epg_json['Bouquets']:
            if jsonbouquet["bouquet"] == current_bouquet:

                for channel in jsonbouquet["channel"]:
                    if channel["serviceid"] == current_ref and channel["description"] == current_channel:
                        if self.selectedList == self["list3"]:
                            for position in self.list3:
                                if "sourcename" in channel:
                                    if position[0] == channel["sourcename"]:
                                        self["list3"].setIndex(pos)
                                    pos += 1
                        if self.selectedList == self["list4"]:
                            for position in self.list4:
                                if position[0] == channel["epgid"]:
                                    self["list4"].setIndex(pos)
                                pos += 1

    def getNextList(self):
        if self["list1"].getCurrent()[2] is False:
            self.getChannels(self["list1"].getCurrent()[3])

    def prevLetter(self):

        if self.selectedList.getCurrent():
            catchup = False
            current = ord((self.selectedList.getCurrent()[0][0]).lower())
            if current == 126 or current == 33 or current == 35 or current == 45 or current == 60 or current == 94:
                catchup = True
                current = ord((self.selectedList.getCurrent()[0][1]).lower())
            self.goUp()
            letter = ord((self.selectedList.getCurrent()[0][0]).lower())
            if catchup:
                letter = ord((self.selectedList.getCurrent()[0][1]).lower())
            while letter == current:
                self.goUp()
                letter = ord((self.selectedList.getCurrent()[0][0]).lower())
                if catchup:
                    letter = ord((self.selectedList.getCurrent()[0][1]).lower())

    def nextLetter(self):
        if self.selectedList.getCurrent():
            catchup = False
            current = ord((self.selectedList.getCurrent()[0][0]).lower())
            if current == 126 or current == 33 or current == 35 or current == 45 or current == 60 or current == 94:
                catchup = True
                current = ord((self.selectedList.getCurrent()[0][1]).lower())
            self.goDown()
            letter = ord((self.selectedList.getCurrent()[0][0]).lower())
            if catchup:
                letter = ord((self.selectedList.getCurrent()[0][1]).lower())

            while letter == current:
                self.goDown()
                letter = ord((self.selectedList.getCurrent()[0][0]).lower())
                if catchup:
                    letter = ord((self.selectedList.getCurrent()[0][1]).lower())

    def selectionChanged(self):
        if self.selectedList == self["list1"]:
            self.selection1Changed()
        if self.selectedList == self["list2"]:
            self.selection2Changed()
        if self.selectedList == self["list3"]:
            self.selection3Changed()
        if self.selectedList == self["list4"]:
            self.selection4Changed()

    def selection1Changed(self):
        if self.selectedList.getCurrent() and self.selectedList == self["list1"]:
            self['key_green'].text = ('')
            self['key_yellow'].text = ('')
            self['key_blue'].text = ('')

            item = self["list1"].getCurrent()
            if item:
                self['selection'].text = item[0]
                self["description"].text = (_("Select Bouquet."))

                if item[2] is False:
                    self.getNextList()

    def selection2Changed(self):
        if self.selectedList.getCurrent() and self.selectedList == self["list2"]:

            self['key_yellow'].text = ('')
            self['key_blue'].text = (_('Unassign All'))

            if self["list2"].getCurrent()[3] != '':
                self['key_green'].text = (_('Unassign EPG'))
            else:
                self['key_green'].text = ('')

            item = self["list2"].getCurrent()
            if item:
                self['selection'].text = item[0]
                self["description"].text = (_("Select Channel."))

    def selection3Changed(self):
        if self.selectedList.getCurrent() and self.selectedList == self["list3"]:
            self['key_green'].text = ('')
            self['key_yellow'].text = (_('Update Source'))
            self['key_blue'].text = (_('Hide Source'))

            item = self["list3"].getCurrent()
            if item:
                self['selection'].text = item[0]
                self["description"].text = (_("Select EPG Source. Press Yellow to refresh and update EPG Source. Optional"))

                name = item[0]
                # url = item[1]

                self["extrainfo"].text = (_("Finding closest matches."))
                self.timer = eTimer()
                try:
                    self.timer_conn = self.timer.timeout.connect(boundFunction(self.getMatchList, name))
                except:
                    try:
                        self.timer.callback.append(boundFunction(self.getMatchList, name))
                    except:
                        self.getMatchList(name)
                self.timer.start(5, True)

    def selection4Changed(self):
        if self.selectedList.getCurrent() and self.selectedList == self["list4"]:
            self['key_green'].text = (_('Assign EPG'))
            self['key_yellow'].text = ('')
            # self['key_blue'].text = (_('Toggle All/Matches'))

            item = self["list4"].getCurrent()
            if item:
                self['selection'].text = item[0]
                self["description"].text = (_("Select the closest EPG ID reference."))

    def ok(self):
        if self.selectedList == self["list1"]:
            self.goRight()

        elif self.selectedList == self["list2"]:
            self.goRight()

        elif self.selectedList == self["list3"]:
            if self["list4"].getCurrent()[0] == (_("Press Yellow to refresh source")):
                self.keyyellow()
            else:
                self.goRight()

        elif self.selectedList == self["list4"]:
            self.keygreen()

    def exit(self):
        self.session.openWithCallback(self.exit2, MessageBox, _('To view newly assigned EPGs. Select and save Jedi EPG in EPGIMPORT sources and do a manual import.'), type=MessageBox.TYPE_INFO, timeout=10)

    def exit2(self, answer=None):
        self.close()

    def keygreen(self):
        if self['key_green'].getText():
            if self.selectedList == self["list2"]:
                self.unassignEPG()
            if self.selectedList == self["list4"]:
                self.assignEPG()

    def keyyellow(self):
        if self['key_yellow'].getText():
            if self.selectedList == self["list3"]:
                item = self["list3"].getCurrent()
                if item:
                    name = item[0]
                    url = item[1]

                    self["extrainfo"].text = (_("Downloading source...please wait."))
                    self.timer = eTimer()
                    try:
                        self.timer_conn = self.timer.timeout.connect(boundFunction(self.downloadSource, name, url))
                    except:
                        try:
                            self.timer.callback.append(boundFunction(self.downloadSource, name, url))
                        except:
                            self.downloadSource(name, url)
                    self.timer.start(5, True)

    def keyblue(self):
        if self['key_blue'].getText():

            if self.selectedList == self["list2"]:
                self.unassignBouquet()
            if self.selectedList == self["list3"]:
                self.hideSource()

    def goLeft(self):
        if self.selectedList.getCurrent():
            if self.selectedList == self["list4"]:
                self.selectedList = self["list3"]
                self.enablelist3()
                self.disablelist4()

            elif self.selectedList == self["list3"]:
                self.selectedList = self["list2"]
                self.enablelist2()
                self.disablelist3()

            elif self.selectedList == self["list2"]:
                self.selectedList = self["list1"]
                self.enablelist1()
                self.disablelist2()

            elif self.selectedList == self["list1"]:
                if self["list1"].getCurrent()[4] == "Level2":
                    self.getBouquets()
                if self["list1"].getCurrent()[4] == "Level1" and self["list1"].getCurrent()[2] is True:
                    self.list2 = []
                    self["list2"].setList(self.list2)

            self.selectionChanged()

    def goRight(self):
        if self.selectedList.getCurrent():
            if self.selectedList == self["list1"]:
                if self["list1"].getCurrent()[2] is True:
                    self.getSubBouquets(self["list1"].getCurrent()[3])
                    self.selectedList.setIndex(0)
                else:
                    self.selectedList = self["list2"]
                    self.selectedList.setIndex(0)
                    self.enablelist2()

            elif self.selectedList == self["list2"]:
                self.lastindex = self.selectedList.getIndex()
                self.selectedList = self["list3"]
                self.enablelist3()

            elif self.selectedList == self["list3"]:
                if self["list4"].getCurrent() and self["list4"].getCurrent()[0] != (_("Press Yellow to refresh source")):
                    self.selectedList = self["list4"]

                    if self["list4"].getCurrent()[0] == (_("No close matches")):
                        self["list4"].setIndex(2)
                    else:
                        self["list4"].setIndex(0)
                    self.enablelist4()

            if self.selectedList != self["list1"] and self["list2"].getCurrent() and self["list2"].getCurrent()[3] != '':
                self.moveToAssigned()

            self.selectionChanged()

    def goUp(self):
        if self.selectedList.getCurrent():
            instance = self.selectedList.master.master.instance
            instance.moveSelection(instance.moveUp)
            if self.selectedList == self["list4"] and (self["list4"].getCurrent()[0] == divider or self["list4"].getCurrent()[0] == (_("No close matches"))):
                self.goUp()

    def goDown(self):
        if self.selectedList.getCurrent():
            instance = self.selectedList.master.master.instance
            instance.moveSelection(instance.moveDown)
            if self.selectedList == self["list4"] and (self["list4"].getCurrent()[0] == divider or self["list4"].getCurrent()[0] == (_("No close matches"))):
                self.goDown()

    def pageUp(self):
        if self.selectedList.getCurrent():
            instance = self.selectedList.master.master.instance
            instance.moveSelection(instance.pageUp)
            if self.selectedList == self["list4"] and (self["list4"].getCurrent()[0] == divider or self["list4"].getCurrent()[0] == (_("No close matches"))):
                self.goDown()

    def pageDown(self):
        if self.selectedList.getCurrent():
            instance = self.selectedList.master.master.instance
            instance.moveSelection(instance.pageDown)
            if self.selectedList == self["list4"] and (self["list4"].getCurrent()[0] == divider or self["list4"].getCurrent()[0] == (_("No close matches"))):
                self.goDown()

    def reset(self):
        if self.selectedList.getCurrent():
            self.selectedList.setIndex(0)


def buildList1(bouquetname, subbouquet, userbouquet, level):
    png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/icons/tv.png")
    if subbouquet is True:
        png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/icons/folder.png")

    if screenwidth.width() > 1280:
        png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/icons/tv-large.png")

        if subbouquet is True:
            png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/icons/folder-large.png")

    return (bouquetname, png, subbouquet, userbouquet, level)


def buildList2(channel, serviceref, epgid):
    png = None
    if epgid != '':
        png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/icons/link.png")

    if screenwidth.width() > 1280:
        if epgid != '':
            png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/JediEPGXtream/icons/link-large.png")

    return (channel, png, serviceref, epgid)


def buildList3(name, source):
    return (name, source)


def buildList4(epg_id, fuzzy, original):
    return (epg_id, fuzzy, original)
