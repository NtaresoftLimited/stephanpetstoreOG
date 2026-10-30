import os

path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\controllers\pdf_report_controller.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

old_draw_header = '''        def draw_header(canvas_obj):
            if picking.company_id.logo:
                try:
                    logo_img = ImageReader(io.BytesIO(base64.b64decode(picking.company_id.logo)))
                    canvas_obj.drawImage(logo_img, left, page_h - 31 * mm, width=42 * mm, height=17 * mm, preserveAspectRatio=True, anchor="sw", mask="auto")
                except Exception:
                    pass
                
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.drawRightString(right, page_h - 18 * mm, "Stephan's Pet Store")
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.drawRightString(right, page_h - 24 * mm, f"{picking.company_id.phone or ''}    info@stephanspetstore.co.tz")
            
            canvas_obj.setStrokeColor(HexColor("#cbd8d3"))
            canvas_obj.line(left, page_h - 34 * mm, right, page_h - 34 * mm)

            title_y, title_h = page_h - 62 * mm, 23 * mm'''

new_draw_header = '''        def draw_header(canvas_obj):
            # Logo on the RIGHT
            if picking.company_id.logo:
                try:
                    logo_img = ImageReader(io.BytesIO(base64.b64decode(picking.company_id.logo)))
                    canvas_obj.drawImage(logo_img, right - 42 * mm, page_h - 34 * mm, width=42 * mm, height=20 * mm, preserveAspectRatio=True, anchor="sw", mask="auto")
                except Exception:
                    pass
                
            # Contact Info on the LEFT
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
                y_text -= 4.5 * mm
            
            canvas_obj.setStrokeColor(HexColor("#cbd8d3"))
            canvas_obj.line(left, page_h - 38 * mm, right, page_h - 38 * mm)

            title_y, title_h = page_h - 66 * mm, 23 * mm'''

code = code.replace(old_draw_header, new_draw_header)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
