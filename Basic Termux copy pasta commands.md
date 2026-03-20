
### entering the file system
cd storage/shared/website/HugoBasedNZBlog

### testing the website

hugo server -D --noBuildLock
Note the -F flag adds pages that are set to a future date

### generating webp images

magick ~/storage/dcim/camera/PXL_20260317_055555523.jpg -resize 2000x -quality 75 -strip ~/storage/shared/website/HugoBasedNZBlog/content/posts//.webp



magick your/file/path/input.jpg -resize 2000x -quality 75 -strip your/output/path/output.webp

magick ~/storage/dcim/camera/your image.jpg -resize 2000x -quality 75 -strip ~/storage/shared/website/HugoBasedNZBlog/yourname.webp

These images are WAY smaller, so use them instead of regular jpgs.


Rotating the images:

magick platform.webp -rotate 90 platform.webp

magick ~/storage/pictures/bungee/1_NBChairPhoto26-03-17-01-50-07-0650.jpg -resize 2000x -quality 75 -strip ~/storage/shared/website/HugoBasedNZBlog/content/posts/bungee/chair.webp



### uploading

git add .
git commit -m "your commit comment here"
git push 

Note - ensure you are in the proper directory (the one above) before running these commands)

### editing the .toml

nano hugo.toml

Note - nano is the editor. 