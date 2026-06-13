import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# ==========================================
# 1. 내 노트북 환경에 맞게 자동 설정
# ==========================================
def get_device():
    if torch.cuda.is_available():
        return torch.device('cuda') # 엔비디아 GPU
    elif torch.backends.mps.is_available():
        return torch.device('mps')  # 맥(M1/M2/M3) GPU
    else:
        return torch.device('cpu')  # 일반 CPU

DEVICE = get_device()
BATCH_SIZE = 8         # 노트북 메모리 부족하면 4로 줄이세요
LEARNING_RATE = 0.001
EPOCHS = 5

print(f"✅ 현재 사용 중인 장치: {DEVICE}")

# ==========================================
# 2. 데이터셋 클래스
# ==========================================
class BrainMRIDataset(Dataset):
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.image_paths = []
        self.mask_paths = []

        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if 'mask' not in filename and filename.endswith('.tif'):
                    img_path = os.path.join(dirpath, filename)
                    mask_path = os.path.join(dirpath, filename.replace('.tif', '_mask.tif'))
                    if os.path.exists(mask_path):
                        self.image_paths.append(img_path)
                        self.mask_paths.append(mask_path)

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        image = cv2.imread(self.image_paths[idx])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(self.mask_paths[idx], 0)

        image = cv2.resize(image, (256, 256))
        mask = cv2.resize(mask, (256, 256))

        image = image / 255.0
        mask = mask / 255.0

        image = torch.from_numpy(image).permute(2, 0, 1).float()
        mask = torch.from_numpy(mask).unsqueeze(0).float()

        return image, mask

# ==========================================
# 3. U-Net 모델
# ==========================================
class UNet(nn.Module):
    def __init__(self):
        super(UNet, self).__init__()
        self.enc1 = self.conv_block(3, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)
        self.bottleneck = self.conv_block(512, 1024)
        self.up4 = self.up_conv(1024, 512)
        self.dec4 = self.conv_block(1024, 512)
        self.up3 = self.up_conv(512, 256)
        self.dec3 = self.conv_block(512, 256)
        self.up2 = self.up_conv(256, 128)
        self.dec2 = self.conv_block(256, 128)
        self.up1 = self.up_conv(128, 64)
        self.dec1 = self.conv_block(128, 64)
        self.final = nn.Conv2d(64, 1, kernel_size=1)

    def conv_block(self, in_c, out_c):
        return nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True)
        )

    def up_conv(self, in_c, out_c):
        return nn.ConvTranspose2d(in_c, out_c, kernel_size=2, stride=2)

    def forward(self, x):
        e1 = self.enc1(x)
        p1 = F.max_pool2d(e1, 2)
        e2 = self.enc2(p1)
        p2 = F.max_pool2d(e2, 2)
        e3 = self.enc3(p2)
        p3 = F.max_pool2d(e3, 2)
        e4 = self.enc4(p3)
        p4 = F.max_pool2d(e4, 2)
        b = self.bottleneck(p4)
        d4 = self.up4(b)
        d4 = torch.cat((e4, d4), dim=1)
        d4 = self.dec4(d4)
        d3 = self.up3(d4)
        d3 = torch.cat((e3, d3), dim=1)
        d3 = self.dec3(d3)
        d2 = self.up2(d3)
        d2 = torch.cat((e2, d2), dim=1)
        d2 = self.dec2(d2)
        d1 = self.up1(d2)
        d1 = torch.cat((e1, d1), dim=1)
        d1 = self.dec1(d1)
        return self.final(d1)

# ==========================================
# 4. 실행 부 (메인 함수)
# ==========================================
if __name__ == '__main__':
    # 데이터 경로 (상대 경로)
    dataset_path = './dataset/kaggle_3m'
    
    if not os.path.exists(dataset_path):
        print(f"❌ 오류: '{dataset_path}' 폴더를 찾을 수 없습니다.")
        print("dataset 폴더 안에 kaggle_3m 폴더를 넣어주세요.")
    else:
        dataset = BrainMRIDataset(dataset_path)
        # 윈도우에서는 num_workers=0 으로 해야 에러가 안 납니다.
        train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
        
        print(f"✅ 데이터 로드 완료: 총 {len(dataset)}장")
        
        model = UNet().to(DEVICE)
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
        criterion = nn.BCEWithLogitsLoss()

        print("🚀 학습을 시작합니다... (종료하려면 Ctrl+C)")
        
        for epoch in range(EPOCHS):
            model.train()
            epoch_loss = 0
            
            for i, (images, masks) in enumerate(train_loader):
                images = images.to(DEVICE)
                masks = masks.to(DEVICE)

                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, masks)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                
                # 진행상황 표시 (너무 조용하면 답답하니까)
                if (i+1) % 10 == 0:
                    print(f"  > Epoch {epoch+1} - Step [{i+1}/{len(train_loader)}] Loss: {loss.item():.4f}")

            print(f"🎉 Epoch [{epoch+1}/{EPOCHS}] 평균 Loss: {epoch_loss/len(train_loader):.4f}")

        # 모델 저장
        torch.save(model.state_dict(), 'unet_brain_mri_local.pth')
        print("✅ 학습 끝! 모델이 'unet_brain_mri_local.pth'로 저장되었습니다.")
        
        # 결과 확인 (시각화)
        # (학습 끝나면 창이 하나 뜹니다)
        model.eval()
        img, mask = dataset[50] # 50번째 이미지 테스트
        input_tensor = img.unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            pred = model(input_tensor)
            pred = torch.sigmoid(pred).squeeze().cpu().numpy()
            
        plt.figure(figsize=(10, 4))
        plt.subplot(1,3,1); plt.title("MRI"); plt.imshow(img.permute(1,2,0)); plt.axis('off')
        plt.subplot(1,3,2); plt.title("True"); plt.imshow(mask.squeeze(), cmap='gray'); plt.axis('off')
        plt.subplot(1,3,3); plt.title("AI Predict"); plt.imshow(pred > 0.5, cmap='gray'); plt.axis('off')
        plt.show()