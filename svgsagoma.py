#!/usr/bin/env python3

import subprocess

default_placeholder = "txt%s"
placeholder_format = "{%s}"

class FileReader():    

    def __init__(self, f, separator=';', first_line_headers=False):

        self.field_names = list()
        self.records = list()
        self.current_record = None
        
        with open(f) as infile:
            if first_line_headers:
                line = infile.readline()
                self.field_names = line.rstrip().split(separator)
            for line in infile:
                fields = line.rstrip().split(separator)
                self.records.append(fields)
                for n in range(len(self.field_names)+1, len(fields)+1):
                    self.field_names.append(default_placeholder % n)

    def pop(self, field_name):
        if not self.current_record:
            self.current_record = dict(zip(self.field_names, self.records.pop(0)))
        return self.current_record.pop(field_name)

    def is_empty(self):
        return not self.records and not self.current_record


class Sagoma():

    def _findall(self, txt, subtxt):
        """Yield each starting and ending position of
        a substring in a given string as a tuple"""
        pos = txt.find(subtxt)
        while pos != -1:
            yield (pos, pos+len(subtxt))
            pos = txt.find(subtxt, pos+1)

    def __init__(self, filename, field_names):
        
        with open(filename) as infile:
            self.txt = infile.read()

        self.slices = list()
        for field in field_names:
            placeholder = placeholder_format % field
            
            pos_tuples = list(self._findall(self.txt, placeholder))
            # positions of each occourrence of the placeholder,
            # e.g.:
            # [(0, 5), (100, 105), (200, 205)]
            
            self.slices += [(field, p) for p in pos_tuples]
            # exploded list of positions for every placeholder,
            # e.g.:
            # [ ('txt1', (0, 5)),
            #   ('txt1', (100, 5)),
            #   ('txt1', (200, 5)),
            #   ('txt2', (50, 55)),
            #   ...
            # ]

        self.slices.sort(key=lambda t: t[1][0])
        # sorted in order of appareance in the file

    def fill(self, f):
        i = 0
        for (placeholder, pos) in self.slices:
            yield self.txt[i:pos[0]]
            try:
                yield f(placeholder)
            except IndexError:
                # no records
                yield ""
            i = pos[1]
        yield self.txt[i:]

def main():
    f = FileReader("testo.txt")
    s = Sagoma("prova.svg", f.field_names)
    tempfile = "_temp.svg"

    i = 1
    
    while not f.is_empty():

        with open(tempfile, "w") as temp:
            for txt in s.fill(f.pop):
                temp.write(txt)
                
        subprocess.check_output([
            "inkscape",
            "-z",
            tempfile,
            "-d",
            "300",
            "-A",
            "out{}.pdf".format(str(i).zfill(3))
        ])

        i+=1 
            
