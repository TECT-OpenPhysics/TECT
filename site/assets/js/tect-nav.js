/* AUTO-INJECT site navigation helpers (back-to-top + future nav widgets).
 * No build step; loaded by every TECT page that includes this script.
 */
(function() {
  'use strict';

  // Avoid double-injection if multiple pages include this script
  if (window.__tect_nav_loaded) return;
  window.__tect_nav_loaded = true;

  // --- Inject style once -------------------------------------------------
  var style = document.createElement('style');
  style.textContent =
    '#tect-back-to-top {' +
    '  position: fixed; right: 1.4em; bottom: 1.4em; z-index: 9999;' +
    '  width: 2.6em; height: 2.6em; border-radius: 50%; ' +
    '  background: #2266aa; color: white; border: none;' +
    '  font-size: 1.3em; line-height: 1;' +
    '  display: none; align-items: center; justify-content: center;' +
    '  cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.18);' +
    '  transition: transform 0.15s ease, background 0.15s ease, opacity 0.2s ease;' +
    '  opacity: 0.85;' +
    '}' +
    '#tect-back-to-top:hover {' +
    '  background: #1a4f85; transform: translateY(-2px); opacity: 1.0;' +
    '}' +
    '#tect-back-to-top:focus { outline: 2px solid #ffd34d; outline-offset: 2px; }' +
    '#tect-back-to-top.visible { display: flex; }' +
    '@media (max-width: 480px) {' +
    '  #tect-back-to-top { right: 0.9em; bottom: 0.9em; width: 2.4em; height: 2.4em; }' +
    '}';
  document.head.appendChild(style);

  // --- Inject button once ------------------------------------------------
  function injectButton() {
    if (document.getElementById('tect-back-to-top')) return;
    var btn = document.createElement('button');
    btn.id = 'tect-back-to-top';
    btn.type = 'button';
    btn.title = 'Back to top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '&uarr;';
    btn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.body.appendChild(btn);

    // Visibility toggle on scroll
    var threshold = 300;
    var ticking = false;
    function onScroll() {
      if (!ticking) {
        window.requestAnimationFrame(function() {
          var y = window.scrollY || document.documentElement.scrollTop || 0;
          if (y > threshold) {
            btn.classList.add('visible');
          } else {
            btn.classList.remove('visible');
          }
          ticking = false;
        });
        ticking = true;
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // initial check
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectButton);
  } else {
    injectButton();
  }
})();
