# Resources

A place to keep files for Gentle King, such as PDFs, handouts, and anything else
worth sharing or coming back to later.

Everything in this folder is public, like the rest of this repository. A file put
here can be opened at `https://gentleking.org/resources/` followed by its name, so
keep private things somewhere else.

To add a file, open this folder on GitHub, choose **Add file**, then
**Upload files**.

---

## The library

The `library` folder is a free library of Puritan and confessionally Reformed
books, kept small on purpose. Its aim is the books a Christian today will actually
read, in clean modern text that opens in the browser or in a reading app. It holds
56 works in 119 files, about 115 MB in all, and its catalog points to 74 more that
are online only as scans at the Internet Archive. Open the `library` folder and
scroll down to see every book in it.

**What belongs here.** A book earns a place when it is a classic still worth reading
and a clean typed text of it can be had. A book known only from a scan, however
famous, stays a link to the scan. Texts read from a scan by machine are not kept,
because they come out jumbled and misread. Old spelling, the Hebrew and Greek, and
Bibles no one reads today are left out too.

**How it is arranged.** One folder per author, named for the author, and one file per
book, named for the book. A work in several volumes has one file per volume, with
`-vol-01`, `-vol-02`, and so on at the end. For example, the Romans volume of
Calvin's commentaries is `library/john-calvin/commentaries-vol-38.epub`. The Bibles
have a folder of their own, `library/bibles`.

**The catalog.** `library/catalog.json` describes every work in one file, ready to
build a web page from. Each work has its title, author and dates, tradition,
category, when it was first published, the edition, and its files. A work in several
volumes lists what each volume holds. The `tier` says how central a work is, from
`core` through `standard` to `further`. A work kept only as a scan has `links` to the
scan at the Internet Archive instead of `files`, and a work missing a part links to a
scan of that part. A few works appear only inside a larger book, and those say so
under `found_in`.

**Where the books came from.** Most come from the Christian Classics Ethereal Library
(ccel.org), which gave Gentle King permission to share its books here, to read and
to download. A page near the front of each one says so. Gentle King added that page
and set the title and author a reading app shows to match this library, and changed
nothing else. A few come from Project Gutenberg, which keeps its license inside each
of its books. The King James Version and the Berean Standard Bible are the public
domain editions published by eBible.org, and the translators of the Berean Standard
Bible gave it to the public domain in 2023.

**Why EPUB.** GitHub Pages serves this whole site from one repository, and a site
there may take up to 1 GB. A scanned PDF of a single volume often runs 30 to 60 MB,
so the library is kept as EPUB, which runs under a megabyte or two a volume. Keep the
total for the whole site under 1 GB when adding to it.

**Reading an EPUB.** The Resources page on the site lists every book. Read opens a
book right in the browser, and a Download button gives the EPUB for a reading app.
For a book kept only as a scan, Read the scan opens the printed pages at the
Internet Archive.
On a phone, Apple Books, ReadEra, and Google Play Books open them. On a computer,
Thorium Reader, Calibre, Foliate on Linux, or Apple Books on a Mac. Sojourner can
add them to its library too.

---

## The reader

`read.html` is the page that opens a book in the browser, as
`resources/read.html?book=library/john-owen/communion-with-god.epub`. It takes only
a book from the library, and it keeps each reader's place and settings on that
reader's own device. The files that run it are in `reader`. The book itself is
drawn by foliate-js, by John Factotum, under the MIT license, in `reader/foliate`,
where `NOTICE.md` says which version it is and how to update it.

The Resources page is built from `library/catalog.json` by `build.py` at the top of
the repository. To add a book, put its file in the library, add it to the catalog,
and run `python3 build.py`. Each work in the catalog can carry `topics`, `scripture`
(the books of the Bible it expounds), `passage`, and a one-sentence `blurb`, and the
page's search and filters use them. A work marked `start` is one of the few a newcomer
can pick up first, and the page marks it as a good place to start.
