import os
import logging
from flair.data import Corpus
from flair.datasets import CSVClassificationCorpus
from flair.embeddings import OneHotEmbeddings, DocumentRNNEmbeddings
from flair.models import TextClassifier
from flair.trainers import ModelTrainer
from flair.data import Dictionary
import warnings
import torch

# Suppress deprecation warnings for cleaner output
warnings.filterwarnings('ignore', category=DeprecationWarning)

def main():
    BATCH_SIZE = 1000000  # Set to a very high number to use all training data in one batch

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)

    # Function to convert the dataset format and filter for Chinese names
    def convert(name_f, nat_f, fout_path):
        with open(fout_path, 'w', encoding='utf8') as fout:
            names = open(name_f, 'r', encoding='utf8').read().strip().splitlines()
            nats = open(nat_f, 'r', encoding='utf8').read().strip().splitlines()
            for name, nat in zip(names, nats):
                if nat == "Chinese":
                    name = name.replace(" ", "▁")
                    name = " ".join(char for char in name)
                    fout.write(f"{name}\t{nat}\n")

        # Debugging: Print number of lines written
        with open(fout_path, 'r', encoding='utf8') as f:
            lines_written = len(f.readlines())
            print(f"Lines written to {fout_path}: {lines_written}")

    # Convert the dataset files and filter for Chinese names
    logging.info("Converting dataset files...")
    convert('train.src', 'train.tgt', 'data/train.txt')
    convert('dev.src', 'dev.tgt', 'data/dev.txt')
    convert('test.src', 'test.tgt', 'data/test.txt')

    # Check if the files are created and contain data
    def check_file(file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf8') as f:
                lines = f.readlines()
                if lines:
                    print(f"File {file_path} is created and contains data.")
                else:
                    print(f"File {file_path} is created but empty.")
        else:
            print(f"File {file_path} does not exist.")

    check_file('data/train.txt')
    check_file('data/dev.txt')
    check_file('data/test.txt')

    # Create a column name map
    column_name_map = {0: "text", 1: "label"}

    # Create a corpus using the CSV files
    logging.info("Reading corpus...")
    corpus = CSVClassificationCorpus(
        'data',
        column_name_map=column_name_map,
        train_file='train.txt',
        test_file='test.txt',
        dev_file='dev.txt',
        label_type='class'
    )

    # Obtain and print corpus statistics
    logging.info("Obtaining corpus statistics...")
    stats = corpus.obtain_statistics()
    print(stats)

    # Create the label dictionary
    logging.info("Creating label dictionary...")
    label_dict = corpus.make_label_dictionary(label_type='class')
    print(label_dict)

    # Create the vocabulary dictionary
    logging.info("Creating vocabulary dictionary...")
    vocab_dictionary = Dictionary.load('chars')

    # Make a list of word embeddings
    embeddings = [OneHotEmbeddings(vocab_dictionary)]

    # Initialize document embedding
    document_embeddings = DocumentRNNEmbeddings(embeddings, bidirectional=True, hidden_size=256)

    # Create the text classifier
    classifier = TextClassifier(document_embeddings, label_dictionary=label_dict, label_type='class')

    # Move the model to the GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    classifier = classifier.to(device)

    # Initialize the text classifier trainer
    trainer = ModelTrainer(classifier, corpus)

    # Start the training
    logging.info("Starting training...")
    try:
        trainer.train(
            'resources/',
            learning_rate=0.1,
            mini_batch_size=BATCH_SIZE,  # Use the entire dataset in one batch
            anneal_factor=0.5,
            patience=5,
            max_epochs=1,  # Set to 1 epoch
            num_workers=0  # Use single worker to avoid multiprocessing issues
        )
    except KeyboardInterrupt:
        logging.info("Training interrupted. Saving the model...")
        trainer.model.save('resources/final-model.pt')
        logging.info("Model saved after interruption.")
        return

    # Save the model after training
    logging.info("Saving the trained model after training...")
    trainer.model.save('resources/final-model.pt')
    logging.info("Model saved after training.")

    # Evaluate the model
    logging.info("Evaluating the model on the test set...")
    result = trainer.test(classifier, corpus.test)
    print(result)

    logging.info("Training complete.")

if __name__ == '__main__':
    main()
