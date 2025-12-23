import sys
from PyPDF2 import PdfReader, PdfWriter

def CombinePages(file_paths):
    try:
        writer = PdfWriter()
        
        for file_path in file_paths:
            # Read each PDF file
            reader = PdfReader(file_path)
            # Add all pages from this PDF to the writer
            for page in reader.pages:
                writer.add_page(page)
        
        return writer

    except Exception as e:
        print(f"✗ Error adding pages: {e}")
        return None

if __name__ == "__main__":
    
    input_folder = "E:/code/GIT_pythontoys/PDF-shit/"
    input_files = ["only1.pdf", "only2.pdf", "only3.pdf"]
    output_file = input_folder + "output.pdf"

    # Build full file paths
    file_paths = [input_folder + input_file for input_file in input_files]
    
    # Combine the PDFs
    combined_writer = CombinePages(file_paths)
    
    if combined_writer:
        # Write the combined PDF to the output file
        with open(output_file, 'wb') as output:
            combined_writer.write(output)
        print(f"✓ Successfully combined {len(input_files)} PDFs into {output_file}")
        success = True
    else:
        print("✗ Failed to combine PDFs")
        success = False

    sys.exit(0 if success else 1)