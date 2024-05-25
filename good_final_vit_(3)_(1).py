# -*- coding: utf-8 -*-
"""Good_Final_ViT_(3)_(1).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1k8oa9UjyLqlS9Y5oGC3riiZuzV6PcwGx
"""

from google.colab import drive
drive.mount('/content/drive')

!pip install torchvision --upgrade

!pip install timm



!pip install transformers

from sklearn.model_selection import StratifiedKFold
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms
import timm
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_fscore_support, roc_curve, auc
import optuna

# Set the path to your dataset
data_dir = '/content/drive/MyDrive/combined_dataset'

# Set the device for training
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# Define the transforms for training, validation, and testing data
data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'validation': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'test': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# Define class labels
class_labels = {'Defective': 1, 'Non Defective': 0}

# Load the entire dataset
entire_dataset = datasets.ImageFolder(data_dir, transform=data_transforms['train'])

# Update class_to_idx attribute of the dataset to reflect the new labels
entire_dataset.class_to_idx = class_labels


# Confirm class labels
print(entire_dataset.classes)

# Check if the "Defective" class is labeled as 1 and "Non Defective" as 0
print(entire_dataset.class_to_idx)
# Calculate sizes for training, validation, and test splits
train_size = int(0.7 * len(entire_dataset))
validation_size = (len(entire_dataset) - train_size) // 2
test_size = len(entire_dataset) - train_size - validation_size

# Perform the random split
train_dataset, validation_dataset, test_dataset = random_split(entire_dataset, [train_size, validation_size, test_size])

# Update the transforms for validation and test datasets
validation_dataset.dataset.transform = data_transforms['validation']
test_dataset.dataset.transform = data_transforms['test']

# Get the number of classes in the dataset
num_classes = len(entire_dataset.classes)

# Create the model
from sklearn.metrics import recall_score
val_loader = DataLoader(validation_dataset, batch_size=32, shuffle=False, num_workers=1)

# Create the study
study = optuna.create_study(direction='maximize')

def objective(trial, val_loader):
    # Hyperparameters to tune
    lr = trial.suggest_float("lr", 1e-5, 1e-1, log=True)
    momentum = trial.suggest_float("momentum", 0.5, 0.99)
    dropout_rate = trial.suggest_float("dropout_rate", 0.1, 0.5)

    # Model setup
    def create_model(dropout_rate):
        model = timm.create_model('vit_base_patch16_224', pretrained=True)
        num_features = model.head.in_features
        model.head = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(num_features, num_classes)
        )
        return model.to(device)

    model = create_model(dropout_rate)
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentum)
    criterion = nn.CrossEntropyLoss()

    # Training loop (simplified for demonstration)
    # Implement cross-validation setup or a single training/validation split
    # Placeholder training function (to be replaced with actual training logic)
    train_loss = np.random.rand()  # Placeholder for demonstration

    # Evaluate the model on validation data and calculate recall
    model.eval()
    all_val_preds = []
    all_val_labels = []
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_val_preds.extend(preds.cpu().numpy())
            all_val_labels.extend(labels.cpu().numpy())
    val_recall = recall_score(all_val_labels, all_val_preds)

    # Return the recall value
    return val_recall


# Define the loss function
criterion = nn.CrossEntropyLoss()

def compute_metrics(targets, predictions):
    precision, recall, f1, _ = precision_recall_fscore_support(targets, predictions, average='weighted')

    return precision, recall, f1



def create_model(dropout_rate):
    model = timm.create_model('vit_base_patch16_224', pretrained=True)
    num_features = model.head.in_features
    model.head = nn.Sequential(
        nn.Dropout(dropout_rate),
        nn.Linear(num_features, num_classes)
    )
    return model.to(device)


# Train the model with Stratified KFold cross-validation
def stratified_kfold_train_model(num_epochs=8, k=10):
    all_train_losses = []
    all_train_accuracies = []
    all_val_losses = []
    all_val_accuracies = []
    all_train_precisions = []
    all_train_recalls = []
    all_train_f1s = []
    all_val_precisions = []
    all_val_recalls = []
    all_val_f1s = []

    # Collecting values for ROC curve
    all_train_true_labels = []
    all_train_predicted_probs = []
    all_val_true_labels = []
    all_val_predicted_probs = []

    # Convert labels to numpy array
    labels_array = np.array(entire_dataset.targets)

    skf = StratifiedKFold(n_splits=k, shuffle=True)

    for fold, (train_indices, val_indices) in enumerate(skf.split(np.zeros(len(labels_array)), labels_array)):
        train_sampler = torch.utils.data.SubsetRandomSampler(train_indices)
        val_sampler = torch.utils.data.SubsetRandomSampler(val_indices)

        train_loader = DataLoader(entire_dataset, batch_size=32, sampler=train_sampler, num_workers=1)
        val_loader = DataLoader(entire_dataset, batch_size=32, sampler=val_sampler, num_workers=1)

        # Use the best parameters obtained from optimization
        model = create_model(best_dropout_rate)

        optimizer = optim.SGD(model.parameters(), lr=best_lr, momentum=best_momentum, weight_decay=0.01)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min') # Learning rate scheduler


        val_losses = []  # Initialize val_losses list
        val_accuracies = []  # Initialize val_accuracies list
        val_precisions = []  # Initialize val_precisions list
        val_recalls = []  # Initialize val_recalls list
        val_f1s = []  # Initialize val_f1s list

        train_losses = []  # Initialize train_losses list
        train_accuracies = []  # Initialize train_accuracies list
        train_precisions = []  # Initialize train_precisions list
        train_recalls = []  # Initialize train_recalls list
        train_f1s = []  # Initialize train_f1s list

        for epoch in range(num_epochs):
            # Train
            model.train()
            running_loss = 0.0
            running_corrects = 0
            all_train_preds = []
            all_train_labels = []

            for inputs, labels in train_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                with torch.set_grad_enabled(True):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    loss.backward()
                    optimizer.step()
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data).item()
                all_train_preds.extend(preds.cpu().numpy())
                all_train_labels.extend(labels.cpu().numpy())

                # Collect predicted probabilities and true labels for training ROC curve
                sm = nn.Softmax(dim=1)
                probabilities = sm(outputs)
                all_train_true_labels.extend(labels.cpu().numpy())
                all_train_predicted_probs.extend(probabilities.detach().cpu().numpy())

            train_loss = running_loss / len(train_loader.sampler)
            train_acc = running_corrects / len(train_loader.sampler)
            train_precision, train_recall, train_f1 = compute_metrics(all_train_labels, all_train_preds)

            train_losses.append(train_loss)
            train_accuracies.append(train_acc)
            train_precisions.append(train_precision)
            train_recalls.append(train_recall)
            train_f1s.append(train_f1)

            # Validation
            model.eval()
            running_loss = 0.0
            running_corrects = 0
            all_val_preds = []
            all_val_labels = []

            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                with torch.set_grad_enabled(False):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data).item()
                all_val_preds.extend(preds.cpu().numpy())
                all_val_labels.extend(labels.cpu().numpy())

                # Collect predicted probabilities and true labels for validation ROC curve
                sm = nn.Softmax(dim=1)
                probabilities = sm(outputs)
                all_val_true_labels.extend(labels.cpu().numpy())
                all_val_predicted_probs.extend(probabilities.detach().cpu().numpy())

            val_loss = running_loss / len(val_loader.sampler)
            scheduler.step(val_loss)
            val_acc = running_corrects / len(val_loader.sampler)
            val_precision, val_recall, val_f1 = compute_metrics(all_val_labels, all_val_preds)

            val_losses.append(val_loss)
            val_accuracies.append(val_acc)
            val_precisions.append(val_precision)
            val_recalls.append(val_recall)
            val_f1s.append(val_f1)

            print(f"Epoch {epoch+1}/{num_epochs} - "
                  f"Train Loss: {train_loss:.4f} Train Acc: {train_acc:.4f} Train Precision: {train_precision:.4f} "
                  f"Train Recall: {train_recall:.4f} Train F1: {train_f1:.4f} - "
                  f"Val Loss: {val_loss:.4f} Val Acc: {val_acc:.4f} Val Precision: {val_precision:.4f} "
                  f"Val Recall: {val_recall:.4f} Val F1: {val_f1:.4f}")

        # Append the training metrics to the lists
        all_train_losses.append(train_losses)
        all_train_accuracies.append(train_accuracies)
        all_train_precisions.append(train_precisions)
        all_train_recalls.append(train_recalls)
        all_train_f1s.append(train_f1s)

        # Append the validation metrics to the lists
        all_val_losses.append(val_losses)
        all_val_accuracies.append(val_accuracies)
        all_val_precisions.append(val_precisions)
        all_val_recalls.append(val_recalls)
        all_val_f1s.append(val_f1s)

        print('-' * 10)

    # Average loss and accuracy values across all folds
    avg_train_losses = np.mean(all_train_losses, axis=0)
    avg_train_accuracies = np.mean(all_train_accuracies, axis=0)
    avg_train_precisions = np.mean(all_train_precisions, axis=0)
    avg_train_recalls = np.mean(all_train_recalls, axis=0)
    avg_train_f1s = np.mean(all_train_f1s, axis=0)
    avg_val_losses = np.mean(all_val_losses, axis=0)
    avg_val_accuracies = np.mean(all_val_accuracies, axis=0)
    avg_val_precisions = np.mean(all_val_precisions, axis=0)
    avg_val_recalls = np.mean(all_val_recalls, axis=0)
    avg_val_f1s = np.mean(all_val_f1s, axis=0)

    # Compute ROC curve and AUC for training and validation sets
    train_fpr, train_tpr, _ = roc_curve(all_train_true_labels, np.array(all_train_predicted_probs)[:, 1])
    train_roc_auc = auc(train_fpr, train_tpr)

    val_fpr, val_tpr, _ = roc_curve(all_val_true_labels, np.array(all_val_predicted_probs)[:, 1])
    val_roc_auc = auc(val_fpr, val_tpr)

    # Plotting
    plt.figure(figsize=(20, 10))

    # Loss subplot
    plt.subplot(2, 3, 1)
    plt.plot(avg_train_losses, '-o', label='Training Loss')
    plt.plot(avg_val_losses, '-o', label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Average Training and Validation Loss across folds')

    # Accuracy subplot
    plt.subplot(2, 3, 2)
    plt.plot(avg_train_accuracies, '-o', label='Training Accuracy')
    plt.plot(avg_val_accuracies, '-o', label='Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.title('Average Training and Validation Accuracy across folds')

    # Precision subplot
    plt.subplot(2, 3, 3)
    plt.plot(avg_train_precisions, '-o', label='Training Precision')
    plt.plot(avg_val_precisions, '-o', label='Validation Precision')
    plt.xlabel('Epochs')
    plt.ylabel('Precision')
    plt.legend()
    plt.title('Average Training and Validation Precision across folds')

    # Recall subplot
    plt.subplot(2, 3, 4)
    plt.plot(avg_train_recalls, '-o', label='Training Recall')
    plt.plot(avg_val_recalls, '-o', label='Validation Recall')
    plt.xlabel('Epochs')
    plt.ylabel('Recall')
    plt.legend()
    plt.title('Average Training and Validation Recall across folds')

    # F1 Score subplot
    plt.subplot(2, 3, 5)
    plt.plot(avg_train_f1s, '-o', label='Training F1 Score')
    plt.plot(avg_val_f1s, '-o', label='Validation F1 Score')
    plt.xlabel('Epochs')
    plt.ylabel('F1 Score')
    plt.legend()
    plt.title('Average Training and Validation F1 Score across folds')

    # ROC Curve subplot
    plt.subplot(2, 3, 6)
    plt.plot(train_fpr, train_tpr, color='darkorange', lw=2, label='Train ROC curve (area = %0.2f)' % train_roc_auc)
    plt.plot(val_fpr, val_tpr, color='blue', lw=2, label='Validation ROC curve (area = %0.2f)' % val_roc_auc)
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")

    plt.tight_layout()
    plt.show()

study.optimize(lambda trial: objective(trial, val_loader), n_trials=10)
 # Perform 100 trials

# Get the top 10 trials
top_trials = study.trials[:2]

# Calculate average of the top 10 trials' parameters
avg_params = {
    'lr': np.mean([trial.params['lr'] for trial in top_trials]),
    'momentum': np.mean([trial.params['momentum'] for trial in top_trials]),
    'dropout_rate': np.mean([trial.params['dropout_rate'] for trial in top_trials])
}

# Print the average parameters
print("Average parameters from top 10 trials:")
print(avg_params)

# Set the best parameters
best_lr = avg_params['lr']
best_momentum = avg_params['momentum']
best_dropout_rate = avg_params['dropout_rate']

# Continue with training and plotting
num_epochs = 7
stratified_kfold_train_model(num_epochs=num_epochs, k=10)

