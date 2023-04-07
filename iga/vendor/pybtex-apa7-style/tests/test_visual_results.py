from pathlib import Path
from pybtex.plugin import find_plugin
from pybtex.database import parse_file
APA = find_plugin('pybtex.style.formatting', 'apa7')()
HTML = find_plugin('pybtex.backends', 'html')()

def bib_to_html(bibfile):
    bibliography = parse_file(bibfile, 'bibtex')
    formatted_bib = APA.format_bibliography(bibliography)
    return "<br>".join(entry.text.render(HTML) for entry in formatted_bib)

with open("tests/results.html", 'w') as outfile:
    outfile.write("""
    <style>
    td {border: 1px solid black; width: 400px;} .raw {width: 600px;} pre {width: 600px; overflow: scroll;}
    </style>
    """)
    outfile.write("<h1>Test results</h1>")
    for example in Path("tests/examples").iterdir():
        if example.suffix == ".bib":
            outfile.write(f"<h2>{example}</h2><table><tr>")
            outfile.write(f'<td class="raw""><pre>' + example.read_text() + "</pre></td>")
            try:
                html = bib_to_html(example)
                outfile.write("<td>" + html + "</td>")
            except Exception as e:
                outfile.write(f"<td>Error: {e}</td>")
            outfile.write("</tr></table>")
