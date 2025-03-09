// Main JavaScript file for Pain Management App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Pain level chart
    const painChartElement = document.getElementById('pain-chart');
    if (painChartElement) {
        const painData = JSON.parse(painChartElement.getAttribute('data-pain-levels'));
        const dates = JSON.parse(painChartElement.getAttribute('data-dates'));
        
        Plotly.newPlot('pain-chart', [{
            x: dates,
            y: painData,
            type: 'scatter',
            mode: 'lines+markers',
            marker: {
                color: '#0d6efd',
                size: 8
            },
            line: {
                color: '#0d6efd',
                width: 2
            }
        }], {
            title: 'Pain Level Over Time',
            xaxis: {
                title: 'Date'
            },
            yaxis: {
                title: 'Pain Level (1-10)',
                range: [0, 10]
            },
            margin: {
                l: 50,
                r: 20,
                t: 50,
                b: 50
            }
        });
    }

    // Mobility chart
    const mobilityChartElement = document.getElementById('mobility-chart');
    if (mobilityChartElement) {
        const mobilityData = JSON.parse(mobilityChartElement.getAttribute('data-mobility-levels'));
        const dates = JSON.parse(mobilityChartElement.getAttribute('data-dates'));
        
        Plotly.newPlot('mobility-chart', [{
            x: dates,
            y: mobilityData,
            type: 'scatter',
            mode: 'lines+markers',
            marker: {
                color: '#28a745',
                size: 8
            },
            line: {
                color: '#28a745',
                width: 2
            }
        }], {
            title: 'Mobility Percentage Over Time',
            xaxis: {
                title: 'Date'
            },
            yaxis: {
                title: 'Mobility (%)',
                range: [0, 100]
            },
            margin: {
                l: 50,
                r: 20,
                t: 50,
                b: 50
            }
        });
    }

    // Medication adherence chart
    const medicationChartElement = document.getElementById('medication-chart');
    if (medicationChartElement) {
        const takenData = JSON.parse(medicationChartElement.getAttribute('data-taken'));
        const missedData = JSON.parse(medicationChartElement.getAttribute('data-missed'));
        const medications = JSON.parse(medicationChartElement.getAttribute('data-medications'));
        
        Plotly.newPlot('medication-chart', [
            {
                x: medications,
                y: takenData,
                name: 'Taken',
                type: 'bar',
                marker: {
                    color: '#28a745'
                }
            },
            {
                x: medications,
                y: missedData,
                name: 'Missed',
                type: 'bar',
                marker: {
                    color: '#dc3545'
                }
            }
        ], {
            title: 'Medication Adherence',
            barmode: 'stack',
            xaxis: {
                title: 'Medication'
            },
            yaxis: {
                title: 'Count'
            },
            margin: {
                l: 50,
                r: 20,
                t: 50,
                b: 100
            }
        });
    }

    // Exercise completion chart
    const exerciseChartElement = document.getElementById('exercise-chart');
    if (exerciseChartElement) {
        const completedData = JSON.parse(exerciseChartElement.getAttribute('data-completed'));
        const missedData = JSON.parse(exerciseChartElement.getAttribute('data-missed'));
        const exercises = JSON.parse(exerciseChartElement.getAttribute('data-exercises'));
        
        Plotly.newPlot('exercise-chart', [
            {
                x: exercises,
                y: completedData,
                name: 'Completed',
                type: 'bar',
                marker: {
                    color: '#28a745'
                }
            },
            {
                x: exercises,
                y: missedData,
                name: 'Missed',
                type: 'bar',
                marker: {
                    color: '#dc3545'
                }
            }
        ], {
            title: 'Exercise Completion',
            barmode: 'stack',
            xaxis: {
                title: 'Exercise'
            },
            yaxis: {
                title: 'Count'
            },
            margin: {
                l: 50,
                r: 20,
                t: 50,
                b: 100
            }
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}); 