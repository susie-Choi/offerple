# Archive

This directory contains archived versions and old structures for historical reference.

## graph-old-version/

Previous version of ROTA (originally called "Zero-Day Defense").

**Timeline**: Initial implementation before current ROTA architecture  
**Architecture**: Simple 3-phase approach (Collection → Signal Extraction → LLM Prediction)  
**Status**: Archived - superseded by current ROTA

### Why Archived

Current ROTA has evolved to a more sophisticated architecture:
- **Spokes**: Data collection from multiple sources
- **Hub**: Neo4j graph database integration
- **Wheel**: Clustering and pattern discovery
- **Oracle**: LLM-based prediction with RAG
- **Axle**: Temporal validation

The old version had a simpler approach that has been significantly improved in the current implementation.

### What Was Kept

- `docker-compose.yml`: Copied to root for Neo4j setup

### What Was Archived

- All source code (superseded by current src/rota/)
- All scripts (superseded by current src/scripts/)
- All documentation (superseded by current docs/)
- All configurations

## data/archive/

Old data directory structure before reorganization.

**Before**: Flat structure with raw/, processed/, analysis/  
**After**: Hierarchical structure with input/, output/, multimodal/

Archived for reference and potential data recovery.
