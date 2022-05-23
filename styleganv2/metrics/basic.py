
# Metrics of PSNR and SSIM

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from math import exp

def convert2im(x):
    # convert [-1, 1] to [0, 1]
    return x*0.5 + 0.5

def psnr(x, y, epsilon=1e-6):
    # Peak Signal-to-Noise Ratio (PSNR)
    x_ = convert2im(x)
    y_ = convert2im(y)

    mse = torch.mean((x_ - y_) ** 2) + epsilon
    return 10 * torch.log10(1.0 / mse)


# SSIM: based on the implementation: https://github.com/Po-Hsun-Su/pytorch-ssim

def gaussian(window_size, sigma):
    gauss = torch.Tensor([exp(-(x - window_size//2)**2/float(2*sigma**2)) for x in range(window_size)])
    return gauss/gauss.sum()

def create_window(window_size, channel):
    _1D_window = gaussian(window_size, 1.5).unsqueeze(1)
    _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
    return Variable(_2D_window.expand(channel, 1, window_size, window_size).contiguous())

def _ssim(im1, im2, window, window_size, channel, size_average=True):
    mu1 = F.conv2d(im1, window, padding = window_size//2, groups = channel)
    mu2 = F.conv2d(im2, window, padding = window_size//2, groups = channel)

    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1*mu2

    sigma1_sq = F.conv2d(im1*im1, window, padding = window_size//2, groups = channel) - mu1_sq
    sigma2_sq = F.conv2d(im2*im2, window, padding = window_size//2, groups = channel) - mu2_sq
    sigma12 = F.conv2d(im1*im2, window, padding = window_size//2, groups = channel) - mu1_mu2

    C1 = 0.01**2
    C2 = 0.03**2

    ssim_map = ((2*mu1_mu2 + C1)*(2*sigma12 + C2))/((mu1_sq + mu2_sq + C1)*(sigma1_sq + sigma2_sq + C2))

    if size_average:
        return ssim_map.mean()
    else:
        return ssim_map.mean(1).mean(1).mean(1)

class SSIM(nn.Module):
    def __init__(self, window_size=11, size_average=True):
        super(SSIM, self).__init__()
        self.window_size = window_size
        self.size_average = size_average

    def forward(self, im1, im2):
        channel = im1.size(1)
        window = create_window(self.window_size, channel).type_as(im1)

        if im1.is_cuda:
            window = window.cuda(im1.get_device())
        return _ssim(im1, im2, window, self.window_size, channel, self.size_average)


def ssim(im1, im2, window_size=11, size_average=True):
    channel= im1.size(1)
    window = create_window(window_size, channel).type_as(im1)

    if im1.is_cuda:
        window = window.cuda(im1.get_device())
    return _ssim(im1, im2, window, window_size, channel, size_average)