# Photo site: project notes

Handoff notes from the conversation where this site was designed and first
published (October 2026). Read this before changing anything. The README
covers day-to-day use; this file covers why things are the way they are,
what is unfinished, and what is planned.

- Live site: https://mxie9805.github.io/photo_site/
- Repository: https://github.com/mxie9805/photo_site

## Goal

A personal photography site for Michael that works both as a showcase for
strangers and as a browsable archive for himself and friends.

What he asked for:

- White, minimal look. The home page opens on one large photo.
- Browse by series (hand-assigned themes) and by place. A map page later.
- Shooting details (camera, lens, aperture and so on) shown per photo and
  kept as data he can analyse later.
- An English/Chinese switch in the top-right corner. Content is mainly
  written in English.
- A blog section later, in a plain early-BBS/blog style, for essays and
  travel notes.
- Free hosting on GitHub, no custom domain for now.
- Low upkeep: adding a photo should mean "drop a file, fill a row, publish".
- Ideally reachable from mainland China, so no Google services.

## How we got here

1. Compared hosted builders (Squarespace, Wix, Adobe Portfolio), an Astro
   template (astro-photo-folio) and a database-backed photo blog
   (exif-photo-blog). Chose a static site on GitHub Pages.
2. Designed eight pages as mockups before building anything (see below).
3. Agreed that everything in the design can be done as a static site, and
   split the work into three versions.
4. Built V1 as a small custom Python generator instead of Astro. Two
   reasons: the environment it was built in could not install Node
   packages, and Michael already knows Python, so he can read and change
   the build script and use the exported data directly.
5. Published to GitHub Pages through GitHub Actions.

## The design

The mockups live in Michael's Claude artifacts as a design canvas titled
"摄影个人站 · 初稿". They are placeholders in grey boxes, not real photos.
In words:

- **Home.** Header with the site name on the left; navigation and the
  language switch on the right. One near-full-width photo in a 16:9 frame,
  chosen at random from a hand-picked "featured" list on every visit. Under
  it, one line: title, place and year on the left; shooting details in a
  monospace face on the right; and a small "Another one" link. Below that,
  entry cards into the rest of the site and a short list of recent posts.
- **Series.** A grid of cards, one per series: cover photo, name, photo
  count, year range.
- **Places.** A list of places beside a map with numbered pins. Picking a
  place shows its photos underneath. The map is planned as static images
  (world, then continents) because interactive map services may not load
  in China.
- **All photos.** A masonry grid that keeps each photo's own proportions,
  with pill-shaped filters for series and place and a "shown / total" count.
- **Single photo.** The whole photo, uncropped. Title and a one-line note on
  the left with links to its series and place; a table of shooting details
  on the right. Previous/next links.
- **Blog.** A plain text list: date, category in brackets, underlined title.
  A category filter in a side column.
- **Blog post.** A narrow reading column with inline photos and quotes.
- **About.** Optional portrait, a short introduction, gear, contact, and an
  image-use note.

Look: white ground, near-black text, one muted grey, a burnt-orange accent
used only for hover and selected states. System fonts throughout, with a
monospace face for data. Web fonts were dropped on purpose: Google Fonts
does not load in China and would stall the page.

## What exists now (V1, live)

Built and published: home with random featured photo, all photos with
filters, single photo pages, series, about, and the language switch.

Differences from the mockups, all deliberate for V1:

- Navigation has only Series, All photos and About. Places and Blog are
  not built yet.
- Home shows series cards under the main photo instead of the three entry
  cards and recent posts.

How it works:

- `build.py` reads `photos/`, `photos.csv` and `site.toml` and writes a
  complete static site to `dist/`.
- Each photo is resized to WebP at 800, 1600 and 2400 px wide. The colour
  profile is kept; all other metadata is removed from the web copies.
- Shooting details are read from each file with Pillow. Any value typed
  into `photos.csv` overrides what the file says.
- A photo with no row in `photos.csv` still appears, titled from its file
  name.
- Order is newest first by date; undated photos follow in CSV order.
- The language switch is CSS only. Every label is rendered in both
  languages and one is hidden. The choice is remembered in the browser.
- Filters are plain links: `photos.html#series=<slug>&place=<slug>`.
- Every build also writes `dist/data/photos.csv` and `photos.json` with the
  merged details of every photo, for analysis.
- All links are relative, so the site works at any address and when opened
  straight from disk.
- `.github/workflows/publish.yml` rebuilds and publishes on every push to
  `main`. Pages is set to Source: GitHub Actions in the repository settings.

To run it locally (Python 3.11 or newer):

```
pip install -r requirements.txt
python build.py --serve      # then open http://localhost:8000
```

## Caveats

Unverified or unfinished:

- **Shooting details have never been tested on a real file.** The six
  photos in `photos/` were uploaded through a chat, which shrank them to
  2576x1717 and stripped their metadata. The reader was only tested on
  synthetic files. First job: run it on original Lightroom exports and
  check every field.
- **The sample content is made up.** Titles, the series names (Canyon,
  Ocean) and the place "Bryce Canyon, Utah" were filled in by Claude from
  looking at the pictures. The whale photos have no place. Dates are empty.
  The About page is placeholder text and the contact links are blank.
- **Fujifilm film simulation is not read automatically.** It lives in a
  maker-specific block that Pillow does not parse and that Lightroom
  exports usually drop. For now the `film` column is filled by hand. Film
  scans need every detail filled by hand.
- **Only the live home page was checked after publishing.** The other
  pages were tested in a local browser before upload, at desktop and phone
  widths, but not clicked through on the live address.
- **Access from mainland China is untested.** github.io addresses are
  reported to be unreliable there. Check before relying on it.

Things to know:

- **The repository is public, so every file in `photos/` can be downloaded
  by anyone, with its original metadata.** Export at about 3000 px on the
  long edge, not full size, and remove location data on export if a photo
  was taken somewhere private.
- **Size limits.** GitHub recommends keeping a repository under 1 GB and
  caps a published site at 1 GB. At about 1 MB per exported photo that is
  several hundred photos. If the collection outgrows it, move the images
  to object storage.
- **Renaming the repository or the GitHub username changes the site
  address** and breaks links already shared.
- **The language switch only translates interface text.** Titles, notes
  and places need their `_zh` columns filled in to appear in Chinese.
- **The publish workflow shows deprecation warnings** for the action
  versions it uses (Node 20). They are harmless today. Update the action
  versions when convenient.
- **Changes go straight to `main`** with no review step. That is fine for
  a one-person site. Switch to pull requests if Michael wants to see each
  change before it goes live.

## Plan

**Finish V1**

1. Replace the sample photos with original exports and verify the shooting
   details end to end.
2. Put in real titles, series, places and dates. Choose the featured list.
3. Write the About text and add contact links in `site.toml`.
4. Click through the live site on a phone and a desktop.

**V2: writing and places**

- Blog: one Markdown file per post, a list page with a category filter,
  and a post page. Recent posts on the home page.
- Places: a list page, and the Places entry on the home page and in the
  navigation.

**V3: map and data**

- Map page from static region images with clickable pins. Consider an
  interactive map only after confirming the provider loads in China.
- A statistics page built from the exported photo data: focal lengths,
  apertures, cameras, film stocks over time.

**Later, if wanted**

- A custom domain.
- Reading Fujifilm film simulation with ExifTool.
- Self-hosted fonts.
- Moving images to object storage.

## Working with Michael

- He is new to Git, GitHub and web development, and wants to learn. Say
  what each command does before running it, and name the concept (commit,
  push, branch, pull request).
- He is comfortable with Python, SQL and data analysis. Keep the build in
  Python and keep the data easy to query.
- He prefers structured answers with the evidence shown.
- He reads and writes both English and Chinese.
- Make the technical decision and explain it, but check with him on
  anything that changes how the site looks or what it says.
