# APA7 Style for Pybtex

*This is a fork of [naeka's pybtex-apa-style](https://github.com/naeka/pybtex-apa-style), which targeted APA6*.

This plugin provides [APA7](https://apastyle.apa.org/) style for Pybtex.

[Pybtex](https://pybtex.org/) provides Python support for interacting with bibTeX
bibliography data. Style plugins provide support for formatting bibliographies,
similar to the role that `csl` files play for LaTeX.

## Installation

```shell
$ pip install pybtex pybtex-apa7-style
```

## Usage

Pybtex uses [Python's plugin system](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/).
To use APA7, load it as a plugin as shown in the example below.

```python3
from pybtex.plugin import find_plugin
from pybtex.database import parse_file
APA = find_plugin('pybtex.style.formatting', 'apa7')()
HTML = find_plugin('pybtex.backends', 'html')()

def bib_to_apa7_html(bibfile):
    bibliography = parse_file(bibfile, 'bibtex')
    formatted_bib = APA.format_bibliography(bibliography)
    return "<br>".join(entry.text.render(HTML) for entry in formatted_bib)
```

## Contributing

This is a work in progres; APA style is not fully-specified and has endless edge cases. 
I would be delighted to receive examples of bibTeX entries which are not formatted correctly
in APA. 

If you clone [this project's repository](https://github.com/cproctor/pybtex-apa7-style), you
can add bibTeX exemplars in `tests/examples` and then run `python tests/test_visual_results.py`.
Open `tests/results.html` to see the resulting APA-formatted HTML.
