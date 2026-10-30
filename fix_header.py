import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = '''        def draw_header(canvas_obj):
            if picking.company_id.logo:
                try:
                    logo_img = ImageReader(io.BytesIO(base64.b64decode(picking.company_id.logo)))
                    canvas_obj.drawImage(logo_img, right - 42 * mm, page_h - 34 * mm, width=42 * mm, height=20 * mm, preserveAspectRatio=True, anchor="sw", mask="auto")
                except Exception:
                    pass
                
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.drawString(left, page_h - 15 * mm, "Stephan's Pet Store")
            
            canvas_obj.setFont("Helvetica", 7.5)
            text_lines = [
                "+255 786 627 873  |  +255 769 324 445",
                "11 Slipway Rd, Masaki, Dar es Salaam",
                "59 Mikocheni A, Dar es Salaam",
                "info@stephanspetstore.co.tz"
            ]
            y_text = page_h - 20 * mm
            for line in text_lines:
                canvas_obj.drawString(left, y_text, line)
                y_text -= 4.5 * mm'''

new_block = '''        def draw_header(canvas_obj):
            if picking.company_id.logo:
                try:
                    logo_img = ImageReader(io.BytesIO(base64.b64decode(picking.company_id.logo)))
                    # Draw logo on the left side
                    canvas_obj.drawImage(logo_img, left, page_h - 34 * mm, width=42 * mm, height=20 * mm, preserveAspectRatio=True, anchor="sw", mask="auto")
                except Exception:
                    pass
                
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica", 7.5)
            text_lines = [
                "+255 786 627 873  |  +255 769 324 445",
                "11 Slipway Rd, Masaki, Dar es Salaam",
                "59 Mikocheni A, Dar es Salaam",
                "info@stephanspetstore.co.tz"
            ]
            y_text = page_h - 15 * mm
            for line in text_lines:
                # Draw text right-aligned on the right side
                canvas_obj.drawRightString(right, y_text, line)
                y_text -= 4.5 * mm'''

if old_block in code:
    code = code.replace(old_block, new_block)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS: Code replaced locally.")
else:
    print("ERROR: Old block not found in file.")
