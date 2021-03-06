import cherrypy
from unipath import Path, FILES
from mako.template import Template
from urllib import unquote
from hashlib import md5
import subprocess
from cherrypy.lib.static import serve_file
from PIL import Image

class MemeCreator:
    def __init__(self, convertcmd="convert"):
        thisdir = Path( __file__ ).parent.absolute()
        self.picsdir = thisdir+'/images'
        self.renderdir = thisdir+'/render'
        if not self.renderdir.exists():
            self.renderdir.mkdir()
        ftemplate = str(thisdir+'/html/index.html')
        self.templateindex = Template(filename=ftemplate)
        self.fontpath = thisdir+'/impact.ttf'
        self.convertcmd = convertcmd

    def index(self):
        pics = self.picsdir.listdir(filter=FILES)
        picsf = [f.name for f in pics]
        return self.templateindex.render(pics=picsf)
       
    index.exposed = True

    def default(self, *args, **kwargs):
        URL = cherrypy.url(qs=cherrypy.request.query_string)
        try:
            text1, text2, picfilename = unquote(URL[len(cherrypy.request.base+'/'):]).split('/')
        except ValueError:
            cherrypy.response.status = 500
            return self.serve_meme("500", "Arr! No t'entenc, pirata!", "piratecat1.jpg")
        return self.serve_meme(text1, text2, picfilename)

    def serve_meme(self, text1, text2, picfilename):
        picfile = self.picsdir.child(picfilename)
        if not picfile.exists():
            cherrypy.response.status = 404
            return self.serve_meme("404", "Meme not found", "piratecat1.jpg")
        #normalize text
        text1 = text1.upper().replace('_',' ')
        text2 = text2.upper().replace('_',' ')
        m = md5('/'.join([text1, text2, picfile])).hexdigest()
        target = self.renderdir.child(picfilename,m)
        if not target.exists():
            img = Image.open(picfile)
            width = img.size[1]
            target.parent.mkdir(parents=True)
            self.convert(width, text1, picfile, 'north', target)
            self.convert(width, text2, target, 'south', target)
        return serve_file(target,"image/jpeg")

    def convert(self, width, text, source, location, destination):
        fontpath = self.fontpath
        subprocess.call([self.convertcmd,
                            "-fill", "white",
                            "-stroke", "black",
                            "-strokewidth", "2",
                            "-background", "transparent",
                            "-gravity", "center",
                            "-size","{}x120".format(width),
                            "-font", str(fontpath),
                            "-weight", "Bold",
                            "caption:{}".format(text),
                            str(source),
                            "+swap",
                            "-gravity", location,
                            "-composite", str(destination),
                        ])

    default.exposed = True

if __name__ == '__main__':
    cherrypy.quickstart(MemeCreator())