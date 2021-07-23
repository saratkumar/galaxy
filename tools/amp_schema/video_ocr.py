import json

class VideoOcr:
    def __init__(self, media=None, frames = []):
        self.frames = []
        if media is None:
            self.media = VideoOcrMedia()
        else:
            self.media = media
             
    def toCsv(self, outputFile):
        # Write as csv
        with open(outputFile, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['Start Time', 'Text', 'Language', 'X Min', 'Y Min', 'X Max', 'Y Max', 'Score Type', 'Score Value'])
            for f in self.frames:
                for o in f.objects:
                    if o.score is not None:
                        scoreType = o.score.type
                        scoreValue = o.score.scoreValue
                    else:
                        scoreType = ''
                        scoreValue = ''
                    if o.language is not None:
                        language = o.language
                    else:
                        language = ''
                    v = o.vertices
                    csv_writer.writerow([f.start, o.text, language, v.xmin, v.ymin, v.xmax, v.ymax, scoreType, scoreValue])
                                 
class VideoOcrResolution:
    width = None
    height = None
    frames = []
    def __init__(self, width = None, height = None):
        self.width = width
        self.height = height

    @classmethod
    def from_json(cls, json_data):
        return cls(**json_data)

class VideoOcrMedia:
    filename = ""
    duration = 0
    frameRate = None
    numFrames = None
    resolution = VideoOcrResolution()

    def __init__(self, duration = 0, filename = "", frameRate = None, numFrames = None, resolution = None):
        self.duration = duration
        self.filename = filename
        self.frameRate = frameRate
        self.numFrames = numFrames
        self.resolution = resolution

    @classmethod
    def from_json(cls, json_data):
        return cls(**json_data)

class VideoOcrFrame:
    start = 0
    objects = []
    def __init__(self, start = None, objects = None):
        self.start = start
        if(objects != None):
            self.objects = objects

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(**json_data)

    
class VideoOcrObject:
    text = ""
    language = ""
    score = None
    vertices = None
    def __init__(self, text = "", language = "", score = None, vertices = None):
        self.text = text
        self.language = language
        self.score = score
        self.vertices = vertices
        
    @classmethod
    def from_json(cls, json_data: dict):
        return cls(**json_data)


class VideoOcrObjectScore:
    type = ""
    value = None
    def __init__(self, type = "", value = None):
        self.type = type
        self.value = value
        
    @classmethod
    def from_json(cls, json_data: dict):
        return cls(**json_data)
    

class VideoOcrObjectVertices:
    xmin = 0
    ymin = 0
    xmax = 0
    ymax = 0
    def __init__(self, xmin = 0, ymin = 0, xmax = 0, ymax = 0):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        
    @classmethod
    def from_json(cls, json_data: dict):
        return cls(**json_data)