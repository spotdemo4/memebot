from html2image import Html2Image
from PIL import Image

url = "https://twitter.com/TheOmniLiberal/status/1725561058855723011"

better_url = url.split('?')[0]
twitter_id = url.split('/')[-1].split('?')[0]
hti = Html2Image(size=(800, 1500), custom_flags=['--virtual-time-budget=10000', '--hide-scrollbars', '--default-background-color=00000000', '--no-sandbox'])
img_paths = hti.screenshot(url=url, save_as='twitter.png')
img = Image.open(img_paths[0])
imageBox = img.getbbox()
cropped = img.crop(imageBox)
cropped.save(img_paths[0])