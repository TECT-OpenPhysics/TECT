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
    // GitHub file finder pre-filtered by Math note ID. The user can
    // press Enter on the highlighted result to open the file.
    // Works regardless of the full filename slug.
    return 'https://github.com/TECT-OpenPhysics/TECT/find/main?q=' +
      encodeURIComponent(mathId);
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

    // Build PDF buttons.
    // Public mirror layout (mirror.json v3 + paper_flatten_pdf_only=true):
    //   Docs/papers/<cat>/<stem>/<stem>.pdf  ->  paper/<stem>.pdf
    // So the canonical GitHub URLs are uniformly paper/<stem>.pdf.
    var pdfButtonsHtml = '<div class="paper-card-buttons">\n';

    var stem = paper.stem || '';
    var ghBlob = 'https://github.com/TECT-OpenPhysics/TECT/blob/main/paper/' + stem + '.pdf';
    var ghRaw  = 'https://github.com/TECT-OpenPhysics/TECT/raw/main/paper/' + stem + '.pdf';

    // Download button (raw GitHub URL — direct PDF download)
    pdfButtonsHtml += '  <a class="btn btn-download" href="' + escapeHtml(ghRaw) + '" download>\n' +
      '    <span>⬇ Download</span> <span class="file-size">(' + escapeHtml(paper.kb) + ' KB)</span>\n' +
      '  </a>\n';

    // View button (GitHub blob viewer — renders PDF inline)
    pdfButtonsHtml += '  <a class="btn btn-view" href="' + escapeHtml(ghBlob) + '" target="_blank">\n' +
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

    var categories = ['papers', 'top_impact', 'auxiliary', 'epochs'];

    // Category-specific metadata: icon + accent color + tier breakdown.
    var meta = {
      'papers': {
        icon: '⛰',
        accent: '#1a4d88',
        bg: 'linear-gradient(135deg, #f4f8fc 0%, #e8f0fa 100%)',
        order: 1,
        tagline: 'Eleven emergence pillars'
      },
      'top_impact': {
        icon: '★',
        accent: '#b88112',
        bg: 'linear-gradient(135deg, #fdf8ed 0%, #f7eed4 100%)',
        order: 2,
        tagline: 'High-leverage results'
      },
      'auxiliary': {
        icon: '⚙',
        accent: '#3e7a4a',
        bg: 'linear-gradient(135deg, #f4faf6 0%, #e6f1eb 100%)',
        order: 3,
        tagline: 'Supporting calculations'
      },
      'epochs': {
        icon: '⌛',
        accent: '#7a4a8e',
        bg: 'linear-gradient(135deg, #f9f4fc 0%, #efe4f7 100%)',
        order: 4,
        tagline: 'Intermediate-closure progress'
      }
    };

    // Build per-category {count, tierBreakdown[]}
    var stats = {};
    categories.forEach(function (cat) {
      var papersInCat = papers.filter(function (p) { return p.category === cat; });
      var tiers = {};
      papersInCat.forEach(function (p) {
        var t = p.tier || '?';
        tiers[t] = (tiers[t] || 0) + 1;
      });
      stats[cat] = { count: papersInCat.length, tiers: tiers };
    });

    var totalPapers = papers.length;

    var html = '<div class="papers-landing">\n' +
      '<div class="papers-landing-hero">\n' +
      '<h2 style="margin: 0 0 0.4em 0; font-size: 1.5em;">TECT papers</h2>\n' +
      '<p class="pdf-summary" style="margin: 0;">' + totalPapers +
      ' papers organised in four publication tracks. ' +
      'Click any track to browse its papers with abstracts, Math-note dependencies, ' +
      'and direct PDF download.</p>\n' +
      '</div>\n' +
      '<div class="landing-grid">\n';

    categories.forEach(function (cat) {
      var s = stats[cat];
      var m = meta[cat];
      var pageFile = (cat === 'papers') ? 'papers-papers.html' : ('papers-' + cat + '.html');

      // Tier mini-badges (sorted T7..T0)
      var tierKeys = Object.keys(s.tiers).sort(function (a, b) { return b.localeCompare(a); });
      var tierBadges = '';
      tierKeys.forEach(function (t) {
        var cls = 'tier-' + (t.match(/^T[0-7]$/) ? t : 'q');
        tierBadges += '<span class="tier-badge ' + cls + '" ' +
          'style="font-size: 0.72em; padding: 0.15em 0.45em; min-width: 2.4em;" ' +
          'title="' + escapeHtml(s.tiers[t]) + ' paper(s) at tier ' + escapeHtml(t) + '">' +
          escapeHtml(t) + ' ×' + s.tiers[t] + '</span>\n';
      });

      html += '<a class="landing-card-link" href="' + escapeHtml(pageFile) + '" ' +
        'style="text-decoration: none; color: inherit; display: block;">\n' +
        '<div class="landing-card" ' +
        'style="background: ' + m.bg + '; border-left: 4px solid ' + m.accent + '; ' +
        'transition: box-shadow 0.2s, transform 0.2s;" ' +
        'onmouseover="this.style.boxShadow=\'0 4px 16px rgba(0,0,0,0.10)\';this.style.transform=\'translateY(-2px)\';" ' +
        'onmouseout="this.style.boxShadow=\'\';this.style.transform=\'\';">' +
        '<div style="display: flex; align-items: center; gap: 0.7em; margin-bottom: 0.4em;">' +
        '<span style="font-size: 1.6em; color: ' + m.accent + ';">' + m.icon + '</span>' +
        '<h3 style="margin: 0; font-size: 1.15em; color: ' + m.accent + ';">' +
        escapeHtml(categoryLabel(cat)) + '</h3>' +
        '<span style="margin-left: auto; font-weight: 700; color: ' + m.accent + '; ' +
        'font-size: 1.4em;">' + s.count + '</span>' +
        '</div>\n' +
        '<p style="margin: 0 0 0.5em 0; font-size: 0.86em; font-weight: 500; color: ' + m.accent + ';">' +
        escapeHtml(m.tagline) + '</p>\n' +
        '<p style="margin: 0; color: #555; font-size: 0.92em; line-height: 1.5;">' +
        escapeHtml(categoryDescr(cat)) + '</p>\n' +
        '<div style="margin-top: 0.9em; display: flex; flex-wrap: wrap; gap: 0.35em;">' +
        tierBadges + '</div>\n' +
        '<div style="margin-top: 0.9em; padding-top: 0.7em; border-top: 1px solid rgba(0,0,0,0.06); ' +
        'color: ' + m.accent + '; font-weight: 500; font-size: 0.92em;">' +
        'Browse all ' + s.count + ' →</div>\n' +
        '</div></a>\n';
    });

    html += '</div>\n</div>\n';
    container.innerHTML = html;
  };

})();
