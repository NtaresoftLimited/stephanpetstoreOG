import qrcode

data = "https://stephanspetstore.co.tz/"
img = qrcode.make(data)
img.save("stephans_qr_code.png")
