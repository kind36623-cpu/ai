"""
conftest.py — pytest configuration for Seed AGI backend tests.
Sets up environment variables so tests run without real API keys.
"""
import os
import pytest

# Inject mock values before any app code runs
os.environ.setdefault("GEMINI_API_KEY",   "test-key")
os.environ.setdefault("GROQ_API_KEY",     "test-key")
os.environ.setdefault("PINECONE_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY",       "test-secret")
os.environ.setdefault("DEBUG",            "false")
