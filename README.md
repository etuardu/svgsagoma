# svgsagoma
A simple templating engine to substitute placeholders in a svg file with values taken
from a csv file and exporting in various formats.

## Syntax

    usage: svgsagoma.py [-h] [-d D] [-j] [--separator SEPARATOR] [--header]
                        (-png | -pdf)
                        csv_file svg_file [out_prefix]
    
    Replace values and export images from an svg file
    
    positional arguments:
      csv_file              input text file in csv format
      svg_file              input svg file
      out_prefix            prefix for output file(s) (default: 'out')
    
    optional arguments:
      -h, --help            show this help message and exit
      -d D                  set dpi quality (default: 300)
      -j                    join output files as a multipage pdf
      --separator SEPARATOR
                            separator character in the csv file (default: ';')
      --header              name the placeholders according to the first line of
                            the csv file (default: 'txt1' ... 'txtN')
      -png                  export as png
      -pdf                  export as pdf (default)
      --sed CMD|#PRESET     preprocess the svg running the provided sed command or
                            preset (#id_display, #onload_display)

## Examples

* One record per line, one placeholder, export as multiple png images.
![Example 1](doc/example1.png)
> Placeholders always have to be put in **curly brackets**. In this case the placeholder
> reads `{txt1}`, as it is the first (and only) record.

* One record per line, one placeholder, export as one unique pdf.
![Example 2](doc/example2.png)
> The `-j` parameter is used to *join* all resulting images in a unique multipage
> pdf file. You can still use the `-png` switch to rasterize the images before.
> In this example, though, the vector data is preserved by using the `-pdf` switch.

* Multiple records per line, one placeholder per record, export as one unique pdf.
![Example 3](doc/example3.png)
> Same as the example above, but with multiple records. Every page of the resulting pdf
> will represent a recordset.

* Multiple records per line, placeholders for multiple recordsets, export as pdf files,
custom separator
![Example 4](doc/example4.png)
> Each output file will contain data from multiple recordsets. Remaning unconsumed
placeholders, if any, will be left blank (i.e. cleared).
> The `--separator` parameter is used to specify the hash symbol `#` as separator
> instead of `;`.

* Multiple records per line, placeholders for multiple recordsets, export as one unique pdf,
read field names from file
![Example 5](doc/example5.png)
> Same as the example above, but outputs a unique pdf.
> The `--header` parameter is used to read the field names from the first line of the
> csv file and the placeholders in the svg are named accordingly.

## Preprocessing of the svg with `--sed`

The `--sed` argument can be used to perform some adjustments on the svg input.
Under the hood, it will just execute the `sed` command for you, so doing this:

    svgsagoma csv.txt img.svg --sed 's/#ff0000/#ffffff'

will produce the same results as doing this:

    sed 's/#ff0000/#ffffff' img.svg > img_white.svg
    svgsagoma csv.txt img_white.svg

This is mainly useful if you need to put placeholders in part of the svg where they
would break the integrity of the source file.

### Presets

A command starting with `#` is considered to be one of the following presets, which are
included in svgsagoma to integrate some features of wider use.

#### `--sed '#id_display'`

Useful if you need the ability to hide elements depening on csv data.
Adds a placeholder to control the display styling of elements having id
ending with `_disp:<placeholder>`.  
This is a shorthand for `--sed 's/id=".*_disp:\(.*\)"/& style="display:{\1}"/g'`.  
Example:

svg input:

    <text id="text4748_disp:nameDisplay"><tspan>{name}</tspan></text>
    
preprocessed svg:

    <text id="text4748_disp:nameDisplay" style="display{nameDisplay}"><tspan>{name}</tspan></text>

csv input:

    nameDisplay;name
    block;Charles
    none;Mark
    
svg to be exported:

    <text id="text4748_disp:nameDisplay" style="display:block"><tspan>Charles</tspan></text>
    <text id="text4748_disp:nameDisplay" style="display:none"><tspan>Mark</tspan></text>

#### `--sed '#onload_display'`

Same goal of `--sed '#id_display'` but avoids the id pollution.
The display placeholder is added to every element having `disp:<placeholder>` as value
for the `onload` property. The onload property is cleared afterwards.  
This is a shorthand for `--sed 's/onload="disp:\(.*\)"/style="display:{\1}"/g'`.  
Example:

svg input:
    
    <text onload="disp:nameDisplay"><tspan>{name}</tspan></text>
    
preprocessed svg:

    <text style="display:{nameDisplay}"><tspan>{name}</tspan></text>

csv input:

    nameDisplay;name
    block;Charles
    none;Mark

svg to be exported:

    <text style="display:block"><tspan>Charles</tspan></text>
    <text style="display:none"><tspan>Mark</tspan></text>

## Dependencies

*svgsagoma* is written in python and relies on the following dependencies:

* inkscape
* pdfunite
* convert (imagemagick)
* sed (for the `--sed` argument)
