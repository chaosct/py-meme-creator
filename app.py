import cherrypy
from unipath import Path, FILES
from mako.template import Template
from urllib import unquote
from hashlib import md5
from wand.image import Image
import subprocess
from cherrypy.lib.static import serve_file

class MemeCreator:
    def __init__(self):
        self.picsdir = Path().absolute()+'/images'
        self.renderdir = Path().absolute()+'/render'
        ftemplate = str(Path().absolute()+'/html/index.html')
        self.templateindex = Template(filename=ftemplate)
        self.fontpath = Path().absolute()+'/impact.ttf'

    def index(self):
        pics = self.picsdir.listdir(filter=FILES)
        picsf = [f.name for f in pics]
        return self.templateindex.render(pics=picsf)
       
    index.exposed = True

    def default(self, *args, **kwargs):
        URL = cherrypy.url(qs=cherrypy.request.query_string)
        text1, text2, picfilename = unquote(URL[len(cherrypy.request.base+'/'):]).split('/')
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
            with Image(filename=picfile) as img:
                width = img.width
            target.parent.mkdir(parents=True)
            self.convert(width, text1, picfile, 'north', target)
            self.convert(width, text2, target, 'south', target)
        return serve_file(target,"image/jpeg")

    def convert(self, width, text, source, location, destination):
        fontpath = self.fontpath
        subprocess.call(["convert",
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