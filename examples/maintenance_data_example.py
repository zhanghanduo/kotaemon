"""Example script for using the maintenance data loaders.

This script demonstrates how to use the specialized loaders for machine maintenance data.
"""
import os
from pathlib import Path

from kotaemon.loaders import (
    MaintenanceDataLoader,
    SignalDataLoader,
    MaintenanceGraphLoader
)


def main():
    """Run the example script."""
    # Replace with the path to your maintenance data Excel file
    # example_file = Path("path/to/your/maintenance_data.xlsx")
    
    # For demonstration purposes, we'll just print the usage instructions
    print("Machine Maintenance Data Loader Example")
    print("-" * 40)
    print("\nThis example shows how to use the specialized loaders for machine maintenance data.")
    print("\nTo use this example with your own data:")
    print("1. Replace the example_file path with your Excel file path")
    print("2. Uncomment the loader code below")
    print("\nAvailable loaders:")
    print("- MaintenanceDataLoader: Basic loader for maintenance data")
    print("- SignalDataLoader: Specialized for signal data with signal types and processing methods")
    print("- MaintenanceGraphLoader: Creates graph-ready data with relationships")
    
    print("\nExample usage:")
    print("""
    # Basic maintenance data loading
    loader = MaintenanceDataLoader()
    documents = loader.load_data(example_file)
    print(f"Loaded {len(documents)} documents")
    
    # For the first document, print the content and metadata
    if documents:
        print("\nSample document content:")
        print(documents[0].text)
        print("\nSample document metadata:")
        for key, value in documents[0].metadata.items():
            print(f"{key}: {value}")
    
    # Signal data loading with automatic column detection
    signal_loader = SignalDataLoader()
    signal_docs = signal_loader.load_data(example_file)
    
    # Graph data loading with relationship extraction
    graph_loader = MaintenanceGraphLoader()
    graph_docs = graph_loader.load_data(example_file, extract_relationships=True)
    
    # Count entity and relationship nodes
    entity_nodes = [doc for doc in graph_docs if doc.metadata.get("node_type") == "entity"]
    relationship_nodes = [doc for doc in graph_docs if doc.metadata.get("node_type") == "relationship"]
    print(f"\nGraph data: {len(entity_nodes)} entities, {len(relationship_nodes)} relationships")
    """)


if __name__ == "__main__":
    main()