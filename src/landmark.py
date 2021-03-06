from src import detect_faces, show_bboxes
from PIL import Image
import os
import torch
from torch import nn
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import numpy as np
import cv2
import numpy.random as npr
import sys
import utils as utils
from torch.autograd import Variable
import torchvision.models as models
import torch.optim as optim
import test2
size = 96




def cal_landmark(img_path):
    img = Image.open(img_path)
    #bounding_boxes, _, x = detect_faces(img)
    #bb = bounding_boxes[0]
    bounding_boxes, flag = test2.get_detect_faces(img_path)
    out3 = []
    if flag == 0:
        return bounding_boxes, out3, flag
    bb = np.array(bounding_boxes)
    image = cv2.imread(img_path)
    width, height, channel = image.shape
    net = torch.load('/home/lc/cy/106/106_demo_new/net.pkl')
    net.eval()
    out2 = []
    index = 0
    w = bb[2] - bb[0]
    h = bb[3] - bb[1]
    while index < 10:
        bbox_size = npr.randint(int(min(w, h) * 0.8), np.ceil(1.25 * max(w, h)))
        delta_x = npr.randint(-w * 0.2, w * 0.2)
        delta_y = npr.randint(-h * 0.2, h * 0.2)
        nx1 = int(max(bb[0] + w / 2 - bbox_size / 2 + delta_x, 0))
        ny1 = int(max(bb[1] + h / 2 - bbox_size / 2 + delta_y, 0))
        nx2 = int(nx1 + bbox_size)
        ny2 = int(ny1 + bbox_size)
        if nx2 > width or ny2 > height:
            continue
        crop_box = np.array([nx1, ny1, nx2, ny2])
        cropped_im = image[ny1:ny2 + 1, nx1:nx2 + 1, :]
        resized_im = cv2.resize(cropped_im, (96, 96), interpolation=cv2.INTER_LINEAR)
        # cal iou
        iou = utils.IoU(crop_box.astype(np.float), np.expand_dims(bb.astype(np.float), 0))
        if iou > 0.65:
            im = resized_im.transpose((2, 0, 1))
            im = im.reshape(1, 3, 96, 96)
            im = torch.from_numpy(im)
            im = im.type('torch.FloatTensor')
            im = Variable(im).cuda()
            out = net(im).data.cpu()
            print out
            out = out * float(size)
            print out
            out = out.numpy()
            ll = out[0]
            l2 = []
            for i in range(106):
                l2.append(ll[2 * i] / 96.0 * float(nx2-nx1) + float(nx1))
                l2.append(ll[2 * i + 1] / 96.0 * float(ny2-ny1) + float(ny1))
            out2.append(l2)
            index += 1
    out2 = np.array(out2)

    out2 = np.mean(out2,0)
    out4 = out2.tolist()

    out3.append(out4)
    return bounding_boxes, out3, flag

class Net(nn.Module):
    def __init__(self, model):
        super(Net, self).__init__()
        self.resnet_layer = nn.Sequential(*list(model.children())[:-2])

        self.fc = nn.Linear(4608, 212)

    def forward(self, x):
        x = self.resnet_layer(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)

        return x
