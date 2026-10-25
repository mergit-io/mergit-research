/* Enhancements for the paper pages. The pages read correctly without this file. */
(function () {
  "use strict";

  // Section links: a small "#" beside each heading, so a section can be cited by address.
  document.querySelectorAll("article section[id] > :is(h2, h3, h4)").forEach(function (h) {
    var a = document.createElement("a");
    a.className = "anchor";
    a.href = "#" + h.parentElement.id;
    a.setAttribute("aria-label", "Link to this section");
    a.textContent = "#";
    h.appendChild(a);
  });

  // Figures open full size in a new tab, because Figure 1 is wide.
  document.querySelectorAll("article figure img").forEach(function (img) {
    var link = document.createElement("a");
    link.href = img.getAttribute("src");
    link.target = "_blank";
    link.rel = "noopener";
    link.title = "Open the figure at full size";
    img.parentNode.insertBefore(link, img);
    link.appendChild(img);
  });

  // Contents rail: open on wide screens, closed on narrow ones; mark the section being read.
  var toc = document.querySelector("details.toc");
  var wide = window.matchMedia("(min-width: 64rem)");
  function syncToc() {
    if (toc) toc.open = wide.matches;
  }
  syncToc();
  if (wide.addEventListener) wide.addEventListener("change", syncToc);

  var links = Array.prototype.slice.call(document.querySelectorAll("details.toc a[href^='#']"));
  var byId = {};
  links.forEach(function (a) {
    byId[decodeURIComponent(a.getAttribute("href").slice(1))] = a;
  });
  var sections = Array.prototype.slice.call(document.querySelectorAll("article section[id]")).filter(function (s) {
    return byId[s.id];
  });

  function setCurrent(id) {
    links.forEach(function (a) {
      a.removeAttribute("aria-current");
      var li = a.parentElement;
      if (li) li.classList.remove("open");
    });
    var a = byId[id];
    if (!a) return;
    a.setAttribute("aria-current", "true");
    // Open this entry's children and its parent's, so the subsections around it are visible.
    var li = a.parentElement;
    while (li && li.tagName === "LI") {
      li.classList.add("open");
      li = li.parentElement && li.parentElement.parentElement;
    }
  }

  function update() {
    var current = null;
    var line = window.innerHeight * 0.25;
    for (var i = 0; i < sections.length; i += 1) {
      if (sections[i].getBoundingClientRect().top <= line) current = sections[i].id;
      else break;
    }
    if (current) setCurrent(current);
  }
  if (sections.length) {
    var ticking = false;
    window.addEventListener(
      "scroll",
      function () {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(function () {
          update();
          ticking = false;
        });
      },
      { passive: true }
    );
    update();
  }

  // "Check this PDF": hash the download in the browser and compare it with the printed fingerprint.
  // It shows that the file you were served matches the page. It does not prove who built either.
  document.querySelectorAll("button.check[data-url]").forEach(function (btn) {
    var out = btn.parentElement.querySelector(".check-out");
    btn.addEventListener("click", function () {
      if (!window.crypto || !window.crypto.subtle) {
        out.className = "check-out bad";
        out.textContent = "This browser cannot compute SHA-256 here.";
        return;
      }
      btn.disabled = true;
      out.className = "check-out";
      out.textContent = "Checking";
      fetch(btn.dataset.url, { cache: "no-store" })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.arrayBuffer();
        })
        .then(function (buf) {
          return crypto.subtle.digest("SHA-256", buf);
        })
        .then(function (digest) {
          var hex = Array.prototype.map
            .call(new Uint8Array(digest), function (b) {
              return b.toString(16).padStart(2, "0");
            })
            .join("");
          var ok = hex === btn.dataset.sha;
          out.className = "check-out " + (ok ? "ok" : "bad");
          out.textContent = ok ? "Matches the fingerprint above." : "Does not match the fingerprint above.";
        })
        .catch(function (e) {
          out.className = "check-out bad";
          out.textContent = "Could not fetch the PDF (" + e.message + ").";
        })
        .then(function () {
          btn.disabled = false;
        });
    });
  });
})();
