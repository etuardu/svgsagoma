#!/usr/bin/env python3

import tempfile
import subprocess

class TxtFields():
    
                
    def _records_gen(self):
        """Yield a dictionary {<field>: <value>, ...} for each line in the file"""
        with open(self.filename) as infile:
            if self.first_line_header:
                infile.next()
            for line in infile:
                field_values = line.rstrip().split(self.separator)
                yield dict(zip(self.field_names, field_values))


    def consumed(self):
        """True if EOF, False otherwise"""
        if self.current_record:
            return False
        else:
            try:
                self.current_record = next(self.records)
            except StopIteration:
                return True
        return False

    
    def pop(self, key):
        """Pop the current value for the field <key>"""
        try:
            if not self.current_record:
                self.current_record = next(self.records)
        except StopIteration:
            return ""
        return self.current_record.pop(key)
    
    
    def __init__(self, filename, separator=';', first_line_header=False):
        
        self.filename = filename
        self.separator = separator
        self.first_line_header= first_line_header
        
        with open(filename) as infile:
            fields = infile.readline().rstrip().split(separator)
            
        if first_line_header:
            self.field_names = fields
        else:
            self.field_names = [ "txt%s" % (n+1) for n in range(len(fields)) ]

        self.records = self._records_gen()
        self.current_record = None


class MyTemplate():

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
            placeholder = '{%s}' % field
            
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


    def next_slice(self):
        i = None
        for (placeholder, pos) in self.slices:
            yield (i, pos[0])
            yield placeholder
            i = pos[1]
        yield (i, None)

    def fill(self, fields):
        for t in self.next_slice():
            if type(t) is tuple:
                yield self.txt[t[0]:t[1]]
            else:
                yield fields.pop(t)



csv = TxtFields("testo.txt")
sagoma = MyTemplate("prova.svg", csv.field_names)
tempfile = "_temp.svg"

i=1
while not csv.consumed():
    
    with open(tempfile, "w") as temp:
    
        for txt in sagoma.fill(csv):
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
    




