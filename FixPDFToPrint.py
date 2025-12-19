import subprocess
import sys
import os
from PyPDF2 import PdfReader, PdfWriter

def remove_pages(input_path, temp_path, remove_first=False, remove_last=False):
    """
    Remove first and/or last pages from PDF
    """
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        total_pages = len(reader.pages)
        print(f"Original PDF has {total_pages} pages")
        
        start_page = 1 if remove_first else 0
        end_page = total_pages - 1 if remove_last else total_pages
        
        if start_page >= end_page:
            print("✗ Error: Would remove all pages!")
            return False
        
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        with open(temp_path, 'wb') as output_file:
            writer.write(output_file)
        
        pages_removed = []
        if remove_first:
            pages_removed.append("first")
        if remove_last:
            pages_removed.append("last")
        
        print(f"Removed {' and '.join(pages_removed)} page(s)")
        print(f"New page count: {end_page - start_page}")
        return True
        
    except Exception as e:
        print(f"✗ Error removing pages: {e}")
        return False

def rebuild_pdf_ghostscript(input_path, output_path):
    """
    Rebuild PDF using Ghostscript - fixes compatibility with print services
    """
    # Use the correct Windows Ghostscript executable
    gs_exe = 'gswin64c.exe'
    
    gs_command = [
        gs_exe,
        '-dNOPAUSE',
        '-dBATCH',
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/prepress',
        '-dEmbedAllFonts=true',
        '-dSubsetFonts=true',
        '-dCompressFonts=true',
        '-dColorConversionStrategy=/LeaveColorUnchanged',
        '-dDownsampleMonoImages=false',
        '-dDownsampleGrayImages=false',
        '-dDownsampleColorImages=false',
        f'-sOutputFile={output_path}',
        input_path
    ]
    
    try:
        print(f"Rebuilding PDF with Ghostscript...")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        
        result = subprocess.run(gs_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                input_size = os.path.getsize(input_path)
                print(f"\n✓ PDF rebuilt successfully!")
                print(f"  Original size: {input_size:,} bytes")
                print(f"  New size: {output_size:,} bytes")
                return True
            else:
                print(f"✗ Output file was not created")
                return False
        else:
            print(f"✗ Ghostscript error:")
            print(result.stderr)
            if result.stdout:
                print(result.stdout)
            return False
            
    except FileNotFoundError:
        print(f"✗ Ghostscript executable not found: {gs_exe}")
        print("Make sure Ghostscript is in your PATH")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    
    input_file = r"E:\code\GIT_pythontoys\FixPDFToPrint\EDETU_Blank.pdf"
    output_file = r"E:\code\GIT_pythontoys\FixPDFToPrint\EverydayHeroes_EnteringTheUnknown_full.pdf"
    
    # OPTIONS: Set these to True to remove pages
    REMOVE_FIRST_PAGE = False
    REMOVE_LAST_PAGE = False
    
    if not os.path.exists(input_file):
        print(f"✗ Input file not found: {input_file}")
        sys.exit(1)
    
    # If we need to remove pages, do that first
    if REMOVE_FIRST_PAGE or REMOVE_LAST_PAGE:
        temp_file = input_file.replace('.pdf', '_temp.pdf')
        print(f"\nStep 1: Removing pages...")
        if not remove_pages(input_file, temp_file, REMOVE_FIRST_PAGE, REMOVE_LAST_PAGE):
            sys.exit(1)
        print()
        
        # Use the temp file as input for Ghostscript
        print(f"Step 2: Rebuilding with Ghostscript...")
        success = rebuild_pdf_ghostscript(temp_file, output_file)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
    else:
        success = rebuild_pdf_ghostscript(input_file, output_file)
    
    sys.exit(0 if success else 1)