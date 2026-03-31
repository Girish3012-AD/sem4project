document.addEventListener('DOMContentLoaded', () => {
  const calendar = document.getElementById('academicCalendar');
  if (!calendar) {
    return;
  }

  const dayButtons = calendar.querySelectorAll('.js-calendar-day');
  const detailTitle = document.getElementById('calendarDetailTitle');
  const detailSubtitle = document.getElementById('calendarDetailSubtitle');
  const detailList = document.getElementById('calendarDetailList');

  const renderEvents = (dateLabel, events) => {
    if (!detailTitle || !detailSubtitle || !detailList) {
      return;
    }

    detailTitle.textContent = dateLabel;
    detailSubtitle.textContent = `${events.length} item${events.length === 1 ? '' : 's'} scheduled for the selected date.`;

    if (!events.length) {
      detailList.innerHTML = `
        <div class="empty-state empty-state--compact">
          <h3>No scheduled items</h3>
          <p>Select another date to inspect the semester calendar in more detail.</p>
        </div>
      `;
      return;
    }

    detailList.innerHTML = '';
    events.forEach((eventItem) => {
      const item = document.createElement('article');
      item.className = 'calendar-detail-item';
      item.innerHTML = `
        <div class="calendar-detail-item__top">
          <span class="badge ${eventItem.tone}">${eventItem.type_label}</span>
        </div>
        <h3></h3>
        <p></p>
      `;
      item.querySelector('h3').textContent = eventItem.title;
      item.querySelector('p').textContent = eventItem.detail;
      detailList.appendChild(item);
    });
  };

  dayButtons.forEach((button) => {
    button.addEventListener('click', () => {
      dayButtons.forEach((day) => day.classList.remove('is-selected'));
      button.classList.add('is-selected');

      let events = [];
      try {
        events = JSON.parse(button.dataset.events || '[]');
      } catch (error) {
        events = [];
      }

      renderEvents(button.dataset.dateLabel, events);
    });
  });
});
