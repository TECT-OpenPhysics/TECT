/**
 * papers-render.js — Rich paper-card rendering for TECT papers.
 *
 * Enhanced with:
 * - Per-paper abstracts/descriptions
 * - Math note citations (clickable links to GitHub)
 * - Tier badges (colour-coded)
 * - PDF download and view buttons
 *
 * Exports:
 *   TECT.renderPaperGrid(containerId, papers, category, title, subtitle)
 *     Renders a paper card grid filtered by category.
 *     Each card shows: tier badge, title, description, Math note links, PDF buttons
 */
(function () {
  'use strict';

  var TECT = window.TECT = window.TECT || {};

  function escapeHtml(text) {
    if (!text) return '';
    var map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    };
    return String(text).replace(/[&<>"']/g, function (c) { return map[c]; });
  }

  function categoryLabel(cat) {
    var labels = {
      'auxiliary': 'Auxiliary',
      'epochs': 'Epoch Series',
      'top_impact': 'Top Impact',
      'papers': 'Papers'
    };
    return labels[cat] || cat;
  }

  function categoryDescr(cat) {
    var descrs = {
      'auxiliary': 'Supporting calculations, anomaly-cancellation notes, mechanism studies',
      'epochs': 'Epoch-track papers documenting intermediate-closure progress',
      'top_impact': 'High-impact results: TOE structure, Cartan forcing, F-GAP closure',
      'papers': 'Main-track Pillar papers (Pillars 1–11)'
    };
    return descrs[cat] || '';
  }

  /**
   * Convert a Math note ID (e.g., "Math82-AddD") to a GitHub blob URL
   */
  function mathNoteUrl(mathId) {
    // Map "Math82-AddD" -> "TECT-Math82-Addendum-D" or similar
    // For now, construct a search-friendly link
    var filename = 'TECT-' + mathId.replace('-', '-').replace(/AddD/, 'Addendum-D')
      .replace(/AddC/, 'Addendum-C').replace(/AddB/, 'Addendum-B')
      .replace(/AddA/, 'Addendum-A');
    // Use a wildcard search on GitHub
    return 'https://github.com/TECT-OpenPhysics/TECT/search?q=' + encodeURIComponent(mathId) + '&type=code';
  }

  /**
   * Render a single paper card with description and Math notes
   */
  function renderPaperCard(paper) {
    var tierClass = 'tier-' + (paper.tier || 'q');
    
    // Build Math notes HTML
    var mathNotesHtml = '';
    if (paper.math_notes && paper.math_notes.length > 0) {
      mathNotesHtml = '<div class="paper-card-math-notes">\n' +
        '  <span class="math-notes-label">Math foundation:</span>\n' +
        '  <span class="math-notes-list">\n';
      
      // Show first 5, collapse rest
      var toShow = paper.math_notes.slice(0, 5);
      toShow.forEach(function (note) {
        mathNotesHtml += '    <a href="' + escapeHtml(mathNoteUrl(note)) + '" class="math-note-tag" title="Link to ' + escapeHtml(note) + '">' + 
          escapeHtml(note) + '</a>\n';
      });
      
      if (paper.math_notes.length > 5) {
        mathNotesHtml += '    <span class="math-notes-more" title="' + escapeHtml(paper.math_notes.slice(5).join(', ')) + '">+' +
          (paper.math_notes.length - 5) + ' more</span>\n';
      }
      
      mathNotesHtml += '  </span>\n' +
        '</div>\n';
    }

    // Build PDF buttons
    var pdfButtonsHtml = '<div class="paper-card-buttons">\n';
    
    // Download button (use raw GitHub URL)
    var downloadUrl = paper.url.replace('/blob/', '/raw/').replace(/\/main\//, '/main/');
    pdfButtonsHtml += '  <a class="btn btn-download" href="' + escapeHtml(downloadUrl) + '" download>\n' +
      '    <span>⬇ Download</span> <span class="file-size">(' + escapeHtml(paper.kb) + ' KB)</span>\n' +
      '  </a>\n';
    
    // View button (GitHub viewer)
    var viewUrl = 'https://github.com/TECT-OpenPhysics/TECT/blob/main/papers/' +
      escapeHtml(paper.url.split('papers/')[1]);
    pdfButtonsHtml += '  <a class="btn btn-view" href="' + escapeHtml(viewUrl) + '" target="_blank">\n' +
      '    <span>📄 View on GitHub</span>\n' +
      '  </a>\n';
    
    pdfButtonsHtml += '</div>\n';

    var html = '<div class="paper-card">\n' +
      '  <div class="paper-card-head">\n' +
      '    <span class="tier-badge ' + tierClass + '" title="Canonical tier per Docs/status/TOE-FACT-SHEET.md">' + 
        escapeHtml(paper.tier || '?') + '</span>\n' +
      '    <span class="stem">' + escapeHtml(paper.stem) + '</span>\n' +
      '  </div>\n' +
      '  <div class="paper-card-title">' + escapeHtml(paper.title) + '</div>\n' +
      '  <div class="paper-card-description">\n' +
      '    ' + escapeHtml(paper.description || 'No description available.') + '\n' +
      '  </div>\n' +
      mathNotesHtml +
      pdfButtonsHtml +
      '</div>\n';
    
    return html;
  }

  /**
   * Render filtered paper grid
   */
  TECT.renderPaperGrid = function (containerId, papers, category, title, subtitle) {
    if (!papers || !Array.isArray(papers)) {
      console.error('TECT.renderPaperGrid: invalid papers array');
      return;
    }

    var filtered = papers;
    if (category) {
      filtered = papers.filter(function (p) { return p.category === category; });
    }

    var container = document.getElementById(containerId);
    if (!container) {
      console.error('TECT.renderPaperGrid: container not found: ' + containerId);
      return;
    }

    var html = '';

    // Optional header
    if (title) {
      html += '<h1>' + escapeHtml(title) + '</h1>\n';
    }
    if (subtitle) {
      html += '<p class="pdf-summary">' + escapeHtml(subtitle) + '</p>\n';
    }

    // Category info
    if (category) {
      html += '<div class="pdf-cat">\n' +
        '<h3>' + escapeHtml(categoryLabel(category)) + '</h3>\n' +
        '<p class="pdf-cat-sub">' + escapeHtml(categoryDescr(category)) + '</p>\n' +
        '<div class="papers-grid">\n';
    } else {
      html += '<div class="papers-grid">\n';
    }

    // Cards
    filtered.forEach(function (paper) {
      html += renderPaperCard(paper);
    });

    html += '</div>\n';

    // Back link
    if (category) {
      html += '<div style="margin-top: 2em; text-align: center;">\n' +
        '<a href="papers.html">← Back to Papers overview</a>\n' +
        '</div>\n';
    }

    container.innerHTML = html;
  };

  /**
   * Render 4-category landing page
   */
  TECT.renderPapersLanding = function (containerId, papers) {
    if (!papers || !Array.isArray(papers)) {
      console.error('TECT.renderPapersLanding: invalid papers array');
      return;
    }

    var container = document.getElementById(containerId);
    if (!container) {
      console.error('TECT.renderPapersLanding: container not found: ' + containerId);
      return;
    }

    var categories = ['papers', 'auxiliary', 'epochs', 'top_impact'];
    var counts = {};
    categories.forEach(function (cat) {
      counts[cat] = papers.filter(function (p) { return p.category === cat; }).length;
    });

    var html = '<div class="papers-landing">\n' +
      '<p class="pdf-summary">TECT papers are organized in four publication tracks.</p>\n' +
      '<div class="landing-grid">\n';

    categories.forEach(function (cat) {
      var count = counts[cat];
      var pageFile = (cat === 'papers') ? 'papers-papers.html' : ('papers-' + cat + '.html');
      
      html += '<div class="landing-card">\n' +
        '<h3>' + escapeHtml(categoryLabel(cat)) + '</h3>\n' +
        '<p>' + escapeHtml(categoryDescr(cat)) + '</p>\n' +
        '<p style="margin-top: 0.8em; font-size: 0.95em; color: #666;">' +
        '<strong>' + count + '</strong> paper' + (count !== 1 ? 's' : '') +
        '</p>\n' +
        '<a href="' + escapeHtml(pageFile) + '" style="display: inline-block; margin-top: 0.8em; padding: 0.5em 1em; background: #2266aa; color: white; text-decoration: none; border-radius: 4px; font-size: 0.9em;">View all →</a>\n' +
        '</div>\n';
    });

    html += '</div>\n</div>\n';
    container.innerHTML = html;
  };

})();
