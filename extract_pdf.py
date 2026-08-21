"""Extract text from PDF using ToUnicode CMap decoding."""
import re
import zlib

def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as f:
        data = f.read()

    # Find all stream objects
    streams = re.findall(rb'stream\r?\n(.+?)\r?\nendstream', data, re.DOTALL)
    
    # Find ToUnicode CMap streams to build glyph->unicode mapping
    cmap = {}
    for stream in streams:
        try:
            if stream[:2] == b'\x78\x9c':
                decoded = zlib.decompress(stream).decode('utf-8', errors='ignore')
            else:
                decoded = stream.decode('utf-8', errors='ignore')
        except:
            continue
        
        # Parse beginbfchar sections
        bfchar_matches = re.findall(r'beginbfchar\s*(.*?)\s*endbfchar', decoded, re.DOTALL)
        for block in bfchar_matches:
            pairs = re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', block)
            for src, dst in pairs:
                cmap[src.upper()] = chr(int(dst, 16))
        
        # Parse beginbfrange sections
        bfrange_matches = re.findall(r'beginbfrange\s*(.*?)\s*endbfrange', decoded, re.DOTALL)
        for block in bfrange_matches:
            ranges = re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', block)
            for start, end, dst_start in ranges:
                s = int(start, 16)
                e = int(end, 16)
                d = int(dst_start, 16)
                for i in range(e - s + 1):
                    cmap[format(s + i, '04X')] = chr(d + i)
    
    # Now decode the content streams using the CMap
    full_text = []
    for stream in streams:
        try:
            if stream[:2] == b'\x78\x9c':
                decoded = zlib.decompress(stream).decode('utf-8', errors='ignore')
            else:
                decoded = stream.decode('utf-8', errors='ignore')
        except:
            continue
        
        if 'Tf' not in decoded:
            continue
        
        # Extract text shown with Tj and TJ operators
        # Match <XXXX> Tj patterns
        tj_matches = re.findall(r'<([0-9A-Fa-f]+)>\s*Tj', decoded)
        for code in tj_matches:
            code_upper = code.upper()
            if code_upper in cmap:
                full_text.append(cmap[code_upper])
            elif len(code) == 4:
                try:
                    full_text.append(chr(int(code, 16)))
                except:
                    pass
        
        # Also look for Td (text positioning) to detect line breaks
        td_matches = re.finditer(r'(\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+Td', decoded)
        
    return ''.join(full_text)


if __name__ == '__main__':
    text = extract_pdf_text(r'd:\careerOS\PS Automate India Hack.pdf')
    with open(r'd:\careerOS\pdf_text.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Extracted to pdf_text.txt, length:", len(text))
