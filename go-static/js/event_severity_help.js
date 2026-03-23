(function() {
    function initSeverityHelpTooltip() {
        const label = document.querySelector('label[for="id_ifrc_severity_level"]');
        if (!label) {
            return;
        }

        const helpIcon = label.querySelector('.ifrc-severity-help-icon');
        const tooltip = label.querySelector('.ifrc-severity-help-tooltip');
        if (!helpIcon || !tooltip) {
            return;
        }

        label.style.position = 'relative';

        helpIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const shouldShow = !tooltip.classList.contains('visible');
            document.querySelectorAll('.cc-help-tooltip.visible').forEach(function(openTooltip) {
                openTooltip.classList.remove('visible');
            });
            tooltip.classList.toggle('visible', shouldShow);
        });

        document.addEventListener('click', function(e) {
            if (!label.contains(e.target)) {
                tooltip.classList.remove('visible');
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSeverityHelpTooltip);
    } else {
        initSeverityHelpTooltip();
    }
})();
