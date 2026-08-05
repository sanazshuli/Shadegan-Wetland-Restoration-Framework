# Reproducibility note

## What is reproducible from the public repository

- recalculation of the restoration-strategy accuracy and Cohen's Kappa from the reported confusion matrix;
- review of the analytical workflow and model structure;
- review of selected maps and manuscript-reported outputs;
- adaptation of the configuration-based Earth Engine workflow template.

## What is not fully reproducible from the public repository

The complete geospatial analysis depends on:

- digitised local management-plan layers;
- private or project-specific Earth Engine assets;
- the exact training samples used for land-cover classification;
- the complete threshold and label-generation record;
- the original model-validation split or sampling objects.

These materials are not silently replaced with synthetic data.

## Validation interpretation

The manuscript reports:

- 86.19% mean accuracy from five-fold cross-validation of the land-cover model;
- 98.1% accuracy and Kappa 0.971 for the restoration-strategy matrix.

The latter matrix contains no General Restoration samples and evaluates rule-derived strategy labels. It is therefore presented as internal validation, not independent field confirmation of all five classes.

## Recommended next research step

A stronger future validation design would include spatially independent expert/field labels, blocked spatial validation, explicit support for every strategy class, sensitivity analysis for rule thresholds, and uncertainty reporting.
