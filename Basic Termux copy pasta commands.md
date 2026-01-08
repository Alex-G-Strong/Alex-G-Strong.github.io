
### entering the file system
cd storage/shared/website/HugoBasedNZBlog

### testing the website

hugo server -D --noBuildLock
Note the -F flag adds pages that are set to a future date

### generating webp images

magick your/file/path/input.jpg -resize 2000x -quality 75 -strip your/output/path/output.webp

These images are WAY smaller, so use them instead of regular jpgs.

### uploading

git add .
git commit -m "your commit comment here"
git push 

Note - ensure you are in the proper directory (the one above) before running these commands)

### editing the .toml

nano hugo.toml

Note - nano is the editor. 