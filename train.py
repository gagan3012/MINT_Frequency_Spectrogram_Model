from utils.model import Simp_Model
from torch import nn
import torch
from tqdm import tqdm
from myargs import args
import time
import numpy as np
import utils.dataset as dataset


def train():

    # define model
    model = Simp_Model()

    # check if continue training from previous epochs
    #if args.continueTrain:
    #    pretrained_dict = torch.load('PATH HERE'.format(args.start_epoch))['state_dict']
    #    model_dict = model.state_dict()
        # 1. filter out unnecessary keys
    #    pretrained_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict}
        # 2. overwrite entries in the existing state dict
    #    model_dict.update(pretrained_dict)
    #    model.load_state_dict(model_dict)

    # define optimizer, loss function, and iterators
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
        betas=(args.beta1, args.beta2)
    )

    lossfn = torch.nn.CrossEntropyLoss(weight=torch.tensor([1.,282/55,282/81,282/79,282/67]))
    #lossfn = torch.nn.MSELoss() 
    
    iterator_train = dataset.GenerateIterator(args, '/data/train/trainfiles')
    iterator_val = dataset.GenerateIterator(args, '/data/train/valfiles')

    # cuda?
    if torch.cuda.is_available():
        model = model.cuda()
        lossfn = lossfn.cuda()

    start_epoch = 1

    for epoch in range(start_epoch, args.num_epoch):

        # values to look at average loss per batch over epoch
        loss_sum, batch_num = 0, 0
        progress_bar = tqdm(iterator_train, disable=False)
        start = time.time()

        '''======== TRAIN ========'''
        for images, labels in progress_bar:
            if torch.cuda.is_available():
                images = images.cuda()
                labels = labels.cuda()
            
            images = images.float()
            labels = labels.long()
            
            images = images.flatten()

            prediction = model(images)
 
            #print(prediction)
            #print(labels)

            loss = lossfn(prediction, labels)#.mean()

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            loss_sum += loss.item()
            batch_num += 1

            progress_bar.set_description('Loss: {:.5f} '.format(loss_sum / (batch_num + 1e-6)))

        '''======== VALIDATION ========'''
        if epoch % 1 == 0:
            with torch.no_grad():
                model.eval()

                preds, gts = [], []

                progress_bar = tqdm(iterator_val)
                val_loss = 0

                for images, labels in progress_bar:
                    if torch.cuda.is_available():
                        images, labels = images.cuda(), labels.cuda()
                    
                    images = images.float()
                    labels = labels.long()
            
                    images = images.flatten()

                    prediction = model(images)

                    loss = lossfn(prediction, labels)

                    prediction = torch.softmax(prediction, dim=1)
                    pred_class = torch.argmax(prediction, dim=1)

                    preds.append(pred_class.cpu().numpy())
                    gts.append(labels.cpu().numpy())

                    val_loss += loss.item()

                preds = np.asarray(preds)
                gts = np.asarray(gts)

                #val_classification_score = (np.mean(preds == gts)).astype(np.float)
                val_classification_score = (preds == gts).sum()/len(preds)

                print(
                    '|| Ep {} || Secs {:.1f} || Loss {:.1f} || Val score {:.3f} || Val Loss {:.3f} ||\n'.format(
                        epoch,
                        time.time() - start,
                        loss_sum,
                        val_classification_score,
                        val_loss,
                    ))

            model.train()

        # save models every 1 epoch
        #if epoch % 5 == 0:
        #    state = {
        #        'epoch': epoch,
        #        'state_dict': model.state_dict(),
        #        'optimizer': optimizer.state_dict(),
        #    }
            #torch.save(state, 'PATH HERE'.format(args.model_name, epoch))


if __name__ == '__main__':
    train()
