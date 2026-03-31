document.addEventListener('DOMContentLoaded', () => {
  const dashboard = document.getElementById('studentPerformanceDashboard');
  if (!dashboard || typeof Chart === 'undefined') {
    return;
  }

  const subjectUrl = dashboard.dataset.subjectUrl;
  const historyUrl = dashboard.dataset.historyUrl;

  const lineCanvas = document.getElementById('performanceTrendChart');
  const barCanvas = document.getElementById('subjectMarksChart');
  const pieCanvas = document.getElementById('strengthWeaknessChart');

  const updateSummary = (selector, value) => {
    document.querySelectorAll(`[data-summary="${selector}"]`).forEach((element) => {
      element.textContent = value;
    });
  };

  const createEmptyState = (canvas, title, message) => {
    const wrapper = canvas.parentElement;
    wrapper.innerHTML = `
      <div class="empty-state chart-empty">
        <h3>${title}</h3>
        <p>${message}</p>
      </div>
    `;
  };

  const statusColor = (status) => {
    if (status === 'Strong') {
      return '#10b981';
    }
    if (status === 'Weak') {
      return '#f43f5e';
    }
    return '#f59e0b';
  };

  const chartTextColor = '#475569';
  const chartGridColor = 'rgba(148, 163, 184, 0.18)';

  const fetchJson = async (url) => {
    const response = await fetch(url, {
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }

    return response.json();
  };

  const renderTrendChart = (history) => {
    if (!history.length) {
      createEmptyState(lineCanvas, 'No performance trend yet', 'Released assessments will appear here once result data is available.');
      return;
    }

    const context = lineCanvas.getContext('2d');
    const gradient = context.createLinearGradient(0, 0, 0, 320);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.26)');
    gradient.addColorStop(1, 'rgba(79, 70, 229, 0.02)');

    new Chart(context, {
      type: 'line',
      data: {
        labels: history.map((entry) => entry.date_label),
        datasets: [
          {
            label: 'Score (%)',
            data: history.map((entry) => entry.percentage),
            borderColor: '#4f46e5',
            backgroundColor: gradient,
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#4f46e5',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            padding: 12,
            callbacks: {
              title: (items) => {
                const point = history[items[0].dataIndex];
                return `${point.exam_name} · ${point.subject_name}`;
              },
              label: (item) => {
                const point = history[item.dataIndex];
                return `Score: ${point.percentage}% (${point.marks_obtained}/${point.max_marks})`;
              },
              afterLabel: (item) => `Type: ${history[item.dataIndex].exam_type}`,
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: chartTextColor,
            },
            grid: {
              color: chartGridColor,
            },
          },
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              color: chartTextColor,
              callback: (value) => `${value}%`,
            },
            grid: {
              color: chartGridColor,
            },
          },
        },
      },
    });
  };

  const renderBarChart = (subjects) => {
    if (!subjects.length) {
      createEmptyState(barCanvas, 'No subject comparison yet', 'Average subject scores will appear here once released marks are available.');
      return;
    }

    new Chart(barCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: subjects.map((subject) => subject.subject_name),
        datasets: [
          {
            label: 'Average Score (%)',
            data: subjects.map((subject) => subject.average_percentage),
            backgroundColor: subjects.map((subject) => statusColor(subject.status)),
            borderRadius: 14,
            maxBarThickness: 44,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            padding: 12,
            callbacks: {
              label: (item) => {
                const subject = subjects[item.dataIndex];
                return `Average score: ${subject.average_percentage}%`;
              },
              afterLabel: (item) => {
                const subject = subjects[item.dataIndex];
                return [`Average marks: ${subject.average_marks}`, `Trend: ${subject.trend}`];
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: chartTextColor,
            },
            grid: {
              display: false,
            },
          },
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              color: chartTextColor,
              callback: (value) => `${value}%`,
            },
            grid: {
              color: chartGridColor,
            },
          },
        },
      },
    });
  };

  const renderPieChart = (subjects) => {
    if (!subjects.length) {
      createEmptyState(pieCanvas, 'No strength breakdown yet', 'The strengths versus weaknesses split needs released marks data.');
      return;
    }

    new Chart(pieCanvas.getContext('2d'), {
      type: 'pie',
      data: {
        labels: subjects.map((subject) => subject.subject_name),
        datasets: [
          {
            data: subjects.map((subject) => subject.average_percentage),
            backgroundColor: subjects.map((subject) => statusColor(subject.status)),
            borderColor: '#ffffff',
            borderWidth: 2,
            hoverOffset: 18,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          animateRotate: true,
          duration: 900,
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: chartTextColor,
              usePointStyle: true,
              padding: 16,
            },
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.92)',
            padding: 12,
            callbacks: {
              title: (items) => subjects[items[0].dataIndex].subject_name,
              label: (item) => {
                const subject = subjects[item.dataIndex];
                return `Average marks: ${subject.average_marks}`;
              },
              afterLabel: (item) => {
                const subject = subjects[item.dataIndex];
                return `Status: ${subject.status}`;
              },
            },
          },
        },
      },
    });
  };

  Promise.all([fetchJson(subjectUrl), fetchJson(historyUrl)])
    .then(([subjectResponse, historyResponse]) => {
      updateSummary('overall-average', `${subjectResponse.summary.overall_average_percentage}%`);
      updateSummary('strong-count', subjectResponse.summary.strong_count);
      updateSummary('weak-count', subjectResponse.summary.weak_count);

      renderTrendChart(historyResponse.history || []);
      renderBarChart(subjectResponse.subjects || []);
      renderPieChart(subjectResponse.subjects || []);
    })
    .catch(() => {
      createEmptyState(lineCanvas, 'Unable to load trend data', 'Please refresh the page to retry loading the performance chart.');
      createEmptyState(barCanvas, 'Unable to load subject data', 'Please refresh the page to retry loading the comparison chart.');
      createEmptyState(pieCanvas, 'Unable to load breakdown data', 'Please refresh the page to retry loading the strengths versus weaknesses chart.');
    });
});
