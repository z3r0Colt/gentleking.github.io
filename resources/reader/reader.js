/* Gentle King reader.

   Opens one book from the library, named in the address as ?book=library/...,
   and lets the reader page through it, find a chapter, search the text, set
   the size and color of the page, and read the notes. It remembers each
   reader's place in each book on that reader's own device, and keeps a short
   list of books read lately for the library page to offer again.

   The rendering itself is foliate-js (MIT), in ./foliate. */

import './foliate/view.js'
import { FootnoteHandler } from './foliate/footnotes.js'

const $ = sel => document.querySelector(sel)
const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v) } catch { return fallback }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* private mode, nothing to do */ }
  },
}

const SETTINGS_KEY = 'gk-reader'
const RECENT_KEY = 'gk-recent'
const settings = Object.assign({ size: 100, theme: null, flow: 'paginated', notes: 'popup' }, store.get(SETTINGS_KEY, {}))
settings.theme ||= document.documentElement.getAttribute('data-theme') || 'light'
const saveSettings = () => store.set(SETTINGS_KEY, settings)

const PAGE = {
  light: { bg: '#fbf8f2', fg: '#1c1a17', link: '#7d5f34', faint: '#706859' },
  sepia: { bg: '#f4ecd8', fg: '#3b2f1e', link: '#84561f', faint: '#6f5d45' },
  dark: { bg: '#151310', fg: '#ece6d9', link: '#d8b955', faint: '#8a8272' },
}

// the styles laid over every book: the page color, the text size, and
// whether notes stay hidden until tapped
const bookCSS = () => {
  const c = PAGE[settings.theme] || PAGE.light
  return `
    @namespace epub "http://www.idpf.org/2007/ops";
    html { color-scheme: ${settings.theme === 'dark' ? 'dark' : 'light'}; }
    html, body { background: ${c.bg} !important; color: ${c.fg} !important; }
    body { font-size: ${settings.size}% !important; line-height: 1.6 !important; }
    p, li, blockquote, dd { line-height: 1.6; hanging-punctuation: allow-end last; widows: 2; orphans: 2; }
    /* the chapter buttons at the head of each book in the eBible.org Bibles */
    ul.tnav a { border: 1px solid ${c.faint} !important; background: transparent !important; color: ${c.link} !important; border-radius: 4px !important; }
    a:link, a:visited { color: ${c.link} !important; }
    img { max-width: 100%; height: auto; }
    pre { white-space: pre-wrap !important; }
    ${settings.theme === 'dark' ? `* { border-color: #2e2a22 !important; } td, th { background: transparent !important; }` : ''}
    ${settings.notes === 'popup' ? `
      aside[epub|type~="footnote"], aside[epub|type~="endnote"],
      aside[epub|type~="note"], aside[epub|type~="rearnote"] { display: none; }` : `
      aside[epub|type~="footnote"] { display: block; margin: .3em 0 .6em 1.5em; font-size: .88em; color: ${c.faint}; }`}
  `
}

// ---------------------------------------------------------------- the book
const params = new URLSearchParams(location.search)
const path = params.get('book') || ''
const VALID = /^library\/[a-z0-9][a-z0-9\-/]*\.epub$/

const status = $('#status')
const fail = (message, download = true) => {
  status.hidden = false
  status.classList.add('failed')
  $('#status-text').innerHTML = message + (download && VALID.test(path)
    ? ` You can still <a href="${path}" download>download the book</a> and open it in a reading app.` : '')
  $('#book-title').textContent = 'The book could not be opened'
}

const langText = x => !x ? '' : typeof x === 'string' ? x : x[Object.keys(x)[0]] || ''
const contributor = x => Array.isArray(x)
  ? x.map(contributor).filter(Boolean).join(', ')
  : typeof x === 'string' ? x : langText(x?.name)

let view
let pending = null
let saveTimer = 0

async function openBook() {
  if (!VALID.test(path) || path.includes('..')) {
    fail('No book was named in the address, or the name is not one from the library.', false)
    return
  }
  const download = $('#btn-download')
  download.href = path
  download.setAttribute('download', '')
  download.removeAttribute('aria-disabled')
  const placeKey = 'gk-read:' + path

  view = document.createElement('foliate-view')
  view.setAttribute('autohide-cursor', '')
  $('#stage').append(view)
  try {
    await view.open(path)
  } catch (e) {
    console.error(e)
    fail(/404/.test(e?.message) ? 'This book is not in the library. It may have been moved or renamed.'
      : 'Something went wrong while opening this book.', !/404/.test(e?.message))
    view.remove()
    return
  }

  const { book } = view
  // A book in Hebrew that does not name its page direction still reads from
  // right to left, so the arrows, taps, and slider should turn that way.
  if (!book.dir && view.language?.direction === 'rtl') book.dir = 'rtl'
  const title = langText(book.metadata?.title) || 'Untitled'
  const author = contributor(book.metadata?.author)
  document.title = `${title} · Gentle King`
  $('#book-title').textContent = title
  $('#book-author').textContent = author

  applyLayout()
  view.renderer.setStyles?.(bookCSS())
  view.addEventListener('load', onLoad)
  view.addEventListener('relocate', e => onRelocate(e.detail, { title, author, placeKey }))
  view.addEventListener('link', onLink)
  view.addEventListener('external-link', openOutside)

  buildTOC(book.toc || [])
  // A place saved before a book was replaced may no longer exist in it. Then
  // the book opens at its start, and the old place is forgotten.
  try {
    await view.init({ lastLocation: store.get(placeKey, null) })
  } catch (e) {
    console.warn(e)
  }
  if (!view.lastLocation) {
    store.set(placeKey, null)
    try { await view.init({}) } catch (e) { console.warn(e) }
  }

  status.hidden = true
  for (const id of ['#btn-toc', '#btn-search', '#btn-prev', '#btn-next', '#progress']) $(id).disabled = false
  $('#progress').dir = book.dir === 'rtl' ? 'rtl' : 'ltr'
  // in a right to left book the next page is the one on the left
  if (book.dir === 'rtl') {
    $('#btn-prev').setAttribute('aria-label', 'Next page')
    $('#btn-next').setAttribute('aria-label', 'Previous page')
  }
  $('#stage').focus({ preventScroll: true })
}

function applyLayout() {
  const r = view?.renderer
  if (!r) return
  r.setAttribute('flow', settings.flow)
  r.setAttribute('margin', '44px')
  r.setAttribute('gap', '6%')
  r.setAttribute('max-inline-size', '720px')
  r.setAttribute('max-column-count', '1')
}

function onLoad({ detail: { doc } }) {
  doc.addEventListener('keydown', onKey)
  // a tap near the left or right edge turns the page, as on a phone
  doc.addEventListener('click', e => {
    if (settings.flow !== 'paginated') return
    if (e.target.closest('a, button, input, select, textarea, summary')) return
    if (doc.getSelection()?.toString()) return
    // In pages mode the chapter is one long strip, a page wide per page, so
    // the tap is measured within the page on screen.
    const w = view.renderer.size
    if (!w) return
    const x = e.clientX % w
    if (x < w * 0.25) view.goLeft()
    else if (x > w * 0.75) view.goRight()
  })
}

function onRelocate(detail, { title, author, placeKey }) {
  const { fraction = 0, tocItem, cfi } = detail
  const pct = Math.round(fraction * 100)
  $('#progress').value = fraction
  $('#progress').setAttribute('aria-valuetext', [tocItem?.label, `${pct}%`].filter(Boolean).join(', '))
  $('#where-text').textContent = [tocItem?.label, `${pct}%`].filter(Boolean).join(' · ')
  if (tocItem?.href) markCurrent(tocItem.href)
  if (!cfi) return
  // the place is written once the pages stop turning, and at once if the
  // reader leaves, so a quick run of page turns never loses the last one
  pending = { placeKey, cfi, entry: { book: path, title, author, pct } }
  clearTimeout(saveTimer)
  saveTimer = setTimeout(savePlace, 500)
}

function savePlace() {
  if (!pending) return
  const { placeKey, cfi, entry } = pending
  pending = null
  store.set(placeKey, cfi)
  const recent = store.get(RECENT_KEY, []).filter(r => r.book !== path)
  recent.unshift({ ...entry, at: Date.now() })
  store.set(RECENT_KEY, recent.slice(0, 12))
}
addEventListener('pagehide', savePlace)
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') savePlace() })

// ------------------------------------------------------------------ notes
const footnotes = new FootnoteHandler()
// the note is drawn by a second, small view of the same book, which has to be
// on the page and showing before it can lay out the text
footnotes.addEventListener('before-render', e => {
  const { view: noteView } = e.detail
  noteView.addEventListener('link', le => { le.preventDefault() })
  noteView.addEventListener('external-link', openOutside)
  $('#note-body').replaceChildren(noteView)
  if (!$('#note-dialog').open) $('#note-dialog').showModal()
  noteView.renderer.setAttribute('flow', 'scrolled')
  noteView.renderer.setAttribute('margin', '16px')
  noteView.renderer.setAttribute('gap', '5%')
  noteView.renderer.setStyles?.(bookCSS().replace(/aside\[[^{]*\{ display: none; \}/g, ''))
})
// the small view is shut down before the box hides, or it tries to lay out
// text in a box that is no longer there
function closeNote() {
  // a note shut while it is still loading has nothing to close yet
  try { $('#note-body').querySelector('foliate-view')?.close() } catch (e) { console.warn(e) }
  $('#note-body').replaceChildren()
  if ($('#note-dialog').open) $('#note-dialog').close()
  $('#stage').focus({ preventScroll: true })
}

// a link out of the book opens in a new tab that cannot reach back into this one
function openOutside(e) {
  e.preventDefault()
  window.open(e.detail.href_, '_blank', 'noopener')
}
$('#note-dialog').addEventListener('cancel', e => { e.preventDefault(); closeNote() })
$('#note-dialog').addEventListener('submit', e => { e.preventDefault(); closeNote() })
$('#note-dialog').addEventListener('click', e => { if (e.target === e.currentTarget) closeNote() })

function onLink(e) {
  if (settings.notes !== 'popup') return
  const handled = footnotes.handle(view.book, e)
  handled?.catch(err => {
    console.warn(err)
    closeNote()
    // if the note could not be shown by itself, go to it in the book instead
    view.goTo(e.detail.href)
  })
}

// --------------------------------------------------------------- contents
// Each chapter is a link, and a chapter with parts has a small button beside
// it to show them, so the keyboard meets one of each and nothing nested.
function setOpen(li, open) {
  const toggle = li.querySelector(':scope > .toc-row > .toc-toggle')
  const sub = li.querySelector(':scope > ol')
  if (!toggle || !sub) return
  toggle.setAttribute('aria-expanded', String(open))
  sub.hidden = !open
}

function tocList(items) {
  const ol = document.createElement('ol')
  for (const item of items) {
    const li = document.createElement('li')
    const row = document.createElement('div')
    row.className = 'toc-row'
    const a = document.createElement('a')
    a.textContent = item.label?.trim() || 'Section'
    a.href = '#'
    a.dataset.href = item.href || ''
    a.addEventListener('click', e => {
      e.preventDefault()
      if (!item.href) return
      view.goTo(item.href)
      closePanels(false)
      $('#stage').focus({ preventScroll: true })
    })
    if (item.subitems?.length) {
      const toggle = document.createElement('button')
      toggle.type = 'button'
      toggle.className = 'toc-toggle'
      toggle.setAttribute('aria-expanded', 'false')
      toggle.setAttribute('aria-label', 'Show the parts of ' + a.textContent)
      toggle.addEventListener('click', () => setOpen(li, toggle.getAttribute('aria-expanded') !== 'true'))
      row.append(toggle, a)
      const sub = tocList(item.subitems)
      sub.hidden = true
      li.append(row, sub)
    } else {
      const spacer = document.createElement('span')
      spacer.className = 'toc-spacer'
      row.append(spacer, a)
      li.append(row)
    }
    ol.append(li)
  }
  return ol
}

function buildTOC(toc) {
  const nav = $('#toc')
  nav.replaceChildren(toc.length ? tocList(toc) : Object.assign(document.createElement('p'), { textContent: 'This book has no contents list.' }))
}

function markCurrent(href) {
  const nav = $('#toc')
  nav.querySelectorAll('a[aria-current]').forEach(a => a.removeAttribute('aria-current'))
  const a = [...nav.querySelectorAll('a')].find(x => x.dataset.href === href)
  if (!a) return
  a.setAttribute('aria-current', 'true')
  for (let li = a.closest('li')?.parentElement.closest('li'); li; li = li.parentElement.closest('li')) setOpen(li, true)
}

// old printings spell John as Iohn and Saviour as Sauiour, so i and j, and
// u and v, count as the same letter when finding a chapter
const fold = s => s.toLowerCase().replace(/j/g, 'i').replace(/v/g, 'u')
$('#toc-filter').addEventListener('input', e => {
  const q = fold(e.target.value.trim())
  const items = [...$('#toc').querySelectorAll('li')]
  for (const li of items) li.classList.remove('hidden')
  if (!q) return
  for (const li of items.reverse()) {
    const own = li.querySelector(':scope > .toc-row > a')
    const hit = own && fold(own.textContent).includes(q)
    const childHit = li.querySelector(':scope > ol > li:not(.hidden)')
    if (!hit && !childHit) li.classList.add('hidden')
    else if (childHit) setOpen(li, true)
  }
})

// ----------------------------------------------------------------- search
let searching = null
$('#search-form').addEventListener('submit', async e => {
  e.preventDefault()
  const query = $('#search-input').value.trim()
  const list = $('#search-results')
  list.replaceChildren()
  view.clearSearch()
  // a new search, even one too short to run, stops the one before it
  searching = null
  if (query.length < 2) { $('#search-note').textContent = 'Type at least two letters.'; return }
  const run = searching = {}
  let found = 0
  let told = 0
  $('#search-note').textContent = 'Searching'
  try {
    // Past 300 finds the search stops, since leaving the loop tells foliate
    // to stop reading the book, and a common word in a large book would
    // otherwise hold the page for a long time.
    search: for await (const result of view.search({ query })) {
      if (run !== searching) return
      if (result === 'done') break
      if (result.progress != null) {
        const pct = Math.round(result.progress * 100)
        if (pct - told >= 25) { told = pct; $('#search-note').textContent = `Searching, ${pct}%` }
        continue
      }
      for (const { cfi, excerpt } of result.subitems || []) {
        if (found >= 300) break search
        found++
        const li = document.createElement('li')
        const b = document.createElement('button')
        b.type = 'button'
        const where = document.createElement('span')
        where.className = 'section'
        where.textContent = result.label || ''
        const mark = document.createElement('mark')
        mark.textContent = excerpt.match
        b.append(where, document.createTextNode('…' + excerpt.pre), mark, document.createTextNode(excerpt.post + '…'))
        b.addEventListener('click', () => {
          view.goTo(cfi)
          if (matchMedia('(max-width: 50rem)').matches) { closePanels(false); $('#stage').focus({ preventScroll: true }) }
        })
        li.append(b)
        list.append(li)
      }
    }
    if (run !== searching) return
    $('#search-note').textContent = found >= 300 ? 'The first 300 found' : found ? `${found} found` : 'Not found in this book.'
  } catch (err) {
    console.error(err)
    $('#search-note').textContent = 'The search could not finish.'
  }
})

// ---------------------------------------------------------------- panels
const panels = { '#btn-toc': '#toc-panel', '#btn-search': '#search-panel', '#btn-settings': '#settings-panel' }
let opener = null
const anyPanelOpen = () => Object.values(panels).some(p => !$(p).hidden)
// Closing a panel gives the keyboard back to the button that opened it,
// unless the reader chose a place in the book, which then takes it.
function closePanels(restore = true) {
  const wasOpen = anyPanelOpen()
  for (const [btn, panel] of Object.entries(panels)) { $(panel).hidden = true; $(btn).setAttribute('aria-expanded', 'false') }
  $('#scrim').hidden = true
  if (wasOpen && restore && opener) opener.focus({ preventScroll: true })
}
for (const [btn, panel] of Object.entries(panels)) {
  $(btn).addEventListener('click', () => {
    const open = $(panel).hidden
    closePanels(false)
    if (!open) { $(btn).focus(); return }
    opener = $(btn)
    $(panel).hidden = false
    $(btn).setAttribute('aria-expanded', 'true')
    $('#scrim').hidden = false
    // on a phone, jumping into a text box would pop up the keyboard over the
    // contents, so only search, which needs typing, takes the cursor there
    const first = panel === '#search-panel' || matchMedia('(hover: hover)').matches
      ? $(panel).querySelector('input, button:not([data-close])') : $(panel).querySelector('[data-close]')
    first?.focus()
  })
}
$('#scrim').addEventListener('click', () => closePanels())
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', () => closePanels()))

// -------------------------------------------------------------- settings
function reflectSettings() {
  $('#size-value').textContent = settings.size + '%'
  document.querySelectorAll('[data-theme-choice]').forEach(b => b.setAttribute('aria-checked', String(b.dataset.themeChoice === settings.theme)))
  document.querySelectorAll('[data-flow-choice]').forEach(b => b.setAttribute('aria-checked', String(b.dataset.flowChoice === settings.flow)))
  document.querySelectorAll('[data-notes-choice]').forEach(b => b.setAttribute('aria-checked', String(b.dataset.notesChoice === settings.notes)))
  document.documentElement.setAttribute('data-theme', settings.theme)
  document.querySelector('meta[name="theme-color"]').setAttribute('content', (PAGE[settings.theme] || PAGE.light).bg)
}
function changed() {
  saveSettings()
  reflectSettings()
  rovingRadios()
  if (view?.renderer) { applyLayout(); view.renderer.setStyles?.(bookCSS()) }
}
$('#size-down').addEventListener('click', () => { settings.size = Math.max(70, settings.size - 10); changed() })
$('#size-up').addEventListener('click', () => { settings.size = Math.min(200, settings.size + 10); changed() })
document.querySelectorAll('[data-theme-choice]').forEach(b => b.addEventListener('click', () => { settings.theme = b.dataset.themeChoice; changed() }))
document.querySelectorAll('[data-flow-choice]').forEach(b => b.addEventListener('click', () => { settings.flow = b.dataset.flowChoice; changed() }))
document.querySelectorAll('[data-notes-choice]').forEach(b => b.addEventListener('click', () => { settings.notes = b.dataset.notesChoice; changed() }))
reflectSettings()

// Each row of choices is one stop for the Tab key, and the arrow keys move
// along it and choose, the way a group of radio buttons works.
function rovingRadios() {
  for (const group of document.querySelectorAll('[role="radiogroup"]')) {
    const radios = [...group.querySelectorAll('[role="radio"]')]
    radios.forEach(r => { r.tabIndex = r.getAttribute('aria-checked') === 'true' ? 0 : -1 })
  }
}
for (const group of document.querySelectorAll('[role="radiogroup"]')) {
  group.addEventListener('keydown', e => {
    const radios = [...group.querySelectorAll('[role="radio"]')]
    const at = radios.indexOf(document.activeElement)
    if (at === -1) return
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
    if (!step) return
    e.preventDefault()
    const next = radios[(at + step + radios.length) % radios.length]
    next.click()
    next.focus()
  })
}
rovingRadios()

// ------------------------------------------------------------ navigation
function onKey(e) {
  // Escape shuts an open panel from anywhere, its search box included. An
  // open note shuts itself.
  if (e.key === 'Escape') {
    if (!$('#note-dialog').open && anyPanelOpen()) { e.preventDefault(); closePanels() }
    return
  }
  // Keys belong to a note, a panel, or a box being typed in while one is open.
  if ($('#note-dialog').open) return
  const t = e.target
  if (anyPanelOpen() || t.closest?.('input, textarea, select, .panel, dialog')) return
  // Space presses a focused button, as it always does. On a link it does
  // nothing, so there it still turns the page.
  if (e.key === ' ' && t.closest?.('button, summary')) return
  const scrolled = settings.flow === 'scrolled'
  if (e.key === 'ArrowLeft') { e.preventDefault(); view?.goLeft() }
  else if (e.key === 'ArrowRight') { e.preventDefault(); view?.goRight() }
  else if (e.key === 'PageUp' || (e.key === ' ' && e.shiftKey)) { e.preventDefault(); view?.prev() }
  else if (e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); view?.next() }
  else if (scrolled && e.key === 'ArrowUp') { e.preventDefault(); view?.prev(40) }
  else if (scrolled && e.key === 'ArrowDown') { e.preventDefault(); view?.next(40) }
}
document.addEventListener('keydown', onKey)
// On a wide screen the page sits in the middle, and a tap in the blank space
// to either side turns the page too. A tap on the page itself is handled in
// onLoad, since it lands inside the book's own frame.
$('#stage').addEventListener('click', e => {
  if (!view || settings.flow !== 'paginated' || !status.hidden) return
  const r = $('#stage').getBoundingClientRect()
  const x = (e.clientX - r.left) / r.width
  if (x < 0.25) view.goLeft()
  else if (x > 0.75) view.goRight()
})
$('#btn-prev').addEventListener('click', () => view?.goLeft())
$('#btn-next').addEventListener('click', () => view?.goRight())
$('#progress').addEventListener('change', e => view?.goToFraction(parseFloat(e.target.value)))

openBook()
