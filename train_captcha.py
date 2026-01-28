import argparse
import sys
import os
import logging

# Ensure local import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from titan.modules.ai_captcha import train_model, predict

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="Titan Captcha Trainer")
    parser.add_argument("--mode", type=str, choices=["train", "predict"], required=True, help="Mode: train or predict")
    parser.add_argument("--data_dir", type=str, help="Directory containing labeled captcha images (for training)")
    parser.add_argument("--image", type=str, help="Image path (for prediction)")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--output", type=str, default="captcha_model.pth", help="Path to save/load model")
    
    args = parser.parse_args()
    
    if args.mode == "train":
        if not args.data_dir:
            print("Error: --data_dir is required for training")
            return
        if not os.path.exists(args.data_dir):
            print(f"Error: Data directory '{args.data_dir}' does not exist")
            return
            
        print(f"Starting training on {args.data_dir}...")
        train_model(args.data_dir, epochs=args.epochs, model_save_path=args.output)
        
    elif args.mode == "predict":
        if not args.image:
            print("Error: --image is required for prediction")
            return
        if not os.path.exists(args.output):
            print(f"Error: Model file '{args.output}' not found. Train first.")
            return
            
        text = predict(args.output, args.image)
        print(f"Prediction: {text}")

if __name__ == "__main__":
    main()
