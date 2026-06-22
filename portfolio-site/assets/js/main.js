document.addEventListener("DOMContentLoaded", () => {
  const yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  const navToggle = document.querySelector(".nav-toggle");
  const navList = document.getElementById("nav-menu");

  if (navToggle && navList) {
    navToggle.addEventListener("click", () => {
      const isOpen = navList.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    navList.addEventListener("click", (event) => {
      const target = event.target;
      if (target instanceof HTMLAnchorElement && target.getAttribute("href")?.startsWith("#")) {
        navList.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLAnchorElement)) {
        return;
      }

      const hash = target.getAttribute("href");
      if (!hash) {
        return;
      }

      const section = document.querySelector(hash);
      if (!section) {
        return;
      }

      event.preventDefault();
      section.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
});

