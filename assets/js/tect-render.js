/**
 * tect-render.js — Client-side data-driven rendering engine for the TECT website.
 *
 * Architecture:
 *   Each page loads:
 *     1. data/site.js        → window.TECT_SITE   (nav, brand, shared config)
 *     2. data/<page>.js      → window.TECT_<PAGE>  (page-specific data)
 *     3. assets/js/tect-render.js  (this file)
 *     4. Inline <script>TECT.render('pageId', window.TECT_<PAGE>);</script>
 *
 *   Data files use plain JS globals (not ES modules) so they work from file://
 *   without CORS issues.  Content is JSON-compatible objects with optional HTML
 *   strings for MathJax-heavy prose.
 *
 * Block types recognised by renderBlock():
 *   kpi-row, table, list, html, card, heading, paragraph,
 *   timeline, changelog, sm-table, pre
 */
(function () {
  'use strict';

  var TECT = window.TECT = window.TECT || {};

  /* ================================================================
   *  Low-level helpers
   * ================================================================ */

  function tag(type, text) {
    return '<span class="tag tag-' + type + '">' + text + '</span>';
  }

  /** Render a single table cell value. */
  function cell(v) {
    if (v == null) return '';
    if (typeof v === 'string') return v;
    if (v.tag)  return tag(v.tag, v.text);
    if (v.html) return v.html;
    if (v.code) return '<code>' + v.code + '</code>';
    return String(v);
  }

  function attrs(obj) {
    if (!obj) return '';
    var s = '';
    for (var k in obj) {
      if (obj.hasOwnProperty(k)) s += ' ' + k + '="' + obj[k] + '"';
    }
    return s;
  }

  /* ================================================================
   *  Block renderers
   * ================================================================ */

  function renderTable(d) {
    var cls = d.class ? ' class="' + d.class + '"' : '';
    var h = '<table' + cls + '>\n';
    if (d.headers) {
      h += '<tr>' + d.headers.map(function (t) { return '<th>' + t + '</th>'; }).join('') + '</tr>\n';
    }
    (d.rows || []).forEach(function (row) {
      h += '<tr>';
      row.forEach(function (c) {
        var a = '';
        if (c && typeof c === 'object' && !c.tag && !c.html && !c.code) {
          if (c.colspan) a += ' colspan="' + c.colspan + '"';
          if (c.style)   a += ' style="' + c.style + '"';
          h += '<td' + a + '>' + cell(c.content != null ? c.content : c) + '</td>';
        } else {
          h += '<td>' + cell(c) + '</td>';
        }
      });
      h += '</tr>\n';
    });
    h += '</table>';
    return h;
  }

  function renderList(d) {
    var cls = d.class || 'tight';
    return '<ul class="' + cls + '">\n' +
      (d.items || []).map(function (i) { return '<li>' + (typeof i === 'string' ? i : cell(i)) + '</li>'; }).join('\n') +
      '\n</ul>';
  }

  function renderKPIRow(d) {
    return '<div class="kpi-row">\n' +
      (d.items || []).map(function (k) {
        return '<div class="kpi">' +
          '<div class="label">' + k.label + '</div>' +
          '<div class="value">' + k.value + '</div>' +
          (k.note ? '<div class="muted">' + k.note + '</div>' : '') +
          '</div>';
      }).join('\n') + '\n</div>';
  }

  function renderTimeline(d) {
    return '<ul class="timeline">\n' +
      (d.items || []).map(function (it) {
        var inner = '<span class="t-date">' + it.date + '</span> ' +
          '<span class="t-area">' + it.area + '</span> ' +
          '<strong>' + it.title + '</strong>';
        if (it.body) inner += '\n<p>' + it.body + '</p>';
        return '<li>' + inner + '</li>';
      }).join('\n') + '\n</ul>';
  }

  function renderChangelog(d) {
    return (d.entries || []).map(function (e) {
      var h = '<div class="changelog-version">\n' +
        '<h2><code>' + e.tag + '</code> <span class="date">' + e.date + '</span></h2>\n';
      (e.sections || []).forEach(function (sec) {
        h += '<div class="changelog-section">\n<div class="label">' + sec.label + '</div>\n';
        if (sec.text) h += '<p>' + sec.text + '</p>\n';
        if (sec.items) h += renderList({ items: sec.items, class: 'tight' }) + '\n';
        h += '</div>\n';
      });
      h += '</div>';
      return h;
    }).join('\n');
  }

  function renderCard(d) {
    var h = '<div class="card">\n';
    if (d.title) h += '<h2>' + d.title + '</h2>\n';
    if (d.subtitle) h += '<h3>' + d.subtitle + '</h3>\n';
    if (d.blocks) {
      d.blocks.forEach(function (b) { h += renderBlock(b) + '\n'; });
    }
    if (d.content) {
      h += (typeof d.content === 'string') ? d.content : renderBlock(d.content);
    }
    h += '</div>';
    return h;
  }

  /** Master dispatcher — turns a block descriptor into HTML. */
  function renderBlock(b) {
    if (!b) return '';
    switch (b.type) {
      case 'kpi-row':   return renderKPIRow(b);
      case 'table':     return renderTable(b);
      case 'sm-table':  return renderTable(b);   // uses same renderer; CSS class handled via d.class
      case 'list':      return renderList(b);
      case 'html':      return b.content || '';
      case 'card':      return renderCard(b);
      case 'heading':
        var lvl = b.level || 2;
        var st = b.style ? ' style="' + b.style + '"' : '';
        var id = b.id ? ' id="' + b.id + '"' : '';
        return '<h' + lvl + st + id + '>' + b.text + '</h' + lvl + '>';
      case 'paragraph':
        var pc = b.class ? ' class="' + b.class + '"' : '';
        var ps = b.style ? ' style="' + b.style + '"' : '';
        return '<p' + pc + ps + '>' + b.content + '</p>';
      case 'pre':
        return '<pre>' + (b.content || '') + '</pre>';
      case 'timeline':  return renderTimeline(b);
      case 'changelog': return renderChangelog(b);
      default:          return '';
    }
  }

  /* ================================================================
   *  Layout: nav + footer
   * ================================================================ */

  function renderNav(activeId) {
    var s = window.TECT_SITE;
    if (!s) return '';
    var h = '<div class="wrap">\n' +
      '<span class="brand"><a href="index.html">' + s.brand.name + '</a>' +
      '<span class="sub">' + s.brand.sub + '</span></span>\n<nav>\n';
    s.nav.forEach(function (n) {
      var c = (n.id === activeId) ? ' class="active"' : '';
      h += '<a href="' + n.href + '"' + c + '>' + n.label + '</a>\n';
    });
    h += '</nav>\n</div>';
    return h;
  }

  function renderFooter(data) {
    var h = '<div class="wrap">\n';
    if (data.footerNote) h += '<p>' + data.footerNote + '</p>\n';
    h += '<p class="timestamp">Last updated: ' + (data.lastUpdated || '—') + '</p>\n';
    h += '</div>';
    return h;
  }

  /* ================================================================
   *  Public API
   * ================================================================ */

  /**
   * TECT.render(pageId, pageData)
   *
   * Populates #site-header, #page-content, #site-footer from pageData,
   * then triggers MathJax re-typeset.
   *
   * pageData shape:
   *   {
   *     title:       "Page heading",          // → <h1>
   *     subtitle:    "muted sub-text",         // → <p class="muted">
   *     lastUpdated: "2026-04-18",
   *     footerNote:  "HTML string for footer",
   *     blocks:      [ ...block descriptors ]
   *   }
   */
  TECT.render = function (pageId, pageData) {
    var s = window.TECT_SITE || {};
    var banners = s.banners || {};

    // Top banner (above header)
    var topSlot = document.getElementById('site-banner-top');
    if (!topSlot && banners.top) {
      topSlot = document.createElement('div');
      topSlot.id = 'site-banner-top';
      topSlot.className = 'site-banner site-banner-top';
      var hdr0 = document.getElementById('site-header');
      if (hdr0 && hdr0.parentNode) hdr0.parentNode.insertBefore(topSlot, hdr0);
    }
    if (topSlot) topSlot.innerHTML = banners.top || '';
    if (topSlot && !banners.top) topSlot.style.display = 'none';

    // Header
    var hdr = document.getElementById('site-header');
    if (hdr) hdr.innerHTML = renderNav(pageId);

    // Main content
    var main = document.getElementById('page-content');
    if (main && pageData) {
      var html = '';
      if (pageData.title) html += '<h1>' + pageData.title + '</h1>\n';
      if (pageData.subtitle) html += '<p class="muted">' + pageData.subtitle + '</p>\n';
      if (pageData.blocks) {
        pageData.blocks.forEach(function (b) { html += renderBlock(b) + '\n'; });
      }
      main.innerHTML = html;
    }

    // Footer
    var ftr = document.getElementById('site-footer');
    if (ftr && pageData) ftr.innerHTML = renderFooter(pageData);

    // Bottom banner (below footer)
    var botSlot = document.getElementById('site-banner-bottom');
    if (!botSlot && banners.bottom) {
      botSlot = document.createElement('div');
      botSlot.id = 'site-banner-bottom';
      botSlot.className = 'site-banner site-banner-bottom';
      if (ftr && ftr.parentNode) ftr.parentNode.insertBefore(botSlot, ftr.nextSibling);
    }
    if (botSlot) botSlot.innerHTML = banners.bottom || '';
    if (botSlot && !banners.bottom) botSlot.style.display = 'none';

    // MathJax re-typeset (MathJax 3 async API)
    if (window.MathJax) {
      if (window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise().catch(function (e) {
          console.warn('MathJax typeset:', e);
        });
      } else if (window.MathJax.startup && window.MathJax.startup.promise) {
        // MathJax not yet ready — wait for startup, then typeset
        window.MathJax.startup.promise.then(function () {
          return MathJax.typesetPromise();
        }).catch(function (e) {
          console.warn('MathJax typeset (deferred):', e);
        });
      }
    }
  };

  // Expose helpers for pages that need custom rendering
  TECT.helpers = {
    tag: tag,
    cell: cell,
    renderBlock: renderBlock,
    renderTable: renderTable,
    renderCard: renderCard,
    renderList: renderList,
    renderTimeline: renderTimeline,
    renderChangelog: renderChangelog
  };

})();
