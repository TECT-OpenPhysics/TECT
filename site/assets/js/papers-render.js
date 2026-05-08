/**
 * papers-render.js — Category-filtered PDF grid rendering for TECT papers.
 *
 * Exports:
 *   TECT.renderPaperGrid(containerId, papers, category, title, subtitle)
 *     Renders a PDF card grid filtered by category into the given container.
 *     category: "auxiliary" | "epochs" | "top_impact" | "papers" | null (all)
 *     title, subtitle: optional page header strings
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
   * Render a single PDF card
   */
  function renderPdfCard(paper) {
    var tierClass = 'tier-' + (paper.tier || 'q');
    var html = '<div class="pdf-card">\n' +
      '  <div class="pdf-card-head">\n' +
      '    <span class="tier-badge ' + tierClass + '">' + escapeHtml(paper.tier || '?') + '</span>\n' +
      '    <span class="stem">' + escapeHtml(paper.stem) + '</span>\n' +
      '  </div>\n' +
      '  <div class="ttl">' + escapeHtml(paper.title) + '</div>\n' +
      '  <div class="pdf-card-foot">\n' +
      '    <span class="meta">' + escapeHtml(paper.kb + ' KB') + '</span>\n' +
      '    <a class="dl" href="' + escapeHtml(paper.url) + '" download>Download PDF</a>\n' +
      '  </div>\n' +
      '</div>\n';
    return html;
  }

  /**
   * Render filtered PDF grid
   *   papers: array of paper objects (from papers_pdf_index.js)
   *   category: filter string (or null for all)
   *   title, subtitle: optional header strings
   *   containerId: DOM element id where to render
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

    // Filter info
    if (category) {
      html += '<div class="pdf-cat">\n' +
        '<h3>' + escapeHtml(categoryLabel(category)) + '</h3>\n' +
        '<p class="pdf-cat-sub">' + escapeHtml(categoryDescr(category)) + '</p>\n' +
        '<div class="pdf-grid">\n';
    } else {
      html += '<div class="pdf-grid">\n';
    }

    // Cards
    filtered.forEach(function (paper) {
      html += renderPdfCard(paper);
    });

    html += '</div>\n';

    // Back link (if filtered)
    if (category) {
      html += '<div style="margin-top: 2em; text-align: center;">\n' +
        '<a href="papers.html">← Back to Papers overview</a>\n' +
        '</div>\n';
    }

    container.innerHTML = html;
  };

  /**
   * Render 4-category landing page grid
   *   papers: array of paper objects
   *   containerId: DOM element id
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

    var categories = ['auxiliary', 'epochs', 'top_impact', 'papers'];
    var counts = {};
    categories.forEach(function (cat) {
      counts[cat] = papers.filter(function (p) { return p.category === cat; }).length;
    });

    var html = '<div class="papers-landing">\n' +
      '<p class="pdf-summary">TECT papers are organized in four publication tracks.</p>\n' +
      '<div class="pdf-grid">\n';

    categories.forEach(function (cat) {
      var count = counts[cat];
      html += '<div class="papers-landing-card">\n' +
        '<h3>' + escapeHtml(categoryLabel(cat)) + '</h3>\n' +
        '<p>' + escapeHtml(categoryDescr(cat)) + '</p>\n' +
        '<p style="margin-top: 0.8em; font-size: 0.95em; color: #666;">' +
        '<strong>' + count + '</strong> paper' + (count !== 1 ? 's' : '') +
        '</p>\n' +
        '<a href="papers-' + escapeHtml(cat === 'papers' ? 'papers' : cat) + '.html" style="display: inline-block; margin-top: 0.8em; padding: 0.5em 1em; background: #2266aa; color: white; text-decoration: none; border-radius: 4px; font-size: 0.9em;">View all →</a>\n' +
        '</div>\n';
    });

    html += '</div>\n</div>\n';
    container.innerHTML = html;
  };

})();
