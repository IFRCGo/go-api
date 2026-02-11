// Add custom HTML header row to Crisis Categorisation fieldsets
document.addEventListener('DOMContentLoaded', function() {
    // Minimal styling for injected icons/tooltips
    const style = document.createElement('style');
    style.textContent = `
        .external-link-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-left: 6px;
            vertical-align: middle;
            color: inherit;
            text-decoration: none;
            opacity: 0.85;
        }
        .external-link-icon:hover { opacity: 1; }
        .external-link-icon svg {
            width: 14px;
            height: 14px;
            fill: currentColor;
        }

        /* Field help icons color adjustment */
        .field-help-icon {
            color: #444 !important;
        }
        @media (prefers-color-scheme: dark) {
            .field-help-icon {
                color: #b0b0b0 !important;
            }
        }

        /* Position field tooltips below the icon */
        .field-help-tooltip {
            top: 100% !important;
            bottom: auto !important;
            margin-top: 8px !important;
        }

        /* Arrow adjustment for top-pointing (tooltip below) */
        .field-help-tooltip::before {
            top: -5px !important;
            bottom: auto !important;
            border-top: none !important;
            border-bottom: 5px solid #ccc !important;
        }

        @media (prefers-color-scheme: dark) {
            .field-help-tooltip::before {
                border-bottom-color: #1a1a1a !important;
            }
        }
    `;
    document.head.appendChild(style);

    const fieldsets = document.querySelectorAll('.change-form fieldset.module');

    const headerNodesByText = new Map();
    let escKeyHandlerAdded = false;

    // Target fieldsets that should have the custom header
    const targetHeaders = [
        '1. Pre-Crisis Vulnerability',
        '2. Crisis Complexity',
        '3. Scope & Scale',
        '4. Humanitarian Conditions',
        '5. Capacity & Response'
    ];

    function submitSaveAndContinue(fromNode) {
        const form =
            (fromNode && fromNode.closest && fromNode.closest('form')) ||
            document.getElementById('change-form') ||
            document.querySelector('form.change-form') ||
            document.querySelector('form[method="post"]');

        if (!form) {
            return;
        }

        const continueSubmit = form.querySelector(
            'input[type="submit"][name="_continue"], button[type="submit"][name="_continue"]'
        );

        // Prefer the actual admin submit control so any JS hooks / expected behavior is preserved.
        if (continueSubmit) {
            if (typeof form.requestSubmit === 'function') {
                form.requestSubmit(continueSubmit);
            } else {
                continueSubmit.click();
            }
            return;
        }

        // Fallback: add a hidden _continue flag and submit.
        let continueFlag = form.querySelector('input[type="hidden"][name="_continue"]');
        if (!continueFlag) {
            continueFlag = document.createElement('input');
            continueFlag.type = 'hidden';
            continueFlag.name = '_continue';
            continueFlag.value = '1';
            form.appendChild(continueFlag);
        }

        form.submit();
    }

    fieldsets.forEach(function(fieldset) {
        const h2 = fieldset.querySelector('h2');
        const firstFormRow = fieldset.querySelector('.form-row:first-of-type');

        // Only add header if h2 exists and matches target headers
        if (h2 && firstFormRow) {
            const headerText = h2.textContent.trim();

            headerNodesByText.set(headerText, h2);

            // Check if this fieldset is one of the target fieldsets
            if (targetHeaders.includes(headerText)) {
                // Create the custom HTML header
                const headerRow = document.createElement('div');
                headerRow.className = 'fieldset-table-header';
                headerRow.innerHTML = `
                    <div class="header-indicator">Indicator</div>
                    <div class="header-comment">Comment / source</div>
                    <div class="header-actions">
                        <button type="button" class="cc-calc-button" title="Save and continue editing" aria-label="Save and continue editing">Calculate</button>
                    </div>
                `;

                const calcButton = headerRow.querySelector('.cc-calc-button');
                if (calcButton) {
                    calcButton.addEventListener('click', function(e) {
                        e.preventDefault();
                        submitSaveAndContinue(calcButton);
                    });
                }

                // Insert after the first form-row (which contains the header field)
                firstFormRow.parentNode.insertBefore(headerRow, firstFormRow.nextSibling);
            }
        }
    });

    function addHeaderHelpTooltip(headerText, imageFilename, imageAlt, extraIconClass) {
        const headerNode = headerNodesByText.get(headerText);
        if (!headerNode) {
            return;
        }

        if (headerNode.querySelector('.cc-help-icon')) {
            return;
        }

        const fallbackHelpTextContent = 'Help image failed to load.';

        const helpIcon = document.createElement('span');
        helpIcon.className = `help-icon cc-help-icon ${extraIconClass || ''}`.trim();
        helpIcon.innerHTML = 'ⓘ';
        helpIcon.title = 'Click for more information';

        const tooltip = document.createElement('div');
        tooltip.className = 'help-tooltip cc-help-tooltip';

        const helpImage = document.createElement('img');
        helpImage.src = `/static/images/cc/${imageFilename}`;
        helpImage.alt = imageAlt;
        helpImage.loading = 'lazy';
        helpImage.addEventListener('error', function() {
            tooltip.textContent = fallbackHelpTextContent;
        });

        tooltip.appendChild(helpImage);

        headerNode.appendChild(document.createTextNode(' '));
        headerNode.appendChild(helpIcon);

        headerNode.style.position = 'relative';
        headerNode.appendChild(tooltip);

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
            if (!headerNode.contains(e.target)) {
                tooltip.classList.remove('visible');
            }
        });

        if (!escKeyHandlerAdded) {
            escKeyHandlerAdded = true;
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' || e.key === 'Esc') {
                    document.querySelectorAll('.cc-help-tooltip.visible').forEach(function(openTooltip) {
                        openTooltip.classList.remove('visible');
                    });
                }
            });
        }
    }

    addHeaderHelpTooltip(
        '1. Pre-Crisis Vulnerability',
        'pre_crisis_vulnerability.gif',
        'Pre-Crisis Vulnerability help',
        'precrisis-help-icon'
    );
    addHeaderHelpTooltip(
        '2. Crisis Complexity',
        'crisis_complexity.gif',
        'Crisis Complexity help',
        'crisiscomplexity-help-icon'
    );
    addHeaderHelpTooltip(
        '3. Scope & Scale',
        'scope_and_scale.gif',
        'Scope & Scale help',
        'scopeandscale-help-icon'
    );
    addHeaderHelpTooltip(
        '4. Humanitarian Conditions',
        'humanitarian_conditions.gif',
        'Humanitarian Conditions help',
        'humanitarianconditions-help-icon'
    );
    addHeaderHelpTooltip(
        '5. Capacity & Response',
        'capacity_and_response.gif',
        'Capacity & Response help',
        'capacityandresponse-help-icon'
    );

    const informMapExplorerUrl = 'https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Map-Explorer';

    function addExternalLinkIcon(fieldSelector, url) {
        const field = document.querySelector(fieldSelector);
        if (!field) {
            return;
        }

        const label = field.querySelector('label');
        if (!label) {
            return;
        }

        if (label.querySelector('.external-link-icon')) {
            return;
        }

        const link = document.createElement('a');
        link.className = 'external-link-icon';
        link.href = url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.title = 'Open INFORM Risk Map Explorer';
        link.setAttribute('aria-label', 'Open INFORM Risk Map Explorer');

        // Inline SVG external-link icon
        link.innerHTML = `
            <svg viewBox="0 0 24 24" role="img" focusable="false" aria-hidden="true">
                <path d="M14 3h7v7h-2V6.41l-9.29 9.3-1.42-1.42 9.3-9.29H14V3z"></path>
                <path d="M5 5h7v2H7v10h10v-5h2v7H5V5z"></path>
            </svg>
        `;

        label.appendChild(link);
    }


    function addFieldHelpTooltip(label) {
        if (label.querySelector('.field-help-icon')) {
            return;
        }

        const helpIcon = document.createElement('span');
        helpIcon.className = 'help-icon cc-help-icon field-help-icon';
        helpIcon.textContent = 'ⓘ';
        helpIcon.title = 'Click for more information';
        helpIcon.style.fontStyle = 'normal';
        helpIcon.style.marginLeft = '5px';
        helpIcon.style.cursor = 'pointer';

        const tooltip = document.createElement('div');
        tooltip.className = 'help-tooltip cc-help-tooltip field-help-tooltip';
        tooltip.textContent = 'This indicator will not be counted for the score but is needed for the overall tracking and estimations.';
        tooltip.style.fontStyle = 'normal';

        // Ensure label can position the absolute tooltip
        label.style.position = 'relative';

        label.appendChild(helpIcon);
        label.appendChild(tooltip);

        helpIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const isVisible = tooltip.classList.contains('visible');

            // Close all open tooltips first
            document.querySelectorAll('.cc-help-tooltip.visible').forEach(function(openTooltip) {
                openTooltip.classList.remove('visible');
            });

            if (!isVisible) {
                tooltip.classList.add('visible');
            }
        });

        document.addEventListener('click', function(e) {
            if (!label.contains(e.target)) {
                tooltip.classList.remove('visible');
            }
        });
    }

    function italicizeFieldLabels(fieldNames) {
        fieldNames.forEach(function(fieldName) {
            const label = document.querySelector(`label[for="id_${fieldName}"]`);
            if (!label) {
                return;
            }

            label.style.fontStyle = 'italic';
            addFieldHelpTooltip(label);
        });
    }

    italicizeFieldLabels([
        'pre_crisis_vulnerability_hazard_exposure_intermediate',
        'pre_crisis_vulnerability_vulnerability_intermediate',
        'pre_crisis_vulnerability_coping_mechanism_intermediate',
        'crisis_complexity_humanitarian_access_acaps',
        'scope_and_scale_number_of_affected_population',
        'scope_and_scale_total_population_of_the_affected_area',
        'scope_and_scale_percentage_affected_population',
        'scope_and_scale_impact_index_inform',
        'humanitarian_conditions_casualties_injrd_deaths_missing',
        'humanitarian_conditions_severity',
        'humanitarian_conditions_people_in_need',
        'capacity_and_response_ifrc_international_staff',
        'capacity_and_response_ifrc_national_staff',
        'capacity_and_response_ifrc_total_staff',
        'capacity_and_response_regional_office',
        'capacity_and_response_ops_capacity_ranking',
        'capacity_and_response_number_of_ns_staff',
        'capacity_and_response_ratio_staff_volunteer',
        'capacity_and_response_number_of_ns_volunteer',
        'capacity_and_response_number_of_dref_ea_last_3_years'
    ]);

    // Add external URL icons after labels
    addExternalLinkIcon('.field-pre_crisis_vulnerability_hazard_exposure', informMapExplorerUrl);
    addExternalLinkIcon('.field-pre_crisis_vulnerability_vulnerability', informMapExplorerUrl);
    addExternalLinkIcon('.field-pre_crisis_vulnerability_coping_mechanism', informMapExplorerUrl);
    addExternalLinkIcon('.field-crisis_complexity_humanitarian_access_score', informMapExplorerUrl);
    addExternalLinkIcon('.field-crisis_complexity_humanitarian_access_acaps', informMapExplorerUrl);
    addExternalLinkIcon('.field-scope_and_scale_impact_index_score', informMapExplorerUrl);
    addExternalLinkIcon('.field-humanitarian_conditions_severity_score', informMapExplorerUrl);
    addExternalLinkIcon('.field-capacity_and_response_ifrc_capacity_score', informMapExplorerUrl);
    addExternalLinkIcon('.field-capacity_and_response_ops_capacity_score', informMapExplorerUrl);
    addExternalLinkIcon('.field-capacity_and_response_ns_staff_score', informMapExplorerUrl);
    addExternalLinkIcon('.field-capacity_and_response_ratio_staff_to_volunteer_score', informMapExplorerUrl);
    addExternalLinkIcon('.field-capacity_and_response_number_of_dref_score', informMapExplorerUrl);
});
