#!/bin/bash

# Run the backend container with persistent volume for ChromaDB
docker run -p 8000:8000 -v $(pwd)/chroma_data:/app/chroma_data beakr-backend