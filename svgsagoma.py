#!/usr/bin/env python3

import subprocess
import argparse
import os
import tempfile
import sys

default_placeholder = "txt%s"
placeholder_format = "{%s}"

sed_presets = {
    "#id_display": r's/id=".*_disp:\(.*\)"/& style="display:{\1}"/g',
    "#onload_display": r's/onload="disp:\(.*\)"/style="display:{\1}"/g'
}

class SvgsagomaMissingPlaceholders(Exception):
    pass

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
        try:
            return self.current_record.pop(field_name)
        except KeyError:
            # unconsumed records
            raise SvgsagomaMissingPlaceholders(
                "Missing placeholder for record(s): {}".format(
                    ", ".join(self.current_record.keys())
                )
            )

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

    def __init__(self, in_file, field_names):
        
        if hasattr(in_file, 'read'):
            # file-like object
            self.txt = in_file.read().decode('utf-8')
            in_file.close()
        else:
            # filename
            with open(in_file) as fp:
                self.txt = fp.read()

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

        if len(self.slices) == 0:
            raise SvgsagomaMissingPlaceholders(
                "No placeholder(s) found. Expected: {}".format(
                    ", ".join(field_names)
                )
            )

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



def parse_arguments():
    parser = argparse.ArgumentParser(description="Replace values and export images from an svg file")
    parser.add_argument("csv_file", help="input text file in csv format")
    parser.add_argument("svg_file", help="input svg file")
    parser.add_argument("out_prefix", nargs="?", default="out", help="prefix for output file(s) (default: 'out')")
    parser.add_argument("-d", type=int, default=300, help="set dpi quality (default: 300)")
    parser.add_argument("-j", action="store_true", help="join output files as a multipage pdf")
    parser.add_argument("--separator", default=';', help="separator character in the csv file (default: ';')")
    parser.add_argument("--header", action="store_true", help="name the placeholders according to the first line of the csv file (default: 'txt1' ... 'txtN')")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-png", dest='format', action="store_const",
                       const=dict(ext='png', flag='-e'),
                       help="export as png")
    group.add_argument("-pdf", dest='format', action="store_const",
                       const=dict(ext='pdf', flag='-A'),
                       help="export as pdf (default)")
    parser.add_argument("--sed", metavar="CMD|#PRESET", help="preprocess the svg running the provided sed command or preset (#id_display, #onload_display)")

    return(parser.parse_args())


def main():

    args = parse_arguments()

    if args.sed:
        # svg preprocessing
        if args.sed in sed_presets:
            args.sed = sed_presets[args.sed]
        svg_in = tempfile.TemporaryFile()
        subprocess.run(['sed', '--posix', args.sed, args.svg_file], stdout=svg_in)
        svg_in.seek(0)
    else:
        svg_in = args.svg_file

    f = FileReader(
        args.csv_file,
        separator=args.separator,
        first_line_headers=args.header
    )
    try:
        s = Sagoma(svg_in, f.field_names)
    except SvgsagomaMissingPlaceholders as e:
        print("svgsagoma: {}".format(e.args[0]), file=sys.stderr)
        return 1
        
    tmpfile = "_temp.svg"
    out_list = list()

    i = 1
    while not f.is_empty():

        out_file = "{}{}.{}".format(
            args.out_prefix,
            str(i).zfill(3),
            args.format['ext']
        )
        out_list.append(out_file)

        try:
            with open(tmpfile, "w") as temp:
                for txt in s.fill(f.pop):
                    temp.write(txt)
        except SvgsagomaMissingPlaceholders as e:
            print("svgsagoma: {}".format(e.args[0]), file=sys.stderr)
            for f in out_list[:-1]:
                # remove already created output files
                os.remove(f)
            return 2

        subprocess.check_output([
            "inkscape",
            "-z", tmpfile,
            "-d", str(args.d),
            args.format['flag'], out_file
        ])

        i+=1

    os.remove(tmpfile)

    if args.j:
        # join all generated files in a multipage
        # pdf and delete them

        command = {
            'pdf': 'pdfunite',
            'png': 'convert'
        }[args.format['ext']]

        out_file = "{}.pdf".format(
            args.out_prefix,
            args.format['ext']
        )
        
        subprocess.check_output([
            command,
            *out_list,
            out_file
        ])

        for f in out_list:
            os.remove(f)
    
    return 0


if __name__ == '__main__':
    exit(main())


