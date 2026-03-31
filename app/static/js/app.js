document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const sidebarToggles = document.querySelectorAll('[data-sidebar-toggle]');
  const sidebarOverlay = document.querySelector('.js-sidebar-overlay');
  const notification = document.querySelector('.js-notification');
  const notificationToggle = document.querySelector('.js-notification-toggle');
  const flashes = document.querySelectorAll('.flash');
  const sidebarKey = 'academiapro-sidebar-collapsed';
  const mobileQuery = window.matchMedia('(max-width: 960px)');

  const closeSidebar = () => {
    body.classList.remove('sidebar-open');
  };

  const syncSidebarState = () => {
    if (mobileQuery.matches) {
      body.classList.remove('sidebar-collapsed');
      closeSidebar();
      return;
    }

    const collapsed = window.localStorage.getItem(sidebarKey) === 'true';
    body.classList.toggle('sidebar-collapsed', collapsed);
  };

  sidebarToggles.forEach((toggle) => {
    toggle.addEventListener('click', () => {
      if (mobileQuery.matches) {
        body.classList.toggle('sidebar-open');
        return;
      }

      const nextCollapsed = !body.classList.contains('sidebar-collapsed');
      body.classList.toggle('sidebar-collapsed', nextCollapsed);
      window.localStorage.setItem(sidebarKey, String(nextCollapsed));
    });
  });

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  if (notification && notificationToggle) {
    const closeNotifications = () => {
      notification.classList.remove('is-open');
      notificationToggle.setAttribute('aria-expanded', 'false');
    };

    notificationToggle.addEventListener('click', (event) => {
      event.stopPropagation();
      const isOpen = notification.classList.toggle('is-open');
      notificationToggle.setAttribute('aria-expanded', String(isOpen));
    });

    document.addEventListener('click', (event) => {
      if (!notification.contains(event.target)) {
        closeNotifications();
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        closeNotifications();
        closeSidebar();
      }
    });
  }

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const submitButton = form.querySelector('button[type="submit"]');
      if (!submitButton || submitButton.classList.contains('is-loading')) {
        return;
      }

      const originalLabel = submitButton.textContent.trim();
      submitButton.dataset.originalLabel = originalLabel;
      submitButton.classList.add('is-loading');
      submitButton.disabled = true;
      submitButton.innerHTML = '<span class="button-spinner" aria-hidden="true"></span><span>Processing...</span>';

      window.setTimeout(() => {
        if (!document.body.contains(submitButton)) {
          return;
        }

        submitButton.disabled = false;
        submitButton.classList.remove('is-loading');
        submitButton.textContent = originalLabel;
      }, 8000);
    });
  });

  if (flashes.length) {
    window.setTimeout(() => {
      flashes.forEach((flash) => {
        flash.style.opacity = '0';
        flash.style.transform = 'translateY(-6px)';
        flash.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
        window.setTimeout(() => flash.remove(), 260);
      });
    }, 4000);
  }

  document.querySelectorAll('.js-print-report').forEach((button) => {
    button.addEventListener('click', () => {
      window.print();
    });
  });

  syncSidebarState();
  window.addEventListener('resize', syncSidebarState);
});
