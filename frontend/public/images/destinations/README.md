# Destination photographs

Original photographs are unmodified 800px provider thumbnails, downloaded from Wikimedia Commons.
Author, license, original file and source article for each published photo are retained in
`src/rag/catalogue_images.json` in the project root and displayed in the popup credit link.
Follow the linked Commons file page for full licensing and attribution terms.

Candidate collection is not publication approval. `data/geography/image_candidates.json`
also contains rejected candidates and failed requests. Images of similarly named places
must not be accepted automatically. Run `scripts/prepare_destination_images.py` to collect
candidates, review their destination identity, then update the approved registry and run
`scripts/build_catalogue.py`. Requests can be rate-limited; do not retry aggressively.