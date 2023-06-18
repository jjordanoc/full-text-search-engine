raw_file_name = "C:/Users/rojot/OneDrive/Escritorio/data/arxiv-metadata-oai-snapshot.json"
limit = 1000000
with open(raw_file_name, "r") as raw_file, open("sample.json", "w") as sample_file:
    i = 0
    while i < limit:
        sample_file.write(raw_file.readline())
        i += 1
