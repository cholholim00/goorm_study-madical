import torch
import torch.nn as nn
from einops import rearrange

# ==========================================
# 1. 기본 부품 (Conv Block)
# ==========================================
class ConvBlock(nn.Module):
    def __init__(self, in_c, out_c):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

# ==========================================
# 2. 트랜스포머 블록
# ==========================================
class TransformerBlock(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.attention = nn.MultiheadAttention(embed_dim, num_heads)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 4),
            nn.GELU(),
            nn.Linear(embed_dim * 4, embed_dim)
        )
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        attn_out, _ = self.attention(x, x, x)
        x = x + self.norm1(attn_out)
        mlp_out = self.mlp(x)
        x = x + self.norm2(mlp_out)
        return x

# ==========================================
# 3. TransUNet 전체 구조 (버그 수정 완료)
# ==========================================
class TransUNet(nn.Module):
    def __init__(self, img_dim=256, in_channels=3, out_channels=1, head_num=4, block_num=4):
        super().__init__()
        # ---------------------------
        # Encoder (내려가는 길)
        # ---------------------------
        self.enc1 = ConvBlock(in_channels, 64)       # 256x256
        self.pool1 = nn.MaxPool2d(2)                 # 128x128
        
        self.enc2 = ConvBlock(64, 128)               # 128x128
        self.pool2 = nn.MaxPool2d(2)                 # 64x64
        
        self.enc3 = ConvBlock(128, 256)              # 64x64
        self.pool3 = nn.MaxPool2d(2)                 # 32x32

        # ---------------------------
        # Transformer Bottleneck (핵심!)
        # ---------------------------
        self.embedding_dim = 256
        self.transformer_blocks = nn.ModuleList(
            [TransformerBlock(self.embedding_dim, head_num) for _ in range(block_num)]
        )
        
        # ---------------------------
        # Decoder (올라가는 길) - 조각 크기 완벽 일치!
        # ---------------------------
        # Up 3 (32x32 -> 64x64)
        self.up3 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec3 = ConvBlock(256 + 128, 128) # enc3(256) + up3(128) = 384 채널
        
        # Up 2 (64x64 -> 128x128)
        self.up2 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec2 = ConvBlock(128 + 64, 64)   # enc2(128) + up2(64) = 192 채널
        
        # Up 1 (128x128 -> 256x256)
        self.up1 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
        self.dec1 = ConvBlock(64 + 32, 32)    # enc1(64) + up1(32) = 96 채널
        
        self.final = nn.Conv2d(32, out_channels, kernel_size=1)

    def forward(self, x):
        # [Encoder]
        e1 = self.enc1(x)
        p1 = self.pool1(e1)
        
        e2 = self.enc2(p1)
        p2 = self.pool2(e2)
        
        e3 = self.enc3(p2)
        p3 = self.pool3(e3)

        # [Transformer]
        b, c, h, w = p3.shape
        embedding = rearrange(p3, 'b c h w -> (h w) b c')
        for block in self.transformer_blocks:
            embedding = block(embedding)
        encoded = rearrange(embedding, '(h w) b c -> b c h w', h=h, w=w)
        
        # [Decoder & Skip Connection] - 퍼즐 맞추기!
        d3 = self.up3(encoded)
        d3 = torch.cat((e3, d3), dim=1) # 64x64 끼리 결합! (여기서 에러 났던 것 수정)
        d3 = self.dec3(d3)
        
        d2 = self.up2(d3)
        d2 = torch.cat((e2, d2), dim=1) # 128x128 끼리 결합!
        d2 = self.dec2(d2)
        
        d1 = self.up1(d2)
        d1 = torch.cat((e1, d1), dim=1) # 256x256 끼리 결합!
        d1 = self.dec1(d1)
        
        return self.final(d1)