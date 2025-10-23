import PyPDF2
import os
import re

def extract_and_analyze(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        print(f"Total pages: {len(reader.pages)}")
        
        image_counter = 0
        total_image_size = 0
        image_details = []  # Store image info for summary
        
        for page_num, page in enumerate(reader.pages):
            print(f"\n=== Page {page_num + 1} ===")
            
            # Get page dimensions (A4)
            media_box = page['/MediaBox']
            page_width = float(media_box[2])
            page_height = float(media_box[3])
            print(f"Page size: {page_width:.2f} x {page_height:.2f} points (A4 = ~210x297mm)")
            
            # Parse content stream for XObject positions
            xobj_positions = {}
            if '/Contents' in page:
                contents = page['/Contents']
                if hasattr(contents, 'get_object'):
                    contents = contents.get_object()
                
                content_data = contents.get_data()
                content_str = content_data.decode('latin-1', errors='ignore')
                
                # Find XObject placements with regex
                # Pattern: numbers followed by 'cm' then XObject name and 'Do'
                pattern = r'([\d.\s-]+)\s+cm[^/]*/(\w+)\s+Do'
                matches = re.findall(pattern, content_str)
                
                print("\n=== XObject Placements ===")
                for matrix_str, xobj_name in matches:
                    matrix_values = matrix_str.strip().split()
                    if len(matrix_values) >= 6:
                        a, b, c, d, e, f = [float(v) for v in matrix_values[:6]]
                        
                        # Store position for later use
                        xobj_positions[xobj_name] = {
                            'x': e,
                            'y': f,
                            'scale_x': a,
                            'scale_y': d
                        }
                        
                        print(f"\nXObject: /{xobj_name}")
                        print(f"  Position (from bottom-left): X={e:.2f}pt, Y={f:.2f}pt")
                        print(f"  Position (from top-left): X={e:.2f}pt, Y={page_height-f:.2f}pt")
                        print(f"  Position (mm from bottom-left): X={e/72*25.4:.1f}mm, Y={f/72*25.4:.1f}mm")
                        print(f"  Position (mm from top-left): X={e/72*25.4:.1f}mm, Y={(page_height-f)/72*25.4:.1f}mm")
                        print(f"  Scale: X={a}, Y={d}")
            
            # Get XObject details
            if '/Resources' in page and '/XObject' in page['/Resources']:
                xobjects = page['/Resources']['/XObject'].get_object()
                
                print("\n=== XObject Details ===")
                for obj_name, obj in xobjects.items():
                    if hasattr(obj, 'get_object'):
                        obj = obj.get_object()
                    
                    print(f"\nXObject: {obj_name}")
                    
                    bbox_width = bbox_height = None
                    if '/BBox' in obj:
                        bbox = obj['/BBox']
                        bbox_width = float(bbox[2])-float(bbox[0])
                        bbox_height = float(bbox[3])-float(bbox[1])
                        print(f"  Size: {bbox_width:.2f} x {bbox_height:.2f} points")
                        print(f"  Size: {bbox_width/72*25.4:.1f} x {bbox_height/72*25.4:.1f} mm")
                    
                    if obj.get('/Subtype') == '/Form':
                        if '/Resources' in obj and '/XObject' in obj['/Resources']:
                            form_xobjects = obj['/Resources']['/XObject'].get_object()
                            
                            for form_obj_name, form_obj in form_xobjects.items():
                                if hasattr(form_obj, 'get_object'):
                                    form_obj = form_obj.get_object()
                                
                                if form_obj.get('/Subtype') == '/Image':
                                    image_counter += 1
                                    width = form_obj['/Width']
                                    height = form_obj['/Height']
                                    data = form_obj.get_data()
                                    size_kb = len(data) / 1024
                                    total_image_size += size_kb
                                    
                                    # Determine position description
                                    position_desc = "unknown position"
                                    obj_name_clean = obj_name.strip('/')
                                    if obj_name_clean in xobj_positions:
                                        pos = xobj_positions[obj_name_clean]
                                        x_pos = pos['x']
                                        y_pos = pos['y']
                                        
                                        # Determine quadrant
                                        is_right = x_pos > page_width / 2
                                        is_top = y_pos > page_height / 2
                                        
                                        h_pos = "right" if is_right else "left"
                                        v_pos = "top" if is_top else "bottom"
                                        position_desc = f"{v_pos}-{h_pos}"
                                    
                                    # Store image details
                                    image_details.append({
                                        'width': width,
                                        'height': height,
                                        'size_kb': size_kb,
                                        'position': position_desc,
                                        'format': form_obj.get('/Filter', 'Unknown')
                                    })
                                    
                                    print(f"  Contains Image: {form_obj_name}")
                                    print(f"    Pixel Dimensions: {width}x{height} px")
                                    print(f"    File Size: {size_kb:.2f} KB")
                                    
                                    # Extract - use a safe filename
                                    output_filename = f"extracted_image_{image_counter}.jpg"
                                    with open(output_filename, 'wb') as img_file:
                                        img_file.write(data)
                                    print(f"    Extracted to: {output_filename}")
    
    # Summary
    total_size = os.path.getsize(pdf_path) / 1024
    print(f"\n=== SUMMARY ===")
    print(f"Total PDF size: {total_size:.2f} KB")
    print(f"Total raster images: {image_counter}")
    
    # Print image details dynamically
    for i, img in enumerate(image_details, 1):
        filter_name = img['format']
        if filter_name == '/DCTDecode':
            format_str = 'JPG'
        elif filter_name == '/FlateDecode':
            format_str = 'PNG'
        else:
            format_str = str(filter_name).strip('/')
        
        print(f"\nImage {i}: {img['width']}x{img['height']}px {format_str}, {img['size_kb']:.2f} KB")
        print(f"  Position: {img['position']}")
        print(f"  Percentage of PDF: {(img['size_kb']/total_size)*100:.1f}%")
    
    print(f"\nTotal image size: {total_image_size:.2f} KB ({(total_image_size/total_size)*100:.1f}%)")
    print(f"Other content (text, fonts, vectors): {total_size - total_image_size:.2f} KB ({((total_size - total_image_size)/total_size)*100:.1f}%)")
    
    print(f"\nTo reduce file size:")
    print(f"  1. Optimize JPG images (reduce dimensions or increase compression)")
    print(f"  2. Consider simplifying vector graphics if possible")
    print(f"  3. Ensure fonts are subset (only include used characters)")

if __name__ == "__main__":
    pdf_path = r"C:\Users\MM-Vision 08-2021\Downloads\Dette er et testbrev.pdf"
    extract_and_analyze(pdf_path)