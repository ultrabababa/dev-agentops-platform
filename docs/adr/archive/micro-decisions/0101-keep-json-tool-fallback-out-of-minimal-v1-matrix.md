# Keep JSON Tool Fallback Out of Minimal V1 Matrix

V1 will implement strict JSON action fallback for tool use, but the minimal V1 evaluation matrix will not include it by default. Native provider tool calling remains the preferred protocol when supported; JSON fallback should enter the matrix only when required by the chosen provider or when explicitly evaluating tool call protocol differences.
