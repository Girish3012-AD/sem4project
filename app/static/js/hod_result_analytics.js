document.addEventListener('DOMContentLoaded', () => {
  const dashboard = document.getElementById('hodResultAnalyticsDashboard');
  if (!dashboard || typeof Chart === 'undefined') {
    return;
  }

  const overviewUrl = dashboard.dataset.overviewUrl;
  const trendsUrl = dashboard.dataset.trendsUrl;

  const subjectCanvas = document.getElementById('hodSubjectAverageChart');
  const passFailCanvas = document.getElementById('hodPassFailChart');
  const trendCanvas = document.getElementById('hodPerformanceTrendChart');
  const insightsContainer = document.getElementById('hodAnalyticsInsights');
  const weakSubjectsContainer = document.getElementById('hodWeakSubjects');
  const topPerformersTable = document.getElementById('hodTopPerformersTable');
  const weakSubjectsTable = document.getElementById('hodWeakSubjectsTable');

  const chartTextColor = '#475569';
  const chartGridColor = 'rgba(148, 163, 184, 0.18)';

  const createEmptyState = (canvas, title, message) => {
    const wrapper = canvas.parentElement;
    wrapper.innerHTML = `
      <div class="empty-state chart-empty">
        <h3>${title}</h3>
        <p>${message}</p>
      </div>
    `;
  };

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

  const updateSummaryValue = (key, value) => {
    document.querySelectorAll(`[data-analytics-summary="${key}"]`).forEach((element) => {
      element.textContent = value;
    });
  };

  const renderInsights = (insights) => {
    if (!insightsContainer) {
      return;
    }

    insightsContainer.innerHTML = '';
    if (!insights.length) {
      insightsContainer.innerHTML = `
        <div class="empty-state empty-state--compact">
          <h3>No insights yet</h3>
          <p>Insights will appear once marks data is available.</p>
        </div>
      `;
      return;
    }

    insights.forEach((insight) => {
      const item = document.createElement('article');
      item.className = 'insight-item';
      item.innerHTML = '<span class="insight-item__marker" aria-hidden="true"></span><p></p>';
      item.querySelector('p').textContent = insight;
      insightsContainer.appendChild(item);
    });
  };

  const renderWeakSubjectChips = (weakSubjects) => {
    if (!weakSubjectsContainer) {
      return;
    }

    weakSubjectsContainer.innerHTML = '';
    if (!weakSubjects.length) {
      weakSubjectsContainer.innerHTML = '<span class="badge badge-neutral">No weak subjects detected</span>';
      return;
    }

    weakSubjects.forEach((subject) => {
      const chip = document.createElement('span');
      chip.className = 'badge badge-risk';
      chip.textContent = `${subject.subject_name} ${subject.average_percentage}%`;
      weakSubjectsContainer.appendChild(chip);
    });
  };

  const renderTopPerformerTable = (performers) => {
    if (!topPerformersTable) {
      return;
    }

    topPerformersTable.innerHTML = '';
    performers.forEach((performer) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><strong>${performer.student_name}</strong></td>
        <td>${performer.roll_no}</td>
        <td>${performer.average_percentage}%</td>
        <td>${performer.total_marks}</td>
        <td>${performer.assessment_count}</td>
      `;
      topPerformersTable.appendChild(row);
    });
  };

  const renderWeakSubjectsTable = (subjects) => {
    if (!weakSubjectsTable) {
      return;
    }

    weakSubjectsTable.innerHTML = '';
    subjects.forEach((subject) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><strong>${subject.subject_name}</strong></td>
        <td>${subject.average_percentage}%</td>
        <td>${subject.student_count}</td>
        <td>${subject.assessment_count}</td>
      `;
      weakSubjectsTable.appendChild(row);
    });
  };

  const renderSubjectAverageChart = (subjects) => {
    if (!subjects.length) {
      createEmptyState(subjectCanvas, 'No subject averages yet', 'Marks data is required before subject averages can be visualized.');
      return;
    }

    new Chart(subjectCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: subjects.map((subject) => subject.subject_name),
        datasets: [
          {
            label: 'Average Score (%)',
            data: subjects.map((subject) => subject.average_percentage),
            backgroundColor: subjects.map((subject) => subject.status === 'Weak' ? '#f43f5e' : '#4f46e5'),
            borderRadius: 14,
            maxBarThickness: 42,
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
                return `Average: ${subject.average_percentage}%`;
              },
              afterLabel: (item) => {
                const subject = subjects[item.dataIndex];
                return [`Marks average: ${subject.average_marks}`, `Status: ${subject.status}`];
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

  const renderPassFailChart = (summary) => {
    const total = (summary.pass_count || 0) + (summary.fail_count || 0);
    if (!total) {
      createEmptyState(passFailCanvas, 'No pass/fail ratio yet', 'Pass and fail distribution will appear after marks are entered.');
      return;
    }

    new Chart(passFailCanvas.getContext('2d'), {
      type: 'pie',
      data: {
        labels: ['Pass', 'Fail'],
        datasets: [
          {
            data: [summary.pass_count, summary.fail_count],
            backgroundColor: ['#10b981', '#f43f5e'],
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
              label: (item) => {
                const value = item.raw;
                const ratio = total ? ((value / total) * 100).toFixed(2) : '0.00';
                return `${item.label}: ${value} (${ratio}%)`;
              },
            },
          },
        },
      },
    });
  };

  const renderTrendChart = (trends) => {
    if (!trends.length) {
      createEmptyState(trendCanvas, 'No performance trend yet', 'Trend analytics will appear after branch assessments have recorded marks.');
      return;
    }

    const context = trendCanvas.getContext('2d');
    const gradient = context.createLinearGradient(0, 0, 0, 320);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.24)');
    gradient.addColorStop(1, 'rgba(79, 70, 229, 0.03)');

    new Chart(context, {
      type: 'line',
      data: {
        labels: trends.map((item) => item.date_label),
        datasets: [
          {
            label: 'Average Score (%)',
            data: trends.map((item) => item.average_percentage),
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
              title: (items) => trends[items[0].dataIndex].exam_name,
              label: (item) => {
                const trend = trends[item.dataIndex];
                return `Average: ${trend.average_percentage}%`;
              },
              afterLabel: (item) => {
                const trend = trends[item.dataIndex];
                return [`Average marks: ${trend.average_marks}`, `Students: ${trend.student_count}`];
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

  Promise.all([fetchJson(overviewUrl), fetchJson(trendsUrl)])
    .then(([overview, trendResponse]) => {
      updateSummaryValue('pass-rate', `${overview.summary.pass_rate}%`);
      updateSummaryValue('subject-count', overview.summary.subject_count);
      updateSummaryValue('fail-count', overview.summary.fail_count);
      updateSummaryValue('overall-average', `${overview.summary.overall_average_percentage}%`);

      renderInsights(overview.insights || []);
      renderWeakSubjectChips(overview.weak_subjects || []);
      renderTopPerformerTable(overview.top_performers || []);
      renderWeakSubjectsTable(overview.weak_subjects || []);
      renderSubjectAverageChart(overview.subject_averages || []);
      renderPassFailChart(overview.summary || {});
      renderTrendChart(trendResponse.performance_trends || []);
    })
    .catch(() => {
      createEmptyState(subjectCanvas, 'Unable to load subject analytics', 'Please refresh the page to retry loading subject averages.');
      createEmptyState(passFailCanvas, 'Unable to load pass/fail analytics', 'Please refresh the page to retry loading the pass ratio.');
      createEmptyState(trendCanvas, 'Unable to load trend analytics', 'Please refresh the page to retry loading the trend line.');
    });
});
