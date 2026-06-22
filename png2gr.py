from PIL import Image
import struct

def png2gr(path):
    img = Image.open(path).convert("RGBA")
    width = img.size[0]
    height = img.size[1]
    stride = (width + 7) & ~7

    color_palette = {
        (0,0,0): b'\x00',       # BLACK
        (0,0,170): b'\x01',     # BLUE
        (0,170,0): b'\x02',     # GREEN
        (0,170,170): b'\x03',   # CYAN
        (170,0,0): b'\x04',     # RED
        (170,0,170): b'\x05',   # MAGENTA
        (170,85,0): b'\x06',    # BROWN
        (170,170,170): b'\x07', # GRAY
        (85,85,85): b'\x08',    # DKGRAY
        (85,85,255): b'\x09',   # LTBLUE
        (85,255,85): b'\x0A',   # LTGREEN
        (85,255,255): b'\x0B',  # LTCYAN
        (255,85,85): b'\x0C',   # LTRED
        (255,85,255): b'\x0D',  # LTPURPLE
        (255,255,85): b'\x0E',  # YELLOW
        (255,255,255): b'\x0F', # WHITE
    }
    
    with open("output.GR", "wb") as file:
        file.write(b'\x00' * 16)
        file.write(struct.pack("<I", width))
        file.write(struct.pack("<I", stride))
        file.write(struct.pack("<I", height))

        file.write(b'\x00' * 4)

        for y in range(height):
            for x in range(width):

                pixel = img.getpixel((x, y))

                if pixel[3] < 128:
                    file.write(b'\xFF')
                else:
                    rgb = (pixel[0], pixel[1], pixel[2])
                    color_byte = color_palette[rgb]
                    file.write(color_byte)
            padding_needed = stride - width
            if padding_needed > 0:
                file.write(b'\xFF' * padding_needed)
    print("Check your output")

png2gr("mcdonaldTRANSPARENT.png")
            
        
