
This is the "Golden Path" for your specific setup. Since you are using a mobile-first workflow (Obsidian + Termux), this flow is designed to be fast and keep your files organized so the "Nuclear Option" theme and images never break.

---
### Phase 1: Creation (In Obsidian)

Hugo works best with **Page Bundles**. Instead of a single file, every post gets its own folder.

1. **Create a Folder:** Inside your `content/posts/` directory, create a new folder named after your post (e.g., `nz-glacier-hike`).
    
2. **Create the File:** Inside that folder, create a file named `index.md`.
    
3. **Add Media:** * **Photos:** Drag your `.jpg` or `.png` directly into that folder.
    
    - **Audio:** Drag your `.mp3` or `.wav` into the same folder.
        
4. **Write the Content:**
    
    Markdown
    
    ```
    ---
    title: "Hiking the Franz Josef Glacier"
    date: 2025-12-30
    draft: false
    ---
    
    This hike was incredible! Check out this view:
    
    ![Glacier View](glacier.jpg)
    
    And listen to the sound of the melting ice:
    
    <audio controls src="glacier-sounds.mp3"></audio>
    ```
    

---

### Phase 2: Preview & Polish (In Termux)

Before going live, check that your "Nuclear" theme and media are rendering correctly.

1. Open Termux and go to your blog folder:
    
    cd ~/storage/downloads/Alex-G-Strong.github.io
    
2. Start the local server:
    
    hugo server
    
3. **View locally:** Open `http://localhost:1313` in your phone's browser.
    
    - _Check:_ Do the images load? Does the audio play? If yes, proceed.
        

---

### Phase 3: Deployment (The "Git Push")

Now we send your local work to the world.

1. **Stop the server:** Press `Ctrl + C` in Termux.
    
2. **Sync to GitHub:**
    
    Bash
    
    ```
    git add .
    git commit -m "Added Glacier Hike post with media"
    git push
    ```
    
3. **Wait for the Robot:** Give GitHub Actions about 60 seconds to finish the build. Verify it’s live at `https://www.alexstrong.design/posts/nz-glacier-hike/`.
    

---

### Phase 4: The "Magic" Email (The Buttondown "Scraper" Method)

Since the RSS automation can be finicky on free tiers, we will use the **"Import from URL"** method. This is the most reliable way to ensure your email looks exactly like your blog post.

1. **Copy your Post URL:** Copy the link to your new live post.
    
2. **Log into [Buttondown](https://buttondown.email/):**
    
3. **Create New Email:** Click the **"Emails"** tab -> **"New"**.
    
4. **Import:** Look for the **"Import from URL"** or **"Fetch content"** icon (usually looks like a link or a globe).
    
5. **Paste & Fetch:** Paste your post URL. Buttondown will "scrape" your Hugo site, pull in your text, and even grab your images.
    
6. **Send:** Do a quick sanity check of the text, then hit **"Send to Subscribers."**
    

---

### Summary Checklist for Success

- **Organized Folders:** Always use `posts/folder-name/index.md`. This ensures your `![Image](image.jpg)` links work in Obsidian, Hugo, and the email scraper.
    
- **Media Names:** Keep media filenames simple (e.g., `glacier.jpg`, not `IMG_20251230_12345.JPG`). Avoid spaces in filenames.
    
- **The "Nuclear" Rule:** Since we moved the theme files directly into your repo, you never have to worry about submodules again. Just edit and push!
    

**Would you like me to create a "One-Touch" script for Termux where you can just type `publish` and it handles the Git Add, Commit, and Push for you in one go?**



## Email List (after the push)

The "Manual" Workaround (If RSS is restricted)

If Buttondown tells you that RSS automation requires a paid plan, don't worry. You can still do this easily:

1. Go to your **Buttondown "Emails"** tab.
2. Click **"New Email"**.
3. There is usually an **"Import from URL"** button.
4. Paste the link to your latest blog post (e.g., `https://www.alexstrong.design/posts/my-trip`).
5. Buttondown will "scrape" the post and turn it into a newsletter instantly.