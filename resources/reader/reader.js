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
  sepia: { bg: '#f4ecd8', fg: '#3b2f1e', link: '#8a5a24', faint: '#7d6a50' },
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
    body { font-size: ${settings.size}% !important; }
    p, li, blockquote, dd { line-height: 1.6; hanging-punctuation: allow-end last; widows: 2; orphans: 2; }
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
  $('#btn-download').href = path
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

  buildTOC(book.toc || [])
  await view.init({ lastLocation: store.get(placeKey, null) })

  status.hidden = true
  for (const id of ['#btn-toc', '#btn-search', '#btn-prev', '#btn-next', '#progress']) $(id).disabled = false
  $('#progress').dir = book.dir === 'rtl' ? 'rtl' : 'ltr'
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
    const w = doc.defaultView.innerWidth
    const x = e.clientX % w
    if (x < w * 0.25) view.goLeft()
    else if (x > w * 0.75) view.goRight()
  })
}

function onRelocate(detail, { title, author, placeKey }) {
  const { fraction = 0, tocItem, cfi } = detail
  const pct = Math.round(fraction * 100)
  $('#progress').value = fraction
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
  $('#note-body').querySelector('foliate-view')?.close()
  $('#note-body').replaceChildren()
  $('#note-dialog').close()
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
function tocList(items) {
  const ol = document.createElement('ol')
  for (const item of items) {
    const li = document.createElement('li')
    const a = document.createElement('a')
    a.textContent = item.label?.trim() || 'Section'
    a.href = '#'
    a.dataset.href = item.href || ''
    a.addEventListener('click', e => {
      e.preventDefault()
      if (!item.href) return
      view.goTo(item.href)
      closePanels()
    })
    if (item.subitems?.length) {
      const details = document.createElement('details')
      const summary = document.createElement('summary')
      summary.append(a)
      details.append(summary, tocList(item.subitems))
      li.append(details)
    } else li.append(a)
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
  for (let d = a.closest('details'); d; d = d.parentElement.closest('details')) d.open = true
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
    const own = li.querySelector(':scope > a, :scope > details > summary > a')
    const hit = own && fold(own.textContent).includes(q)
    const childHit = li.querySelector('li:not(.hidden)')
    if (!hit && !childHit) li.classList.add('hidden')
    else if (childHit) { const d = li.querySelector(':scope > details'); if (d) d.open = true }
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
  if (query.length < 2) { $('#search-note').textContent = 'Type at least two letters.'; return }
  const run = searching = {}
  let found = 0
  $('#search-note').textContent = 'Searching'
  try {
    for await (const result of view.search({ query })) {
      if (run !== searching) return
      if (result === 'done') break
      if (result.progress != null) { $('#search-note').textContent = `Searching, ${Math.round(result.progress * 100)}%`; continue }
      for (const { cfi, excerpt } of result.subitems || []) {
        if (found >= 300) break
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
        b.addEventListener('click', () => { view.goTo(cfi); if (matchMedia('(max-width: 50rem)').matches) closePanels() })
        li.append(b)
        list.append(li)
      }
    }
    $('#search-note').textContent = found ? `${found}${found >= 300 ? '+' : ''} found` : 'Not found in this book.'
  } catch (err) {
    console.error(err)
    $('#search-note').textContent = 'The search could not finish.'
  }
})

// ---------------------------------------------------------------- panels
const panels = { '#btn-toc': '#toc-panel', '#btn-search': '#search-panel', '#btn-settings': '#settings-panel' }
function closePanels() {
  for (const [btn, panel] of Object.entries(panels)) { $(panel).hidden = true; $(btn).setAttribute('aria-expanded', 'false') }
  $('#scrim').hidden = true
}
for (const [btn, panel] of Object.entries(panels)) {
  $(btn).addEventListener('click', () => {
    const open = $(panel).hidden
    closePanels()
    if (!open) return
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
$('#scrim').addEventListener('click', closePanels)
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', closePanels))

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
  if (view?.renderer) { applyLayout(); view.renderer.setStyles?.(bookCSS()) }
}
$('#size-down').addEventListener('click', () => { settings.size = Math.max(70, settings.size - 10); changed() })
$('#size-up').addEventListener('click', () => { settings.size = Math.min(200, settings.size + 10); changed() })
document.querySelectorAll('[data-theme-choice]').forEach(b => b.addEventListener('click', () => { settings.theme = b.dataset.themeChoice; changed() }))
document.querySelectorAll('[data-flow-choice]').forEach(b => b.addEventListener('click', () => { settings.flow = b.dataset.flowChoice; changed() }))
document.querySelectorAll('[data-notes-choice]').forEach(b => b.addEventListener('click', () => { settings.notes = b.dataset.notesChoice; changed() }))
reflectSettings()

// ------------------------------------------------------------ navigation
function onKey(e) {
  if (e.target.closest?.('input, textarea')) return
  if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); view?.goLeft() }
  else if (e.key === 'ArrowRight' || e.key === 'PageDown' || (e.key === ' ' && settings.flow === 'paginated')) { e.preventDefault(); view?.goRight() }
  else if (e.key === 'Escape') closePanels()
}
document.addEventListener('keydown', onKey)
$('#btn-prev').addEventListener('click', () => view?.goLeft())
$('#btn-next').addEventListener('click', () => view?.goRight())
$('#progress').addEventListener('change', e => view?.goToFraction(parseFloat(e.target.value)))

openBook()
