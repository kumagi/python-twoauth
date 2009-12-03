import urllib2
import xml.parsers.expat

class twitter_xml:
    def __init__(self, xmlstr):
        self.name = []
        self.data = []
        self.cdata = ""
        self.mode = []
        self.nmode = ""

        self.p = xml.parsers.expat.ParserCreate()
        self.p.StartElementHandler = self.start_element
        self.p.CharacterDataHandler = self.char_data
        self.p.EndElementHandler = self.end_element
        self.p.Parse(xmlstr)

    def start_element(self, name, attrs):
        self.cdata = ""
        self.name.append(name)
        self.mode.append(self.nmode)
        
        if attrs and attrs["type"] and attrs["type"] == "array":
            self.nmode = "array"
        else:
            self.nmode = ""

    def end_element(self, name):
        cdata = self.cdata.strip(" \n")

        mode = self.mode.pop()
        self.nmode = mode

        if cdata:
            self.data.append([name, cdata])
            self.cdata = ""
        elif self.name and name == self.name[-1]:
            self.data.append([name, ""])
        else:
            elements = []
            while self.name.pop() != name:
                elements.append(self.data.pop())

            self.name.append(name)
            if mode:
                self.data.append(dict(elements))
            else:
                if isinstance(elements[0], dict):
                    self.data.append([name, elements])
                else:
                    self.data.append([name, dict(elements)])

    def char_data(self, c):
        self.cdata += c

def xmlparse(xml_text):
    parsed = twitter_xml(xml_text)
    parsed.data = parsed.data[0][1]
    
    return parsed.data

if __name__ == '__main__':
    #url = 'http://twitter.com/statuses/public_timeline.xml'
    url = 'http://twitter.com/statuses/user_timeline.xml?screen_name=hktechno'
    xml_tl = urllib2.urlopen(url).read()

    tl = xmlparse(xml_tl)

    for post in tl:
        print "@%s\t%s" % (post["user"]["screen_name"], post["text"])
