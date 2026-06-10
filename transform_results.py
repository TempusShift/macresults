#!/usr/bin/env python3
"""
Transform event results HTML files to simplified format.
Keeps only the Overall results table, removes buttons/controls, and sorts drivers alphabetically.

Usage: python transform_results.py input.html output.html
"""

import sys
import re
from html.parser import HTMLParser
from io import StringIO


class ResultsHTMLParser(HTMLParser):
    """Parse and extract components from event results HTML."""
    
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.in_body = False
        self.in_overall_table = False
        self.in_tbody = False
        self.current_row = []
        self.current_cell = StringIO()
        self.rows = []
        self.head_content = StringIO()
        self.style_content = StringIO()
        self.metadata = {}
        self.in_style = False
        self.depth = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'head':
            self.in_head = True
        elif tag == 'body':
            self.in_body = True
        elif tag == 'style':
            self.in_style = True
        elif tag == 'table' and self.in_body:
            table_id = attrs_dict.get('id', '')
            if table_id == 'result-overall':
                self.in_overall_table = True
                self.depth = 1
            elif table_id in ['result-class', 'result-pax']:
                # Skip other tables
                pass
        elif self.in_overall_table:
            if tag == 'tbody':
                self.in_tbody = True
            elif tag == 'tr' and self.in_tbody:
                self.current_row = []
            elif tag == 'td':
                self.current_cell = StringIO()
        elif self.in_body and tag == 'div' and 'float' in attrs_dict.get('style', ''):
            # Extract metadata from float div
            pass
        elif self.in_head:
            if tag == 'title':
                self.current_cell = StringIO()
    
    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False
        elif tag == 'body':
            self.in_body = False
        elif tag == 'style':
            self.in_style = False
        elif tag == 'table' and self.in_overall_table:
            self.in_overall_table = False
        elif self.in_overall_table:
            if tag == 'tbody':
                self.in_tbody = False
            elif tag == 'tr' and self.in_tbody and self.current_row:
                # Skip header rows and dividers
                if len(self.current_row) > 0 and self.current_row[0].strip():
                    self.rows.append(self.current_row)
                self.current_row = []
            elif tag == 'td':
                cell_content = self.current_cell.getvalue().strip()
                self.current_row.append(cell_content)
                self.current_cell = StringIO()
    
    def handle_data(self, data):
        if self.in_style:
            self.style_content.write(data)
        elif self.in_overall_table and self.current_row is not None:
            self.current_cell.write(data)
        elif self.in_head and tag == 'title':
            self.current_cell.write(data)


def transform_html(input_file, output_file):
    """Transform results HTML file."""
    
    # Read input
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse to extract overall table
    from html.parser import HTMLParser
    
    class OverallTableExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_overall = False
            self.table_depth = 0
            self.table_html = StringIO()
            self.title = ""
            self.metadata = {}
            self.in_title = False
            self.header_extracted = False
            
        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            
            if tag == 'title':
                self.in_title = True
            elif tag == 'table' and attrs_dict.get('id') == 'result-overall':
                self.in_overall = True
                self.table_depth = 1
                self.table_html.write(self.get_starttag_text())
            elif self.in_overall:
                self.table_html.write(self.get_starttag_text())
                if tag == 'table':
                    self.table_depth += 1
                elif tag == 'thead':
                    self.header_extracted = False
            elif tag == 'div' and not self.in_overall:
                # Try to get metadata
                style = attrs_dict.get('style', '')
                if 'float: right' in style:
                    pass
            elif tag == 'h2':
                pass
            elif tag == 'h4':
                pass
            
        def handle_endtag(self, tag):
            if self.in_overall:
                self.table_html.write(f'</{tag}>')
                if tag == 'table':
                    self.table_depth -= 1
                    if self.table_depth == 0:
                        self.in_overall = False
            elif tag == 'title':
                self.in_title = False
        
        def handle_data(self, data):
            if self.in_title:
                self.title += data
            elif self.in_overall:
                self.table_html.write(data)
    
    # Extract table using regex for simplicity
    # Find the result-overall table
    match = re.search(r'<table id="result-overall".*?</table>', content, re.DOTALL)
    if not match:
        print("Error: Could not find result-overall table")
        sys.exit(1)
    
    table_html = match.group(0)
    
    # Extract rows from tbody
    tbody_match = re.search(r'<tbody>(.*?)</tbody>', table_html, re.DOTALL)
    if not tbody_match:
        print("Error: Could not find tbody")
        sys.exit(1)
    
    tbody_content = tbody_match.group(1)
    
    # Extract individual rows
    row_pattern = r'<tr class="row">(.*?)</tr>'
    rows = []
    
    def remove_columns_from_row(row_html, cols_to_remove):
        """Remove specific columns from a row."""
        # Extract all TDs with their full tags
        td_pattern = r'<td[^>]*>.*?</td>'
        tds = list(re.finditer(td_pattern, row_html, re.DOTALL))
        
        if not tds:
            return row_html
        
        # Build new row by keeping only non-removed columns
        new_row = '<tr class="row">\n'
        for i, td_match in enumerate(tds):
            if i not in cols_to_remove:
                new_row += '          ' + td_match.group(0) + '\n'
        new_row += '        </tr>'
        return new_row
    
    # Columns to remove: 0=Rank, 1=Class, 5=Diff., 6=Diff. Prev.
    cols_to_remove = {0, 1, 5, 6}
    
    for row_match in re.finditer(row_pattern, tbody_content, re.DOTALL):
        row_html = row_match.group(0)
        # Extract all TDs to find driver name (column 2 before removal)
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        if len(tds) >= 3:
            # Driver name is in 3rd column (index 2, after Rank and Class)
            driver_name = tds[2].strip()
            # Clean up HTML tags for sorting
            driver_clean = re.sub(r'<[^>]+>', '', driver_name).strip()
            # Remove unwanted columns
            filtered_row = remove_columns_from_row(row_html, cols_to_remove)
            rows.append((driver_clean, filtered_row))
    
    # Sort rows alphabetically by driver name
    rows.sort(key=lambda x: x[0].lower())
    
    # Reconstruct tbody with sorted rows
    new_tbody = '<tbody>\n'
    for _, row_html in rows:
        new_tbody += row_html + '\n'
    new_tbody += '</tbody>'
    
    # Replace tbody in table_html
    new_table_html = re.sub(r'<tbody>.*?</tbody>', new_tbody, table_html, flags=re.DOTALL)
    
    # Remove display: none style since we're making this the only visible table
    new_table_html = re.sub(r'\s*style="display: none"', '', new_table_html)
    
    # Remove header columns: Rank, Class, Diff., Diff. Prev.
    # Replace the header row with columns removed
    def remove_columns_from_header(table_html, cols_to_remove):
        """Remove specific columns from table header."""
        # Find the header row with column names
        header_match = re.search(r'<tr>\s*<th>Rank</th>.*?</tr>', table_html, re.DOTALL)
        if not header_match:
            return table_html
        
        old_header = header_match.group(0)
        # Extract all TH elements
        ths = list(re.finditer(r'<th[^>]*>[^<]*</th>', old_header))
        
        # Build new header with only kept columns
        new_header = '<tr>\n'
        for i, th_match in enumerate(ths):
            if i not in cols_to_remove:
                new_header += '          ' + th_match.group(0) + '\n'
        new_header += '        </tr>'
        
        return table_html.replace(old_header, new_header)
    
    new_table_html = remove_columns_from_header(new_table_html, cols_to_remove)
    
    # Extract head
    head_match = re.search(r'<head>(.*?)</head>', content, re.DOTALL)
    head_content = head_match.group(1) if head_match else ""
    
    # Extract metadata from body
    title_match = re.search(r'<h2[^>]*>([^<]+)</h2>', content)
    title = title_match.group(1).strip() if title_match else "Event Results"
    
    date_match = re.search(r'<h4[^>]*>([^<]+)</h4>', content)
    date = date_match.group(1).strip() if date_match else ""
    
    participants_match = re.search(r'Participants: (\d+)', content)
    participants = participants_match.group(1) if participants_match else "0"
    
    runs_match = re.search(r'Runs: (\d+)', content)
    runs = runs_match.group(1) if runs_match else "0"
    
    # Build output HTML
    output_html = f"""<html>
  <head>
{head_content}
  </head>
  <body>
    <div style="float: right">Participants: {participants}<br />Runs: {runs}</div>
    <h1>Minnesota Autosports Club</h1>
    <h2 style="margin-bottom: 4px">{title}</h2>
    <h4 style="margin-top: 0px">{date}</h4>
    <div class="clearfix"></div>
    {new_table_html}
    <div>Created by <a href="http://www.axti.me">AXti.me</a></div>
  </body>
</html>"""
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_html)
    
    print(f"✓ Transformed {input_file} → {output_file}")
    print(f"  Drivers: {len(rows)}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python transform_results.py input.html output.html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    transform_html(input_file, output_file)
