# LanceDB Upgrade Guide for P.U.L.S.E.

This document provides instructions for upgrading LanceDB in the P.U.L.S.E. project.

## Current Status

P.U.L.S.E. currently uses LanceDB version 0.3.0 for vector storage and semantic search. The vector database implementation in `utils/vector_db.py` has been updated to support both:

1. Legacy LanceDB API (0.3.x)
2. Modern LanceDB API (0.4.0+)

The code will automatically detect which version is installed and use the appropriate API.

## Upgrading to Latest LanceDB

To upgrade to the latest version of LanceDB:

1. Update the requirements.txt file:
   ```diff
   - lancedb==0.3.0  # Vector database for semantic search
   + lancedb>=0.22.0  # Vector database for semantic search
   ```

2. Install the updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the vector database tests to verify the upgrade:
   ```bash
   python scripts/test_vector_db.py
   ```

## Migration Considerations

When upgrading from LanceDB 0.3.0 to a newer version, consider the following:

1. **Data Migration**: The table schema and storage format have changed between versions. The updated code will handle this automatically for new data, but existing vector data may need to be migrated.

2. **Performance Tuning**: Newer versions of LanceDB offer improved performance and additional configuration options. You may want to adjust the index parameters in `_initialize_modern_lancedb()` method for optimal performance.

3. **API Changes**: The search API has changed in newer versions. The updated code handles these differences, but custom code that directly interacts with LanceDB may need to be updated.

## Troubleshooting

If you encounter issues after upgrading:

1. **Compatibility Issues**: Ensure you have the latest versions of pandas and pyarrow installed.

2. **Data Access Errors**: If you can't access existing vector data, you may need to rebuild the vector database:
   ```python
   # Delete the existing vector database
   import shutil
   shutil.rmtree("data/vector_db")
   
   # Reinitialize the vector database
   from utils.vector_db import VectorDatabase
   vector_db = VectorDatabase()
   ```

3. **Performance Issues**: If search performance degrades, try adjusting the index parameters in `_initialize_modern_lancedb()` method.

## References

- [LanceDB Documentation](https://lancedb.github.io/lancedb/)
- [LanceDB Python API Reference](https://lancedb.github.io/lancedb/python/api/)
- [LanceDB Migration Guide](https://lancedb.github.io/lancedb/migration_guide/)
