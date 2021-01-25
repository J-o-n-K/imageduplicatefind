import os
import sys
import cv2
from difflib import SequenceMatcher
import statistics

class Differences:
    # templates = set()
    # hists = set()
    # fileseqs = set()
    def __init__(self,template_diff,hist_diff,file_diff):
        self.template_diff = template_diff
        self.hist_diff = hist_diff
        self.file_diff = file_diff # flip the ratio to be in the same style as opencv's image compares
        # Differences.templates.add(self.template_diff)
        # Differences.hists.add(self.hist_diff)
        # Differences.fileseqs.add(self.file_diff)
    def GetRatio(self):
        return self.template_diff + self.hist_diff + self.file_diff
    def CheckDiff(self,inclusive,inclusiveignorefile=True):
        if inclusive:
            return self.hist_diff < g_hist_diff or self.template_diff < g_temp_diff or self.file_diff < g_maximum_file_diff
        return self.hist_diff < g_hist_diff and self.template_diff < g_temp_diff and (self.file_diff < g_maximum_file_diff or inclusiveignorefile)
    def DiffDispStr(self):
        return '%.4f %s %.4f %s %.4f %s' % (self.hist_diff,self.hist_diff < g_hist_diff,self.template_diff, self.template_diff < g_temp_diff, self.file_diff, self.file_diff < g_maximum_file_diff)
    # def stats(self):
    #     return statistics.stdev([self.hist_diff, self.template_diff, self.file_diff]), statistics.variance([self.hist_diff, self.template_diff, self.file_diff])
    def __repr__(self):
        return '%s(%s,%s,%s)' % (self.__class__.__name__, self.template_diff, self.hist_diff, self.file_diff)

class ImageCompare(object):
    def __init__(self, image_path):
        self.image_path = image_path

    def GetCVim(self):
        return cv2.imread(str(self.image_path), cv2.IMREAD_COLOR)

    def compare_image(self,other,image_1=[]):
        if len(image_1) == 0:
            image_1 = self.GetCVim()
        image_2 = other.GetCVim()

        first_image_hist = cv2.calcHist([image_1], [0], None, [256], [0, 256])
        second_image_hist = cv2.calcHist([image_2], [0], None, [256], [0, 256])

        img_hist_diff = cv2.compareHist(first_image_hist, second_image_hist, cv2.HISTCMP_BHATTACHARYYA)
        img_template_probability_match = cv2.matchTemplate(first_image_hist, second_image_hist, cv2.TM_CCOEFF_NORMED)[0][0]
        img_template_diff = 1 - img_template_probability_match

        file_diff = 1-SequenceMatcher(None, self.image_path.filenamenoext, other.image_path.filenamenoext).ratio()

        ret = Differences(img_template_diff,img_hist_diff,file_diff)
        #print(ret)
        
        return ret

class ImageClassified:
    def __init__(self,img,diff):
        self.img=img
        self.diff=diff
    def __lt__(self,other):
        return self.img.image_path.size < other.img.image_path.size

class filepath:
    def __init__(self,path,filename,size=None):
        self.path = path
        self.filename = filename
        self.fullpath = os.path.join(path,filename)
        self.filenamenoext = '.'.join(filename.split('.')[:-1])
        self.size = size
        if not size:
            self.size = os.stat(self.fullpath).st_size
    def __lt__(self,other):
        return self.size < other.size
    def __str__(self):
        return self.fullpath
    def __repr__(self):
        return '%s(%s,%s,%s)' % (self.__class__.__name__, self.path, self.filename, self.size)

g_dupimagefolder = 'dupeimagefolder'
def main(root):
    for directory, dirnames, filenames in os.walk(root):
        if len(filenames)>0:
            print('working',directory)
        else:
            continue
        if os.path.split(directory)[1] == g_dupimagefolder:
            continue
        moveto = os.path.join(directory,g_dupimagefolder)
        notclassified = []
        filenames = [filepath(directory,filename) for filename in filenames]
        filenames.sort(reverse=True)

        for filename in filenames:
            notclassified.append(ImageCompare(filename))
        #for img in notclassified:
        while len(notclassified)>0:
            img = notclassified[0]
            imread = img.GetCVim()
            matches = [ImageClassified(img,Differences(0,0,0))]
            for img2 in notclassified:
                if img != img2:
                    diff = img.compare_image(img2,imread)
                    #if diff.GetIMGRatio() < g_minimum_commutative_image_diff:
                    if diff.CheckDiff(True):
                        matches.append(ImageClassified(img2,diff))
            matches.sort(reverse=True) # assuming the biggest image is an uncut / best quality
            takebacksies = 0
            hists = []
            temps = []
            files = []
            if len(matches) > 1:
                movetosub = os.path.join(moveto,matches[0].img.image_path.filename)
                if not os.path.exists(moveto):
                    os.mkdir(moveto)
                if not os.path.exists(movetosub):
                    os.mkdir(movetosub)
            for match in matches:
                # hists.append(match.diff.hist_diff)
                # temps.append(match.diff.template_diff)
                # files.append(match.diff.file_diff)
                if match.diff.CheckDiff(False):
                    print('+',match.img.image_path.filename,match.img.image_path.size,match.diff.DiffDispStr())
                    notclassified.remove(match.img)
                    if match.diff.hist_diff == 0.0 and match.diff.template_diff == 0.0 and match.diff.file_diff == 0.0:
                        continue # don't move the 'source' image
                    os.rename(os.path.join(directory,match.img.image_path.filename),os.path.join(movetosub,match.img.image_path.filename))
                else:
                    print('-',match.img.image_path.filename,match.img.image_path.size,match.diff.DiffDispStr())
                    takebacksies = takebacksies + 1
                #print(match.diff.stats())
            # print('stdev hists',statistics.stdev(hists))
            # print('stdev temps',statistics.stdev(temps))
            # print('stdev files',statistics.stdev(files))
            # print('varia hists',statistics.variance(hists))
            # print('varia temps',statistics.variance(temps))
            # print('varia files',statistics.variance(files))
            # print('Progression',len(notclassified),'-',len(matches) - takebacksies)

g_temp_diff = 0.09
g_hist_diff = 0.13
g_maximum_file_diff = 0.35

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('This program will walk through your target directory and move all images it things are parts / duplicates to a subfolder of',g_dupimagefolder+'/[filename it thinks this is a dupe of]')
        print('Need path to check for similar images')
        print('dupeimagefinder.py /some/directory/to/check')
    else:
        main(sys.argv[1])

