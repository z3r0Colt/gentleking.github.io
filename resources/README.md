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
books, all in the public domain, with Bibles, study Bibles, and commentaries among
them. It holds 517 works in 915 files, about 570 MB in all, and its catalog
points to 61 more that stay as scans at the Internet Archive. Open the `library`
folder and scroll down to see every book in it.

**How it is arranged.** One folder per author, named for the author, and one file per
book, named for the book. A work in several volumes has one file per volume, with
`-vol-01`, `-vol-02`, and so on at the end. For example, the eighth volume of Owen's
works is `library/john-owen/works-of-john-owen-vol-08.epub`. The Bibles have a
folder of their own, `library/bibles`, named by version and year, such as
`library/bibles/geneva-bible-1599.epub`.

**The catalog.** `library/catalog.json` describes every work in one file, ready to
build a web page from. Each work has its title, author and dates, tradition,
category, when it was first published, the edition the file was made from, and its
files. The categories begin with `Bibles`, `Study Bibles`, and further on
`Commentaries`. A work in several volumes lists what each volume holds. The `tier`
says how central a work is, from `core` through `standard` to `further`. Some old
printings are too large or too hard to read to keep here. Those have `links` to the
scan at the Internet Archive instead of `files`, and a work missing a part in its
transcription links to a scan of that part. A few works appear only inside a larger
book, such as Owen's *Pneumatologia* in volumes 3 and 4 of his Works, and those say
so under `found_in`.

**Where the books came from.** Nothing here came from the Christian Classics
Ethereal Library. The books come from four places.

Most were made by Gentle King from scans of printings dated 1930 or earlier, kept by
the Internet Archive and the libraries that lent them. The text was read from the
scan by machine, so expect a misread word now and then, and Greek and Hebrew rarely
come through. The first page of each book names the printing and links to the scan.

The books of the 1500s and 1600s were made by Gentle King from the typed
transcriptions of the Text Creation Partnership, which gave them to the public domain
(CC0). Their spelling is as first printed, *vnto* and *haue* and all, except that
the long s is given as a plain s. A dot or a diamond in angle brackets marks a letter
or word that could not be read in the copy transcribed. Notes printed beside or
below the text, like Poole's annotations or the Geneva notes, follow the verse they
belong to, and a tap on the letter in the text opens them.

The King James, the 1599 Geneva, the American Standard Version, the Berean Standard
Bible, the Hebrew Old Testament, and the Greek New Testament are the public domain
editions published by eBible.org. The Berean Literal Bible comes from LiteralBible.com,
made into an EPUB here with its words unchanged. The translators of both Berean Bibles
gave them to the public domain in 2023. A few other books come from Project
Gutenberg, which keeps its license inside each of its books.

**Why so few PDFs.** GitHub Pages serves this whole site from one repository, and a
site there may take up to 1 GB. A scanned PDF of a single volume often runs 30 to 60
MB, so the library is kept as EPUB, which runs under a megabyte a volume. The few
PDFs here are small ones. Keep the total for the whole site under 1 GB when adding
to it.

**Reading an EPUB.** On a phone, Apple Books and Google Play Books open them. On a
computer, Calibre, Thorium Reader, or Apple Books. Sojourner can add them to its
library too.
