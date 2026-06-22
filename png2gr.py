from PIL import Image
import struct
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-iPath", required=True, help="Path for image ready to be converted")
parser.add_argument("-oPath", required=True, help="Output path")
parser.add_argument("-d", action="store_true", help="Dithering")
parser.add_argument("-gr2img", action="store_true", help="Converting GR to supported image formats by PIL")
args = parser.parse_args()
    

def set_pixel(x, y, pixels, error_pixel, weight):
    neighborPixel = pixels[x, y]
    new_r = int(neighborPixel[0] + error_pixel[0] * weight)
    new_g = int(neighborPixel[1] + error_pixel[1] * weight)
    new_b = int(neighborPixel[2] + error_pixel[2] * weight)
    clamped_r = max(0, min(255,new_r))
    clamped_g = max(0, min(255,new_g))
    clamped_b = max(0, min(255,new_b))
    pixels[x, y] = (clamped_r, clamped_g, clamped_b, neighborPixel[3])

def img2gr(path, outpath, dithering):
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
    
    with open(outpath, "wb") as file:
        file.write(b'\x00' * 16)
        file.write(struct.pack("<I", width))
        file.write(struct.pack("<I", stride))
        file.write(struct.pack("<I", height))

        file.write(b'\x00' * 4)

        pixels = img.load()

        
        for y in range(height):
            for x in range(width):
                pixel = pixels[x,y]

                

                if dithering:
                    old_pixel = pixels[x,y]
                    if old_pixel[3] < 128:
                        file.write(b'\xFF')
                    else:
                        smallest_distance = float('inf')
                        closest_color = pixel
                        for color in color_palette:
                            distance = ((old_pixel[0] - color[0])*(old_pixel[0] - color[0])) + ((old_pixel[1] - color[1]) * (old_pixel[1] - color[1])) + ((old_pixel[2] - color[2]) * (old_pixel[2] - color[2]))
                            if distance < smallest_distance:
                                smallest_distance = distance
                                closest_color = color
                            
                        color_byte = color_palette[closest_color]
                        file.write(color_byte)
                        err_r = old_pixel[0] - closest_color[0]
                        err_g = old_pixel[1] - closest_color[1]
                        err_b = old_pixel[2] - closest_color[2]

                        error_pixel = (err_r, err_g, err_b)
                
                        # floyd steinberg algorithm
                        if x + 1 < width:
                            set_pixel(x+1, y, pixels, error_pixel, 7/16)
                        if y + 1 < height:
                            set_pixel(x, y+1, pixels, error_pixel, 5/16)
                        if x - 1 >= 0 and y + 1 < height:
                            set_pixel(x-1, y+1, pixels, error_pixel, 3/16)
                        if x + 1 < width and y + 1 < height:
                            set_pixel(x+1, y+1, pixels, error_pixel, 1/16)
                    
                else:
                    # no dithering
                    if pixel[3] < 128:
                        file.write(b'\xFF')
                    else:
                        rgb = (pixel[0], pixel[1], pixel[2])
                        color_byte = color_palette[rgb]
                        file.write(color_byte)
            padding_needed = stride - width
            if padding_needed > 0:
                file.write(b'\xFF' * padding_needed)
    print("Done converting from your image format to GR")

def gr2img(inputPath, outputPath):
    reverse_palette = {
        b'\x00': (0,0,0),       # BLACK
        b'\x01': (0,0,170),     # BLUE
        b'\x02': (0,170,0),     # GREEN
        b'\x03': (0,170,170),   # CYAN
        b'\x04': (170,0,0),     # RED
        b'\x05': (170,0,170),   # MAGENTA
        b'\x06': (170,85,0),    # BROWN
        b'\x07': (170,170,170), # GRAY
        b'\x08': (85,85,85),    # DKGRAY
        b'\x09': (85,85,255),   # LTBLUE
        b'\x0A': (85,255,85),   # LTGREEN
        b'\x0B': (85,255,255),  # LTCYAN
        b'\x0C': (255,85,85),   # LTRED
        b'\x0D': (255,85,255),  # LTPURPLE
        b'\x0E': (255,255,85),  # YELLOW
        b'\x0F': (255,255,255), # WHITE
    }
    with open(inputPath, "rb") as file:
        file.seek(16)

        width = struct.unpack("<I", file.read(4))[0]
        stride = struct.unpack("<I", file.read(4))[0]
        height = struct.unpack("<I", file.read(4))[0]

        file.seek(4,1)

        img = Image.new("RGBA", (width, height))
        pixels = img.load()

        for y in range(height):
            for x in range(width):
                color_byte = file.read(1)
                if color_byte == b'\xFF':
                    pixels[x,y] = (0,0,0,0)
                elif color_byte in reverse_palette:
                    pixel = reverse_palette[color_byte]
                    pixels[x,y] = (pixel[0], pixel[1], pixel[2], 255)
                else:
                    pixels[x,y] = (0,0,0,255)

            padding_needed = stride - width
            if padding_needed > 0:
                file.seek(padding_needed, 1)
        img.save(outputPath)
        print("Converted GR to your image format")

def main():
    if args.gr2img:
        gr2img(args.iPath, args.oPath)
    else:
        img2gr(args.iPath, args.oPath, args.d)
    
    

if __name__ == '__main__':
    main()
            
        
