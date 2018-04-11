try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
import itertools
import os
import requests
import shutil
import tarfile
import tempfile
import yaml


def repo_index(repo_url):
    """Downloads the Chart's repo index"""
    index_url = os.path.join(repo_url, 'index.yaml')
    index = requests.get(index_url)
    return yaml.load(index.content)


def from_repo(repo_url, chart, version=None):
    """Downloads the chart from a repo."""
    _tmp_dir = tempfile.mkdtemp(prefix='pyhelm-', dir='/tmp')
    index = repo_index(repo_url)

    if chart not in index['entries']:
        raise RuntimeError('Chart not found in repo')

    versions = index['entries'][chart]

    if version is not None:
        versions = itertools.ifilter(lambda k: k['version'] == version,
                                     versions)

    try:
        metadata = sorted(versions, key=lambda x: x['version'])[0]
        for url in metadata['urls']:
            try:
                req = requests.get(url, stream=True)
                fobj = StringIO(req.content)
                tar = tarfile.open(mode="r:*", fileobj=fobj)
                tar.extractall(_tmp_dir)
                return os.path.join(_tmp_dir, chart)
            except requests.exceptions.RequestException as e:
                raise RuntimeError('Requests error, could not GET resource at %s: \n %s' % (url, str(e)))
            except tarfile.TarError as e:
                raise RuntimeError('Could no untar chart: \n %s' % str(e))
    except IndexError:
        raise RuntimeError('Chart version %s not found' % version)


def source_cleanup(target_dir):
    """Clean up source."""
    try:
        shutil.rmtree(target_dir)
    except shutil.Error as e:
        raise RuntimeError('Could not delete chart source at %s: \n %s' % (target_dir, str(e)))
