###########################################################################
# CGNet: A Light-weight Context Guided Network for Semantic Segmentation
# Paper-Link: https://arxiv.org/pdf/1811.08201.pdf
###########################################################################

import torch
import torch.nn as nn
import torch.nn.functional as F

from climatenet_plus.climatenet.models.modules import *


class CGNet(nn.Module):
    """
    CGNet (Wu et al, 2018: https://arxiv.org/pdf/1811.08201.pdf) implementation.
    This is taken from their implementation, we do not claim credit for this.
    """

    def __init__(self, classes=19, channels=4, M=3, N=21, dropout_flag=False):
        """
        args:
          classes: number of classes in the dataset. Default is 19 for the cityscapes
          M: the number of blocks in stage 2
          N: the number of blocks in stage 3
        """
        super().__init__()
        # feature map size divided 2, 1/2
        self.level1_0 = ConvBNPReLU(channels, 32, 3, 2)
        self.level1_1 = ConvBNPReLU(32, 32, 3, 1)
        self.level1_2 = ConvBNPReLU(32, 32, 3, 1)

        # down-sample for Input Injection, factor=2
        self.sample1 = InputInjection(1)
        # down-sample for Input Injiection, factor=4
        self.sample2 = InputInjection(2)

        self.b1 = BNPReLU(32 + channels)

        # stage 2
        self.level2_0 = ContextGuidedBlock_Down(
            32 + channels, 64, dilation_rate=2, reduction=8)
        self.level2 = nn.ModuleList()
        for i in range(0, M-1):
            self.level2.append(ContextGuidedBlock(
                64, 64, dilation_rate=2, reduction=8))  # CG block
        self.bn_prelu_2 = BNPReLU(128 + channels)

        # stage 3
        self.level3_0 = ContextGuidedBlock_Down(
            128 + channels, 128, dilation_rate=4, reduction=16)
        self.level3 = nn.ModuleList()
        for i in range(0, N-1):
            self.level3.append(ContextGuidedBlock(
                128, 128, dilation_rate=4, reduction=16))  # CG block
        self.bn_prelu_3 = BNPReLU(256)

        if dropout_flag:
            print("have droput layer")
            self.classifier = nn.Sequential(
                nn.Dropout2d(0.1, False), Conv(256, classes, 1, 1))
        else:
            self.classifier = nn.Sequential(Conv(256, classes, 1, 1))

        # init weights
        for m in self.modules():
            classname = m.__class__.__name__
            if classname.find('Conv2d') != -1:
                nn.init.kaiming_normal_(m.weight)
                if m.bias is not None:
                    m.bias.data.zero_()
                elif classname.find('ConvTranspose2d') != -1:
                    nn.init.kaiming_normal_(m.weight)
                    if m.bias is not None:
                        m.bias.data.zero_()

    def forward(self, input):
        """
        args:
            input: Receives the input RGB image
            return: segmentation map
        """
        # stage 1
        output0 = self.level1_0(input)
        output0 = self.level1_1(output0)
        output0 = self.level1_2(output0)
        inp1 = self.sample1(input)
        inp2 = self.sample2(input)

        # stage 2
        output0_cat = self.b1(torch.cat([output0, inp1], 1))
        output1_0 = self.level2_0(output0_cat)  # down-sampled

        for i, layer in enumerate(self.level2):
            if i == 0:
                output1 = layer(output1_0)
            else:
                output1 = layer(output1)

        output1_cat = self.bn_prelu_2(
            torch.cat([output1,  output1_0, inp2], 1))

        # stage 3
        output2_0 = self.level3_0(output1_cat)  # down-sampled
        for i, layer in enumerate(self.level3):
            if i == 0:
                output2 = layer(output2_0)
            else:
                output2 = layer(output2)

        output2_cat = self.bn_prelu_3(torch.cat([output2_0, output2], 1))

        # classifier
        classifier = self.classifier(output2_cat)

        # upsample segmenation map ---> the input image size
        out = F.interpolate(classifier, input.size()[
                            2:], mode='bilinear', align_corners=False)  # Upsample score map, factor=8
        return out
