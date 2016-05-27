import click
import hashlib
import logging
import multiprocessing
import os
import subprocess as sp
import sys
import time
from functools import partial
from xml.etree import cElementTree as ET


def set_cookie(username, password, output):
    """Logs into JGI Genome Portal.

    Args:
        username (str): JGI Genome Portal username
        password (str): JGI Genome Portal password
        output (str): output dir where cookie file will be written

    Returns:
        str: the cookie file path

    Note:
        This method will exit with `1` if login appears to fail.
    """
    cookie = "{output}/jgi-cookies".format(output=output)
    cmd = ("curl 'https://signon.jgi.doe.gov/signon/create' --data-urlencode "
           "'login={username}' --data-urlencode 'password={password}' "
           "-c {cookie} -s > {null}").format(username=username,
           password=password, cookie=cookie, null=os.devnull)
    logging.debug(cmd)
    sp.check_call(cmd, shell=True)
    logged_in = False
    with open(cookie) as fh:
        for line in fh:
            if "jgi_session" and "TRUE" in line:
                logged_in = True
                logging.info("Successfully signed into JGI.")
    if not logged_in:
        logging.critical("Login failed.")
        sys.exit(1)
    return cookie


def links_from_xml(xml):
    """Links for individual files within their respective folder along with
    md5 and url stub.

    Args:
        xml (string): xml file path

    Returns:
        list of dicts representing each individual file

    >>> d = links_from_xml('get-directory.xml')
    >>> d[0].keys()
    dict_keys(['md5', 'parent_folder', 'url', 'timestamp', 'sizeInBytes', 'fastq_format', 'rta_version', 'quality_score_type', 'library', 'project', 'filename', 'label', 'size'])
    """
    links = []
    doc = ET.parse(xml)
    root = doc.getroot()
    for folder in root.iterfind("folder"):
        for elem in folder.iterfind("file"):
            elem.attrib["parent_folder"] = folder.get("name")
            links.append(elem.attrib)
    return links


def download_link(cookie, link_dict, output_dir=".", retries=5, overwrite=False):
    """Builds and executes the download command. It will also create the file
    output dir and parent folder it lies in on the Genome Portal.

    Args:
        cookie (str): file path to cookie file
        link_dict (dict): entry dictionary from :func:`links_from_xml`
        output_dir (Optional[str]): file path to dir in which to write
        retries (Optional[int]): number of `curl` retries
        overwrite (Optional[boolean]): whether or not to overwrite existing local file

    Returns:
        tuple of output file path, md5
    """
    if link_dict['parent_folder']:
        output_dir = os.path.join(os.path.abspath(output_dir),
                                  link_dict['parent_folder'].replace(" ", "_"))
    else:
        output_dir = os.path.join(os.path.abspath(output_dir))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, link_dict['filename'])
    if os.path.exists(output_file) and not overwrite:
        logging.debug("File exists: %s" % output_file)
        return (output_file, link_dict['md5'])
    else:
        logging.debug('Downloading %s.', link_dict['filename'])
        cmd = ("curl 'http://genome.jgi.doe.gov{url}' -b {cookie} -s "
               "--retry {retries} > {file}").format(url=link_dict['url'],
               cookie=cookie, retries=retries, file=output_file)
        tries = 0
        while True:
            try:
                sp.check_call(cmd, shell=True)
                return (output_file, link_dict['md5'])
            except sp.CalledProcessError:
                tries += 1
                time.sleep(tries * 10)
                if tries > retries:
                    return "", ""


def handle_download(links, cookie, output_dir, retries, overwrite, threads):
    """Downloads links across threads as simultaneous downloads.

    Args:
        links (list): list of dict entries from :func:`links_from_xml`
        cookie (str): file path to cookie
        output_dir (str): dir path where to write new files
        retries (int): number of `curl` retries
        overwrite (boolean): whether or not to overwrite existing local files
        threads (int): number of simultaneous downloads

    Returns:
        list of local file path, md5 tuples.
    """
    pool = multiprocessing.Pool(processes=threads)
    download = partial(download_link, cookie, output_dir=output_dir,
                       retries=retries, overwrite=overwrite)
    download_results = pool.map(download, links)
    pool.close()
    pool.join()
    return download_results


def md5(fname):
    # https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
    hash_md5 = hashlib.md5()
    if not os.path.exists(fname):
        return None
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def check_md5(tpl):
    """Run :func:`md5` against the local file and compare to known remote md5.

    Args:
        tpl (tuple): file path, remote md5 string

    Returns:
        tuple of file path and test status
    """
    path, remote_md5 = tpl
    if remote_md5 != md5(path):
        return path, False
    else:
        return path, True


def validate_results(results, threads):
    """Validates Genome Portal downloads.

    Args:
        results (list): list of file, md5 strings
        threads (int): number of simultaneous md5 checks

    Returns:
        tuple of file path, test status
    """
    pool = multiprocessing.Pool(processes=threads)
    md5_results = pool.map(check_md5, results)
    pool.close()
    pool.join()
    validated = 0
    failed_files = list()
    for path, success in md5_results:
        if success:
            validated += 1
        else:
            failed_files.append(path)
    logging.info("%d files validated." % validated)
    if failed_files:
        logging.warn("%d files failed to download successfully." % len(failed_files))
        # thinking about making this cleanup optional
        for f in failed_files:
            if os.path.exists(f):
                os.remove(f)
        logging.warn("These partial files have been deleted to facilitate re-download.")
        logging.debug("Failed to download:\n %s" % "\n".join(failed_files))
    return md5_results


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("xml")
@click.argument("username")
@click.argument("password")
@click.option("-o", "--output", default=".", help="optional output dir")
@click.option("--overwrite", is_flag=True, default=False, show_default=True,
              help="overwrite existing downloaded files")
@click.option("--retries", default=5, type=int, show_default=True,
              help="number of download retries if there is an error")
@click.option("-t", "--threads", default=12, type=int, show_default=True,
              help="number of simultaneous download threads")
def gpd(xml, username, password, output, overwrite, retries, threads):
    """Logs into JGI Genome Portal and downloads links from
    'Open Downloads as XML' XML file. Files are written into `output`/JGI
    folder name.
    """
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s - %(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    if threads < 1:
        logging.warn("Setting `threads` to 1.")
        threads = 1

    output = os.path.abspath(output)
    os.makedirs(output, exist_ok=True)
    logging.info("Logging into http://genome.jgi.doe.gov")
    cookie = set_cookie(username, password, output)
    logging.info("Parsing %s for URLs." % xml)
    links = links_from_xml(xml)
    logging.info("Found %s files to download." % len(links))
    logging.info("Downloading...")
    download_results = handle_download(links, cookie, output, retries,
                                       overwrite, threads)
    logging.info("Downloaded %d files." % len(download_results))
    md5_results = validate_results(download_results, threads)


if __name__ == '__main__':
    gpd()
