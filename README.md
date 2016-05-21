# JGI Genome Portal Downloader

Yep, you _could_ probably use [Globus](https://www.globus.org/), but if you can't or don't want to you can download from the XML. This script simply makes the `curl` calls for you.

## Getting the XML

![JGI Genome Portal](/../master/resources/genome_portal.png?raw=true "JGI Genome Portal")

Looks a little something like:

```
<?xml version="1.0"?>
<organismDownloads name="xx">
    <folder name="folder name">
        <file filename="README.txt" url="/ext-api/downloads/.../README.txt" md5="9e590..." />
        <file ... />
    </folder>
</organismDownloads>
```

# Usage

```
$ gpd --threads 8 -o tmp test.xml 'brwnj' 'passwrd'

[2016-05-21 11:56:56 - INFO] Logging into http://genome.jgi.doe.gov
[2016-05-21 11:56:56 - INFO] Successfully signed into JGI.
[2016-05-21 11:56:56 - INFO] Parsing test.xml for URLs.
[2016-05-21 11:56:56 - INFO] Found 4 files to download.
[2016-05-21 11:56:56 - INFO] Downloading...
[2016-05-21 11:57:01 - INFO] Downloaded 4 files.
[2016-05-21 11:57:01 - INFO] 4 files validated.
```

## Help

```
Usage: gpd.py [OPTIONS] XML USERNAME PASSWORD

  Logs into JGI Genome Portal and downloads links from 'Open Downloads as
  XML' XML file. Files are written into `output`/JGI folder name.

Options:
  -o, --output TEXT      optional output dir
  --overwrite            overwrite existing downloaded files  [default: False]
  --retry INTEGER        number of download retries if there is an error
                         [default: 5]
  -t, --threads INTEGER  number of simultaneous download threads  [default:
                         12]
  -h, --help             Show this message and exit.
```
