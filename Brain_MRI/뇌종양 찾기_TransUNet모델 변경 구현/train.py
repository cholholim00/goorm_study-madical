import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
# 반드시 transunet.py 파일이 같은 폴더에 있어야 합니다.
from transunet import TransUNet

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
EPOCHS = 10             # TransUNet은 학습이 좀 더 걸릴 수 있습니다 (5~10 추천)

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
# 3. 실행 부 (메인 함수)
# ==========================================
if __name__ == '__main__':
    # 데이터 경로 (상대 경로)
    dataset_path = './dataset/kaggle_3m'
    
    if not os.path.exists(dataset_path):
        print(f"❌ 오류: '{dataset_path}' 폴더를 찾을 수 없습니다.")
        print("dataset 폴더 안에 kaggle_3m 폴더를 넣어주세요.")
    else:
        # 데이터 로드
        dataset = BrainMRIDataset(dataset_path)
        # 윈도우에서는 num_workers=0 필수
        train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
        print(f"✅ 데이터 로드 완료: 총 {len(dataset)}장")
        
        # ==========================================
        # 모델 정의 (TransUNet)
        # ==========================================
        print("🤖 TransUNet 모델을 불러옵니다...")
        model = TransUNet(img_dim=256, in_channels=3, out_channels=1).to(DEVICE)
        
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
                    
                # 진행상황 표시
                if (i+1) % 10 == 0:
                    print(f"  > Epoch {epoch+1} - Step [{i+1}/{len(train_loader)}] Loss: {loss.item():.4f}")

            print(f"🎉 Epoch [{epoch+1}/{EPOCHS}] 평균 Loss: {epoch_loss/len(train_loader):.4f}")
        
        # 모델 저장
        save_name = 'transunet_brain_mri.pth'
        torch.save(model.state_dict(), save_name)
        print(f"✅ 학습 끝! 모델이 '{save_name}'로 저장되었습니다.")
        
        # ==========================================
        # 결과 확인 (시각화)
        # ==========================================
        model.eval()
        # 랜덤하게 하나 뽑아서 확인 (매번 다른거 보게)
        import random
        idx = random.randint(0, len(dataset)-1)
        
        img, mask = dataset[idx] 
        input_tensor = img.unsqueeze(0).to(DEVICE)
            
        with torch.no_grad():
            pred = model(input_tensor)
            pred = torch.sigmoid(pred).squeeze().cpu().numpy()
            
        plt.figure(figsize=(10, 4))
        plt.subplot(1,3,1); plt.title("MRI"); plt.imshow(img.permute(1,2,0)); plt.axis('off')
        plt.subplot(1,3,2); plt.title("True"); plt.imshow(mask.squeeze(), cmap='gray'); plt.axis('off')
        plt.subplot(1,3,3); plt.title("TransUNet Predict"); plt.imshow(pred > 0.5, cmap='gray'); plt.axis('off')
        plt.show()