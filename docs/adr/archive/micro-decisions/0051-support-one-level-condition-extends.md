# Support One-Level Condition Extends

V1 evaluation matrix conditions may extend one existing condition to avoid duplicated configuration and make ablations explicit. The matrix parser will support only one level of inheritance and must resolve each condition into a complete effective condition before formal evaluation and run manifest creation, avoiding hard-to-read inheritance chains.
