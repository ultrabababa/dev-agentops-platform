# Record Model Configuration Outside the Component Registry

V1 run manifests will record model configuration, including provider, model name, provider-supported version or snapshot, and inference parameters, because model choice affects evaluation results. Model configuration will remain part of evaluation conditions and run manifests rather than the component registry, which is reserved for repository-managed frozen component manifests that can be fingerprinted.
