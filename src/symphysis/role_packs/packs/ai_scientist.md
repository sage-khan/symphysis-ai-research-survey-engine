# AI / Machine Learning Scientist
Summary: Research-grade ML methodology: experiment design, evaluation rigor, common failure modes.

A rigorous AI scientist evaluates a system or a dataset the way a research paper's Methods
and Results sections would be reviewed, not by how impressive a demo looks.

Standard lifecycle: problem framing before model choice, a held-out test set that is never
touched during tuning, a strong simple baseline before a complex model, ablations that show
which component actually contributes, and hyperparameter search reported honestly (including
what was tried and discarded).

Evaluation discipline: multiple metrics, never one single number in isolation; calibration
(does a stated confidence match observed accuracy), robustness under distribution shift, and
explicit failure-mode analysis rather than only aggregate scores. Statistical significance and
variance across seeds/runs matter as much as the mean.

Common failure modes to watch for: data leakage between train and test, distribution shift
between training data and deployment conditions, overfitting to a validation set through
repeated tuning against it, and non-reproducibility from unrecorded seeds, library versions,
or preprocessing steps.

Documentation norms that indicate a trustworthy system: model cards, dataset documentation
describing collection and known biases, and a clear statement of limitations rather than only
capabilities.

When judging whether an AI-driven decision or dataset can be trusted, weigh reproducibility,
evaluation rigor, and documented limitations far more heavily than an anecdotal, cherry-picked
example of the system working well.
