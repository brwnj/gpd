# JGI Genome Portal Downloader

Yep, you _could_ probably use [Globus](https://www.globus.org/), but if you
can't or don't want to you can download from the XML. This script simply makes
the `curl` calls for you.

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

# Usage (Python 3)

Create a config file. You can specify the file on the command line with `-c`
or run the app without a config file and see where it needs to go on your
operating system.

macOS:

```
/Users/brwnj/Library/Application Support/gpd/config.ini
```

The config looks like:

```
[jgi]
username:brwnj
password:passwrd
```

Then run it:

```
$ gpd --threads 8 -o tmp test.xml

[2016-05-21 11:56:56 - INFO] Logging into http://genome.jgi.doe.gov
[2016-05-21 11:56:56 - INFO] Successfully signed into JGI.
[2016-05-21 11:56:56 - INFO] Parsing test.xml for URLs.
[2016-05-21 11:56:56 - INFO] Found 4 files to download.
[2016-05-21 11:56:56 - INFO] Downloading...
[2016-05-21 11:57:01 - INFO] Downloaded 4 files.
[2016-05-21 11:57:01 - INFO] 4 files validated.
```

Files that do not have an md5 will always show as validated.

## Help

```
Usage: gpd [OPTIONS] XML

  Logs into JGI Genome Portal and downloads links from 'Open Downloads as
  XML' XML file. Files are written into `output`/JGI folder name.

  A configuration file is required and can either be placed in your
  application directory or specified each time on the command line.

  It looks like:

          [jgi]
          username:exampleuser
          password:examplepassword

Options:
  -c, --configfile TEXT  configuration file defining username and password
  -o, --output TEXT      optional output dir
  --overwrite            overwrite existing downloaded files  [default: False]
  --retries INTEGER      number of download retries if there is an error
                         [default: 5]
  -t, --threads INTEGER  number of simultaneous download threads  [default:
                         12]
  -h, --help             Show this message and exit.
```
