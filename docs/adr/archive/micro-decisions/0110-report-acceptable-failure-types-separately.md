# Report Acceptable Failure Types Separately

V1 will report primary failure type exact accuracy separately from acceptable failure type selections. Acceptable alternatives may produce a pass-with-warning or partial-credit signal, but they will not be silently merged into exact accuracy; the initial quality gate will use exact accuracy so ambiguous-case leniency remains visible rather than inflating the main classification metric.
