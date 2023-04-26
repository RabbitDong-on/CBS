#!/usr/bin/python

"""A script that generate a table in html for any raw tags.

Usage:

top-k.py [tagcode] [sysname]

Ouput:
/tmp/search.html

"""

#library
import os, re, sys, subprocess, operator

# get key of dict from value of dict
def get_key_from_value(my_dict, v):
    for key,value in my_dict.items():
        if value == v:
            return key
    return None

# List of names who has discussed an issue
WHO = ['al','ke','ja','as','ah','vm','jf','mz','tl','td', 'hg','sl']

OPTIONS = ['bynewest','byoldest', 'byttr', 'bycomm']

# Systems name - shorten name
SYSTEMS = {'MAPREDUCE':'mr', 'HBASE':'hb', 'CASSANDRA':'ca',
           'HDFS':'hd', 'ZOOKEEPER':'zk', 'FLUME':'fl'}
# Systems to check
CHECKSYSTEMS = []
           
# Type of tags in all systems
TAGFILTERS = []
# Tags to filter
CHECKTAGFILTERS = []

# Various aspects of a issue
DESC = 'desc'  # General description
COMP = 'comp'  # Component, e.g., ipc, spec. exec.
TEST = 'test'  # Test to reproduce
FAULT = 'fault'   # Failure involved, e.g, slow disk, node crash
SPEC = 'spec'   # Checks that can catch the bug.
FIX = 'fix'   # Potential fixes
CAT = 'cat'  # Category of bug
IMPACT = 'impact'
TAX = 'tax'  # HG's taxonomy
JIRA_LINK='https://issues.apache.org/jira/browse/{id}'
SAME_SHADE_ROWS = 3  # We will alternate shading after a number of rows.

# Function - TAGFILTERS selection
# Todo : grab all kinds of tags from system raw txt and store it inside
#        TAGFILTERS
def parseTagFilters():
  for s in SYSTEMS:
    filename = '../raw-public/%s.txt' % s.lower()
    if not os.path.exists(filename):
      print '%s does not exist' % filename
      sys.exit(-1)
    rawfile = open(filename, 'r')
    # Start Parsing
    for rawline in rawfile:
      line = rawline.rstrip()
      if(not line.startswith('[')) and (len(line) > 1) and (not line.startswith('  ')) and (not line.startswith('>')) and (not line in TAGFILTERS) and (not ' ' in line):
        TAGFILTERS.append(line)

# Function - Parameter Selection
# Todo : discern which parameter is system parameter and which one is
#        tag filters parameter
def parameterSelection():
  Unknowntag = []
  check = {}
  check['systems'] = list()
  check['tagfilters'] = list()
  check['sorter'] = list()
  if len(sys.argv) == 1:
    help()
  if len(sys.argv) > 1:
    for s in sys.argv:
      if s != './top-k.py':
          valid = False
          if s.upper() in SYSTEMS:
            check['systems'].append(s.upper())
            valid = True
          elif s.lower() in SYSTEMS.values():
            check['systems'].append(get_key_from_value(SYSTEMS, s.lower()))
            valid = True
          elif s.lower() in OPTIONS:
            check['sorter'].append(s.lower())
            valid = True
          for availableTag in TAGFILTERS:
              availableTagComp = availableTag.split('-')
              checkTagComp = s.split('-')
              matchTag = True
              for i in range(len(checkTagComp)):
                if checkTagComp[i] != availableTagComp[i]:
                  matchTag = False
                  break
              if matchTag:
                valid = True
                check['tagfilters'].append(s)
              if valid:
                break
          if s.upper() not in SYSTEMS and s not in TAGFILTERS and s not in OPTIONS:
            Unknowntag.append(s)

  if len(Unknowntag) > 0:
    print 'Error: Invalid parameter '+', '.join(Unknowntag) +  '. Please look at valid-tags.txt to find the valid tag(s) that available beeing parameter(s)'
    sys.exit(-1)  
  if len(check['sorter']) > 1 or len(check['sorter']) == 0:
    print 'Error: Parameter must have one order of: %s' % str(OPTIONS).lower()
    sys.exit(-1)    
  if len(check['systems']) == 0:
    check['systems'] = SYSTEMS.keys()
  if len(check['tagfilters']) == 0 and len(check['systems']) == 0:
    check['systems'] = SYSTEMS.keys()
    # print 'Error: Parameter must have atleast one tag of: %s' % str(TAGFILTERS).lower()
    # sys.exit(-1)

  return check


#--------------------------------------
#--------- Issue Data structure -------
#--------------------------------------
class Issue(object):
    """A class that represent each bug."""
    def __init__(self, idstr, title):
        self.idstr = idstr
        self.title = title
        i = self.idstr.find('-')
        self.sys = self.idstr[:i]
        self.num = int(self.idstr[i+1:])
        self.reviewers = []
        self.types = []
        self.priority = 99
        # Notes
        self.notes = {}  # mapping from description
        self.notes[DESC] = ''
        self.notes[COMP] = ''
        self.notes[TEST] = ''
        self.notes[FAULT] = ''
        self.notes[SPEC] = ''
        self.notes[FIX] = ''
        self.notes[CAT] = ''
        self.notes[IMPACT] = ''
        self.notes[TAX] = ''
        self.studentnotes = ''
        self.hgnotes = ''
        # tempory variable, for parsing purpose.
        self._tmp = ''
        self.ttr = ''
        self.comm = ''

    def isRelevant(self):
        """Return True if this bug is tagged."""
        return len(self.reviewers) > 0
      
    def toString(self):
        """For debugging purpose only."""
        s = ''
        s += '[%s][%s]\n' % (self.idstr, self.title)
        s += 'Reviewers: %s\n' % str(self.reviewers)
        s += 'Types: %s\n' % str(self.types)
        s += 'Priority: %d\n' % self.priority
        s += 'Desc: %s\n' % self.notes[DESC]
        s += 'Comp: %s\n' % self.notes[COMP]
        s += 'Test: %s\n' % self.notes[TEST]
        s += 'Fault: %s\n' % self.notes[FAULT]
        s += 'Spec: %s\n' % self.notes[SPEC]
        s += 'Fix: %s\n' % self.notes[FIX]
        s += 'Cat: %s\n' % self.notes[CAT]
        s += 'Impact: %s\n' % self.notes[IMPACT]
        s += 'Students: %s\n' % self.studentnotes
        s += 'HG: %s\n' % self.hgnotes
        return s

    def parseTags(self, line, parser):
        # Who, types, and pipeline aspect.
        m = parser.pw.match(line)
        if m:
            tag = m.group(1)
            temp = tag.split('-')
            whoTag = ''
            try:
              whoTag = temp[1]
            except:
              pass
            if whoTag in WHO and not whoTag in self.reviewers:
              self.reviewers.append(whoTag)
            else:
              self.types.append(tag)
        # Priority.
        m = parser.pd.match(line)
        if m:
            tag = m.group(0)
            temp = tag.split('-')
            if temp[0] != 'x' and temp[0] != 's':
              self.priority = int(m.group(1))
            # So lowest priority is 1 according to the script.
            if self.priority == 0:
                self.priority = 1
        if line.find('j-ttr-')==0:
            self.ttr = line.strip()
        if line.find('j-comm-')==0:
            self.comm = line.strip()

    def parseNotes(self, line):
        if line.startswith(' ' * 4):
            self._tmp += line
        if len(line.strip()) == 0:
            self.processNotes(self._tmp)
            self._tmp = ''

    def processNotes(self, note):
        if note == '':
            return
        if note.startswith(' ' * 6):
            note = note.lstrip()
            i = note.find(':')
            prefix = note[:i].lower()
            content = note[i+1:]
            if prefix in self.notes:
                self.notes[prefix] += content
            else:
                self.hgnotes += '<p> %s' % note
        elif note.startswith(' ' * 4):
            note = note.lstrip()
            i = note.find(':')
            prefix = note[:i].lower()
            content = note[i+1:]
            if prefix in self.notes:
                self.notes[prefix] += content
            else:
                self.studentnotes += '<p> %s' % note

    def getWhoSortKey(self):
        if 'hg' in self.reviewers:
            who = '1hg'
        elif 'sl' in self.reviewers:
            who = '2sl'
        else:
            who = '3students'
        return who

    def _getImage(self, check):
        if check:
            return '<img width=15 height=15 src="check.gif">'
        return '<img width=15 height=15 src="cross.gif">'

    def getSortKey(self):
        """Sort key to show in html files.
        People should write different getSortKey method if needed be.
        """
        return '<b>%02d-%s-%s</b><br><br>%05d' \
            % (self.priority, self.getWhoSortKey(), SYSTEMS[self.sys],
               self.num)

    def getPrintSortKey(self, counter):
        """Sort key to show in html files.
        People should write different getSortKey method if needed be.
        """
        link = JIRA_LINK.format(id=self.idstr)
        sysnum = '%s-%d' % (SYSTEMS[self.sys], self.num)
        title = '<a href=\"%s\" target="_blank"><font size=+1><b>%s</b></font>:'
        title += ' %s (%d)</a>'
        title = title % (link, sysnum, self.title, counter)
        discuss = ', '.join(self.reviewers)
            
        # return '%s<br><br>Sort Key: %02d-%s-%s<br><i>Discussed by: %s</i>' \
        #     % (title, self.priority, self.getWhoSortKey(), SYSTEMS[self.sys], discuss)

        return '%s<br><br> <br><i> </i>' \
            % (title)


#--------------------------------------
#--------- Parse logic ----------------
#--------------------------------------
class Parser(object):
    """A class for parsing. It has info about project tag,
    and list of systems. This should be independent of how
    we print the table."""

    def __init__ (self, systems, tagfilter):
        """Constructor.

        Params:
        - systems: list of String, e.g, ['mapreduce', 'hdfs']
        - tagfilter: list of string, e.g, ['dc-d','sw-eh']
        """
        self.systems = systems
        self.tagfilter = tagfilter
        
        # A bunch of regex
        self.pt = re.compile('\[(.+)\]\[(.+)\]') # For title and description
        self.pw = re.compile('([a-zA-Z\-\d]+)') # For who and types.
        self.pd = re.compile('[a-zA-Z]+-(\d+)') # For priority.
        

    def parseSystem(self, system):
        """This function contains the parsing logic.

        Params:
        - system: String lower case, system name, e.g. 'mapreduce'.

        Return: a dict mapping issue->issue.sortedkey.
        """
        print 'Parsing %s' % system
        filename = '../raw-public/%s.txt' % system
        if not os.path.exists(filename):
            print '%s does not exist' % filename
            sys.exit(-1)
        rawfile = open(filename, 'r')
        issues = {}
        cur = None
        # Start parsing.
        for line in rawfile:
            m = self.pt.match(line)
            if m:
                # Reach new issue, store last issue.
                if cur != None and self.passFilter(cur):
                  issues[cur] = cur.getSortKey()
                idstr = m.group(1)
                title = m.group(2)
                try:
                    cur = Issue(idstr, title)
                    cur.idstr
                except:
                    print 'Warning: bad form'
                    print line
                    # reset parsing
                    cur = None
            if cur != None:
                cur.parseTags(line, self)
                cur.parseNotes(line)
        # Outside for loop. Remember the last issue.
        if self.passFilter(cur):
            issues[cur] = cur.getSortKey()
        return issues

    def passFilter(self, issue):
        """Check issue types and compare it with tagfilter
        Return: bool True or False, whether issue pass all the filters or not
        """
        listedTags = 0
        for tag in self.tagfilter:
          for typ in issue.types:
            if typ.startswith(tag):
              listedTags += 1
              break

        if listedTags == len(self.tagfilter):
          return True
        else:
          return False
    
    def parse(self):
        """Parse all systems.
        Return: a dict mapping issue->issue.sortedkey.
        """
        issues = {}
        for system in self.systems:
            issues.update(self.parseSystem(system))
        return issues


#--------------------------------------
#--------- Create html file -----------
#--------------------------------------
class Printer(object):
    """Printing HTML utils. The logic to different table styles
    should be here. For instance, if people want new table format,
    they will add new methods here to write different format.
    """

    def __init__(self):
        """Constructor.

        """

        os.system('cp html-files/* /tmp/')

    def printHtml(self, issues, options):
        """Generate /tmp/output.html.

        Params:
        - issues: a map (not sorted) from issue->issue.sortkey"""
        out = open('/tmp/output.html', 'w')
        self.printHeader(out)
        self.printTableHeader(out)
        self.printTableBody(out, issues, options)
        self.printFooter(out)
        out.close()

    def printHeader(self, out):
        header = '<html>\n'
        header += ' <head>\n'
        header += '  <meta>\n'
        header += '  <link rel=StyleSheet href=coffee.css type=text/css>\n'
        header += ' </head>\n'
        header += ' <body style="margin:0px">\n'
        header += ' <table>\n'
        out.write(header)

    def printFooter(self, out):
        out.write('  </table>\n')
        out.write(' </body>\n')
        out.write('</html>\n')

    def pRowStart(self, out, i=0):
        if i == 0:
            out.write('    <tr>\n')
            return
        t = i % (2 * SAME_SHADE_ROWS)
        if t >=1 and t <= SAME_SHADE_ROWS:
            out.write('    <tr class=noshade>\n')
        else:
            out.write('    <tr class=shade>\n')

    def pRowEnd(self, out):
        out.write('    </tr>\n')

    def pCol(self, out, col):
        out.write('     <td>%s</td>\n' % col)

    def printColWidth(self, out):
        out.write('<colgroup>\n')
        out.write('<col span="1" style="width: 50%;">')  # Key & Title
        #out.write('<col span="1" style="width: 10%;">')  # Title
        out.write('<col span="1" style="width: 30%;">')  # Desc
        out.write('<col span="1" style="width: 20%;">')  # Moreinfo
        out.write('</colgroup>\n')

    def printTableHeader(self, out):
        self.printColWidth(out)
        out.write('    <thead>\n');
        self.pRowStart(out);
        self.pCol(out, 'Title')
        self.pCol(out, 'More Info')
        self.pCol(out, 'Comment')
        self.pRowEnd(out);
        out.write('    </thead>\n');

    def printTableBody(self, out, issues, options):
        """Notes: for new table with different column,
        please create new method.


        Params:
        - issues: a map (not sorted) from issue->issue.sortkey"""
        """
        newest
        oldest
        ttr 
        comm
        """
        rev= True
        meta = sorted(issues.items(), key=lambda x: x[1], reverse=rev)
        for opt in options:
            if opt == 'byoldest':
                rev = False
                print "oldest"
                meta = sorted(issues.items(), key=lambda x: x[1], reverse=rev)
            elif opt == 'bynewest':
                meta = sorted(issues.items(), key=lambda x: x[1], reverse=rev)
            elif opt == 'byttr':
                meta = sorted(issues.items(), key=lambda x: int(x[0].ttr.split('-')[2]) if any(x[0].ttr) else 0, reverse=rev)
            elif opt == 'bycomm':
                meta = sorted(issues.items(), key=lambda x: int(x[0].comm.split('-')[2]) if any(x[0].comm) else 0, reverse=rev)

        out.write('   <tbody>\n')
        i = 1

        for issue, sortkey in meta:
            # TODO: may be combine all of this to
            # issue.getPrintentry? 
            if not issue.ttr and 'byttr' in options:
                continue 
            if not issue.comm and 'bycomm' in options:
                continue 
            self.pRowStart(out, i)
            self.pCol(out, issue.getPrintSortKey(i))
            desc = issue.notes[DESC]
            if len(issue.studentnotes) > 0:
                desc += '<p><b>Students:</b> %s' % issue.studentnotes
            # self.pCol(out, desc)
            more = ''
            if len(issue.types) > 0:
                # print issue.types[len(issue.types) -1].split('-')[2]
                more = '<p><b>Tags:</b> %s' % ', '.join(issue.types)
            if len(issue.notes[COMP]) > 0:
                more += '<p><b>Comp:</b> %s' % issue.notes[COMP]
            if len(issue.notes[IMPACT]) > 0:
                more += '<p><b>Impact:</b> %s' % issue.notes[IMPACT]
            if len(issue.notes[TEST]) > 0:
                more += '<p><b>Test:</b> %s' % issue.notes[TEST]
            if len(issue.notes[FAULT]) > 0:
                more += '<p><b>Fault:</b> %s' % issue.notes[FAULT]
            if len(issue.notes[SPEC]) > 0:
                more += '<p><b>Spec:</b> %s' % issue.notes[SPEC]
            if len(issue.notes[FIX]) > 0:
                more += '<p><b>Fix:</b> %s' % issue.notes[FIX]
            if len(issue.notes[CAT]) > 0:
                more += '<p><b>Cat:</b> %s' % issue.notes[CAT]
            self.pCol(out, more)
            hg = issue.hgnotes
            if len(issue.notes[TAX]) > 0:
                hg += '<p><b>Tax:</b> %s' % issue.notes[TAX]
            self.pCol(out, hg)
            i += 1
            self.pRowEnd(out)
            if i > 100:
                break
        out.write('   </tbody>\n')

def help():
    print ""
    print "---------------------------help-----------------------------------"
    print ""
    print "usage:"
    print "   ./top-k.py [system name|tags][sortkey]"
    print ""
    print "Available options:                                                  "
    print "   The parameter should consist of one sortkey                                         "
    print "       Example : ./top-k.py mapreduce byoldest                    "
    print ""
    print "valid system(s) : cassandra, flume, hbase, hdfs, mapreduce, zookeeper"
    print "valid tag(s)    : see the available tags on valid-tags.txt   "
    print "valid sortkey   : bynewest, byoldest, byttr, and bycomm"    
    print "------------------------------------------------------------------"
    print "Only show top 100 issues"
    
    sys.exit(-1)    

# main class
def main():
  parseTagFilters()
  check = parameterSelection()
  CHECKSYSTEMS = check['systems']
  CHECKTAGFILTERS = check['tagfilters']
  CHECKOPTIONS = check['sorter']
  print 'System(s) that will be checked: ' + str(CHECKSYSTEMS)
  print 'Filter Tag(s): ' + str(CHECKTAGFILTERS)
  print 'sortkey(s): ' + str(CHECKOPTIONS)
  parser = Parser([s.lower() for s in CHECKSYSTEMS], CHECKTAGFILTERS)
  issues = parser.parse()
  printer = Printer()
  printer.printHtml(issues, CHECKOPTIONS)
  
  print "Open in the browser.."
  subprocess.call("./openBrowser.sh", shell =True)
  print "Done"

if __name__ == '__main__':
    main()
