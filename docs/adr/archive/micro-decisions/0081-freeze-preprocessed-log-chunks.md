# Freeze Preprocessed Log Chunks

V1 offline case packages will include frozen preprocessed log chunks alongside raw logs. Formal evaluation should use the packaged chunks and record the log preprocessing version and chunk fingerprint, because chunking changes affect retrieval behavior and evidence hit rate; comparing new log preprocessing strategies should happen through a new suite version or an explicit preprocessing ablation.
