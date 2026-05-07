/* DEPRECATED 2026-05-07: states.js has been renamed to status.js.
 * No HTML page loads this file any more; states.html now redirects to
 * status.html which loads data/status.js. This stub is kept only so that
 * any cached external bookmark to data/states.js does not 404 — it does
 * not define window.TECT_STATES and will be removed after one snapshot
 * cycle. Load Website/data/status.js for the live scoreboard. */
(function () {
  if (typeof console !== 'undefined' && console.warn) {
    console.warn('TECT: data/states.js is deprecated; the canonical file is data/status.js.');
  }
})();
