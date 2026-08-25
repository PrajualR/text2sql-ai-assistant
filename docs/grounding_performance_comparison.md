# Grounding Performance Comparison

The knowledge graph is implemented using the existing ESG semantic metadata
stored in:

`data/esg_knowledge.json`

---

## Approaches Compared

### 1. Embeddings

The existing grounding approach uses:

- BGE embeddings
- ChromaDB
- Semantic similarity search
- PDF-derived ESG knowledge documents

The retriever returns relevant text chunks from the knowledge base.

### 2. JSON Knowledge Graph

The alternative grounding approach uses:

- `data/esg_knowledge.json`
- In-memory loading
- Explicit KPI and dimension relationships
- Deterministic exact-phrase matching

The graph directly resolves business terminology to database columns.

For example:

```text
carbon footprint
    ├── Scope1_Emissions
    ├── Scope2_Emissions
    └── Scope3_Emissions

employee attrition
    └── Employee_Turnover_Percentage

green energy
    └── Renewable_Energy_Percentage
```

This makes the semantic relationship explicit instead of relying on vector
similarity.

---

# Benchmark Methodology

Both approaches were evaluated against the same **17-question test set**.

The benchmark covers:

- Direct KPI aliases
- Business synonyms
- Multi-KPI business concepts
- Dimension grounding
- Compliance metrics
- Workforce terminology
- Phrasing variations
- Facility/site terminology
- Industry/sector terminology

The expected database columns are based on the actual SQLite schema and the
ESG semantic layer.

### Metrics

Three measurements were used.

#### 1. Context Grounding Recall

Measures whether the expected database column, or its human-readable KPI or
dimension name, appears in the context returned by the retriever.

#### 2. Structural Precision and Recall

The knowledge graph returns explicit structured column mappings, so its
actual resolved columns can be compared directly with the expected columns.

The embedding retriever returns free-text chunks rather than structured
column mappings, so equivalent structural precision/recall cannot be
calculated for it.

#### 3. Retrieval Latency

Measures the time required to perform the grounding operation.

For the embedding retriever, the BGE model is warmed up before the benchmark
starts. This removes the one-time model-loading cost from the per-query
latency measurement and gives a steady-state comparison.

---

# Benchmark Results

| Metric | JSON Knowledge Graph | Embeddings |
|---|---:|---:|
| Context grounding recall | **91%** | 87% |
| Structural precision | **98%** | N/A |
| Structural recall | **91%** | N/A |
| Average retrieval latency | **0.8 ms** | 98.2 ms |

## Performance Difference

The JSON knowledge graph achieved approximately:

**123x lower average retrieval latency**

```text
98.2 ms / 0.8 ms ≈ 122.75x
```

The graph also achieved higher context grounding recall:

```text
Knowledge Graph: 91%
Embeddings:      87%
```

---

# Accuracy Comparison

## Knowledge Graph

The knowledge graph achieved:

- **91% context grounding recall**
- **98% structural precision**
- **91% structural recall**

The graph's misses were primarily caused by limitations of the current
explicit vocabulary.

### Entity value

Question:

```text
List facilities in Germany
```

The graph correctly understands the facility dimension, but the current
knowledge graph represents the `Country` column rather than individual
country values. Therefore, `Germany` is not currently represented as an
entity/value node.

### Unlisted phrasing

Question:

```text
Show freshwater usage by site
```

The graph recognizes `site` as a facility alias, but `freshwater usage` is
not currently listed as an alias for `Water_Withdrawal_m3`.

### Vocabulary variation

Question:

```text
Compare waste output across sectors
```

The graph resolves the waste KPI but does not currently map `sectors` to
the `Industry` dimension because that vocabulary variation is not present
in the alias list.

These are vocabulary coverage limitations rather than incorrect mappings.
They can be addressed by extending the semantic JSON with additional
aliases or entity values where appropriate.

---

## Embedding Retriever

The embedding approach achieved:

- **87% context grounding recall**
- **98.2 ms average steady-state latency**

Its misses were concentrated around semantic relationships that were not
consistently surfaced by similarity retrieval.

### Attrition vs. turnover

Question:

```text
Show employee attrition by country
```

Expected column:

```text
Employee_Turnover_Percentage
```

The ESG semantic layer defines employee attrition as a business synonym for
employee turnover, but embedding retrieval did not consistently return the
relevant column in the retrieved context.

The same issue appeared with:

```text
Which plants have the highest employee attrition?
```

### Multi-column business concept

Question:

```text
Show carbon footprint by facility
```

The knowledge graph explicitly represents:

```text
carbon footprint
    ├── Scope1_Emissions
    ├── Scope2_Emissions
    └── Scope3_Emissions
```

The embedding retriever did not reliably return all three Scope columns in
the retrieved context.

This demonstrates the difference between semantic similarity retrieval and
explicit relationship-based grounding.

---


# Key Findings

### 1. Knowledge graph provides better measured grounding recall

The graph achieved **91%**, compared with **87%** for embeddings.

The difference is relatively small, so the benchmark does not show a
dramatic accuracy advantage. However, it demonstrates that explicit
relationships can achieve comparable or slightly better grounding accuracy
for this fixed ESG vocabulary.

### 2. Knowledge graph is significantly faster

The graph averaged **0.8 ms/query**, while embeddings averaged
**98.2 ms/query**.

This is approximately a **123x latency advantage** for the JSON knowledge
graph.

The primary reason is that the graph performs deterministic in-memory
resolution and does not require embedding model inference or vector
similarity search for each question.

### 3. Knowledge graph provides explicit mappings

The graph directly produces mappings such as:

```text
employee attrition
        ↓
Employee_Turnover_Percentage
```

and:

```text
carbon footprint
        ↓
Scope1_Emissions
Scope2_Emissions
Scope3_Emissions
```

This makes the semantic relationship explicit and predictable.

### 4. Embeddings provide broader vocabulary tolerance

Embeddings remain useful when terminology is difficult to enumerate in
advance.

Users may introduce new wording that is semantically related to an existing
KPI but has not been added as an explicit graph alias.

The trade-off is that semantic similarity does not guarantee that the exact
required relationship or all required columns will be retrieved.

---

# Conclusion

For the current ESG manufacturing grounding use case, the **JSON-based
knowledge graph performed better in the benchmark**.

```text
                     Knowledge Graph    Embeddings
Grounding Recall          91%              87%
Latency                   0.8 ms           98.2 ms
Structural Precision      98%               N/A
Structural Recall         91%               N/A
```

The knowledge graph provides:

- Slightly higher measured grounding recall
- Explicit and deterministic column mappings
- Multi-column business concept resolution
- Approximately 123x lower retrieval latency
- No external graph database dependency

The main trade-off is vocabulary maintenance. New business terminology,
phrasing variations, or entity values may need to be explicitly added to
the JSON semantic layer.

For a relatively small and controlled ESG schema, this trade-off is
manageable.

**Based on the benchmark, the JSON knowledge graph is the stronger
grounding approach for this specific CR and current ESG use case.**

---