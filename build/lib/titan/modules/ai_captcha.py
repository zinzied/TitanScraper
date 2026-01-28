import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Config
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CHAR_MAP = {c: i for i, c in enumerate(CHARS)}
IDX_MAP = {i: c for i, c in enumerate(CHARS)}
NUM_CLASSES = len(CHARS)
MAX_CAPTCHA_LEN = 6 # Adjust based on target site
IMG_WIDTH = 200
IMG_HEIGHT = 60

class CaptchaDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.image_files = [f for f in os.listdir(root_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_name = self.image_files[idx]
        img_path = os.path.join(self.root_dir, img_name)
        image = Image.open(img_path).convert('RGB')
        
        # Label from filename (e.g., "x7z3.png" -> "x7z3")
        label_str = os.path.splitext(img_name)[0]
        
        # Pad label if short, truncate if long
        if len(label_str) > MAX_CAPTCHA_LEN:
             label_str = label_str[:MAX_CAPTCHA_LEN]
        
        # Convert label to tensor indices
        label_indices = []
        for c in label_str:
            idx = CHAR_MAP.get(c, 0) # Default to 0 if unknown
            label_indices.append(idx)
        
        # Pad with 0 (or specific pad class) if needed - for now simplified
        while len(label_indices) < MAX_CAPTCHA_LEN:
            label_indices.append(0) # Padding
            
        label_tensor = torch.tensor(label_indices, dtype=torch.long)

        if self.transform:
            image = self.transform(image)

        return image, label_tensor

class MultiHeadCaptchaCNN(nn.Module):
    def __init__(self):
        super(MultiHeadCaptchaCNN, self).__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        # Calculate linear input size based on IMG_WIDTH/HEIGHT and pooling
        # 200x60 -> 100x30 -> 50x15 -> 25x7 (approx)
        self.linear_input = 128 * 7 * 25 
        
        self.fc = nn.Linear(self.linear_input, 1024)
        self.drop = nn.Dropout(0.5)
        
        # Multiple output heads, one for each character position
        self.heads = nn.ModuleList([
            nn.Linear(1024, NUM_CLASSES) for _ in range(MAX_CAPTCHA_LEN)
        ])

    def forward(self, x):
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1) # Flatten
        x = self.fc(x)
        x = self.drop(x)
        
        outputs = []
        for head in self.heads:
            outputs.append(head(x))
            
        return torch.stack(outputs, dim=1) # [Batch, Len, Classes]

def get_transform():
    return transforms.Compose([
        transforms.Resize((IMG_HEIGHT, IMG_WIDTH)),
        transforms.ToTensor(),
    ])

def train_model(data_dir, epochs=10, batch_size=32, model_save_path="captcha_model.pth"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on {device}")
    
    transform = get_transform()
    dataset = CaptchaDataset(data_dir, transform=transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    model = MultiHeadCaptchaCNN().to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device) # [Batch, Len]
            
            optimizer.zero_grad()
            outputs = model(images) # [Batch, Len, Classes]
            
            # Compute loss for each character head
            loss = 0
            for i in range(MAX_CAPTCHA_LEN):
                loss += criterion(outputs[:, i, :], labels[:, i])
                
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            
        logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {running_loss/len(dataloader):.4f}")
        
    torch.save(model.state_dict(), model_save_path)
    logger.info(f"Model saved to {model_save_path}")

def predict(model_path, image_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiHeadCaptchaCNN().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    transform = get_transform()
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(image) # [1, Len, Classes]
        predicted_indices = torch.argmax(outputs, dim=2) # [1, Len]
        
    result = ""
    for idx in predicted_indices[0]:
        result += IDX_MAP[idx.item()]
        
    return result
