from flask import Flask, make_response, send_file
import flask
import os
import boto3
import StringIO
import requests
import mimetypes
from BeautifulSoup import BeautifulSoup


app = Flask(__name__)

os.environ['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY']
os.environ['BUCKET']


class S3Resource:
    def __init__(self):
        self.client = boto3.client('s3')
        self.bucket = os.environ['BUCKET']

    def presign(self, key):
        url = self.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self.bucket,
                'Key': key
            }
        )
        return url

    def read(self, key):
        data = StringIO.StringIO()
        self.client.download_fileobj(self.bucket, key, data)
        data.seek(0)
        return data

    def list(self, key):
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            MaxKeys=1000,
            Prefix=key,
            Delimiter="/",
        )

        return response.get('CommonPrefixes', []), response.get('Contents', [])


    
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/sign/<path:path>')
def sign(path):
    return S3Resource().presign(path)

@app.route('/redirect/<path:path>')
def redirect(path):
    url = S3Resource().presign(path)
    response = make_response("", 302)
    response.headers["Location"] = url
    return response

def index(path):
    dirs, indx = S3Resource().list("%s" % path)
    body = ["<tr><td><a href='/%(Prefix)s'>%(Prefix)s</a></td><td> </td><td> </td></tr>" % i for i in dirs]
    body += ["<tr><td><a href='/%(Key)s'>%(Key)s</a></td><td>%(LastModified)s</td><td>%(Size)d</td></tr>" % i for i in indx]
    return "<html><head><title>/%s/</title></head><body><table>%s</table></body></html>" % (path, "".join(body))
#    return flask.jsonify(indx)

@app.route('/<path:path>')
def serve(path):
    if path.endswith("/"):
        return index(path)
    if path.endswith(".html"):
        data = S3Resource().read(path)
        # data = StringIO.StringIO("""<a href='./abc.html'><img src='./abc.jpg' /></a>""")
        data.seek(0)
        if path.endswith(".html"):
            mangle_html("/" + path, data)
        return send_file(data, attachment_filename=path)
    return redirect(path)

def mangle_html(relative, data):
    base = os.path.dirname(relative)
    soup = BeautifulSoup(data.getvalue())
    # make all paths absolute.
    for a in soup.findAll('a'):
        a['href'] = fix_path(base, a['href'])
    for a in soup.findAll('img'):
        a['src'] = fix_path(base, a['src'])
    data.seek(0)
    data.write(str(soup))
    data.seek(0)

def fix_path(base, ref):
    path = os.path.normpath(os.path.join(base, ref))
    if mimetypes.guess_type(path)[0].split("/")[0] in ('image', 'video'):
        path = "/redirect/" + path
    return path
        
        
