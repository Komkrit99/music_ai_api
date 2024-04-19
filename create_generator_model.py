import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Reshape, Dropout, LSTM, Bidirectional
from tensorflow.keras.layers import BatchNormalization, LeakyReLU
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from music21 import converter, instrument, note, chord, stream, percussion
from pathlib import Path
import matplotlib.pyplot as plt
import math
from random import randrange

SEQUENCE_LENGTH = 100
LATENT_DIMENSION = 1000
BATCH_SIZE = 16
EPOCHS = 100
SAMPLE_INTERVAL = 1

unpich_SnareDrum = note.Note("D2",instrument=instrument.SnareDrum)
# unpich_SnareDrum.storedInstrument = instrument.SnareDrum
unpich_HiHatCymbal = note.Note("F#2",instrument=instrument.HiHatCymbal)
# unpich_HiHatCymbal.storedInstrument = instrument.HiHatCymbal
unpich_Percussion = note.Note("A#0",instrument=instrument.Percussion)
# unpich_Percussion.storedInstrument = instrument.Percussion
unpich_CrashCymbals = note.Note("D#3",instrument=instrument.CrashCymbals)
# unpich_CrashCymbals.storedInstrument = instrument.CrashCymbals
unpich_TomTom = note.Note("E2",instrument=instrument.TomTom)
# unpich_TomTom.storedInstrument = instrument.TomTom
unpich_BassDrum = note.Note("C2",instrument=instrument.BassDrum)
# unpich_BassDrum.storedInstrument = instrument.BassDrum

def get_notes():
    """ Get all the notes and chords from the midi files """
    notes = []
    notes_2 = []
    drum = []
    for file in Path("drum").glob("*.mid"):
        try:
            midi = converter.parse(file)

            print("Parsing %s" % file)
            offset = 0.0
            notes_to_parse = midi.flat.notes
            off_set = []
            for element in notes_to_parse:
                if isinstance(element, note.Rest):
                    notes.append('R')
                    notes_2.append('R')
                if isinstance(element, note.Note):
                    notes.append(f"{str(element.pitch)}")
                    notes_2.append(f"{str(element.pitch)}")
                elif isinstance(element, chord.Chord):
                    notes.append('.'.join(str(n) for n in element.normalOrder))
                    notes_2.append(f"{str(element.pitches[0])}")
                elif isinstance(element, percussion.PercussionChord ):
                   drum.append('D.'+'.'.join(str(n.getInstrument()) for n in element.notes))
                elif isinstance(element,note.Unpitched):
                    drum.append('D.'+str(element.getInstrument()))
                off_set.append(f"{float(element.offset-offset)}")
                offset = element.offset
        except:
            continue
    with open(r'note-1-test.txt', 'w') as fp:
        fp.write(','.join(str(n) for n in notes))
    with open(r'note-2-test.txt', 'w') as fp:
        fp.write(','.join(str(n) for n in notes_2))
    with open(r'off_set-1-test.txt', 'w') as fp:
        fp.write(','.join(str(n) for n in off_set))
    with open(r'drum-1.txt', 'w') as fp:
        fp.write(','.join(str(n) for n in drum))
    return notes

def get_notes_from_file():
    f = open("note-5.txt", "r")
    notes = f.read().split(",")
    # new_notes = []
    # for a in notes:
    #   if "." in a:
    #     new_notes.append(a.split(".")[0])
    #   else:
    #     new_notes.append(a)
    # notes = notes[:5000000]
    print(len(notes))
    return notes

def get_off_set():
    f = open("off_set-1.txt", "r")
    offset = f.read().split(",")
    return offset
def prepare_sequences(notes, n_vocab):
    """ Prepare the sequences used by the Neural Network """
    sequence_length = 100

    # Get  pitch names
    pitchnames = sorted(set(item for item in notes))

    # Create a dictionary to map pitches to integers
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    network_input = []
    network_output = []

    # create input sequences and the corresponding outputs
    for i in range(0, len(notes) - sequence_length, 1):
        sequence_in = notes[i:i + sequence_length]
        sequence_out = notes[i + sequence_length]
        network_input.append([note_to_int[char] for char in sequence_in])
        network_output.append(note_to_int[sequence_out])

    n_patterns = len(network_input)
    # Reshape the input into a format compatible with LSTM layers
    network_input = np.reshape(network_input, (n_patterns, sequence_length, 1))
    
    # Normalize input between -1 and 1
    network_input = (network_input - float(n_vocab) / 2) / (float(n_vocab) / 2)
    network_output = to_categorical(network_output, num_classes=n_vocab)  # Use to_categorical from TensorFlow's Keras

    return network_input, network_output  # Add this return statement

  
def create_midi(prediction_output, filename):
    """ convert the output from the prediction to notes and create a midi file
        from the notes """
    offset = 0
    output_notes = []
    off_set = get_off_set()
    # create note and chord objects based on the values generated by the model
    i = randrange(len(off_set)-len(prediction_output))
    for item in prediction_output:
        pattern = item
        if pattern.startswith("Q"):
           offset += float(pattern.replace("Q",""))
        else:
        # pattern is a chord
            # offset += float(off_set[i])
            offset += 0.5
            if pattern == 'R':
                    output_notes.append(note.Rest())
            elif pattern.startswith("D."):
                note_in_set = pattern.split(".")
                notes = []
                for instrument_name in note_in_set:
                  if instrument_name == 'Snare Drum':
                    notes.append(unpich_SnareDrum)
                  elif instrument_name == 'Hi-Hat Cymbal':
                    notes.append(unpich_HiHatCymbal)
                  elif instrument_name == 'Percussion':
                    notes.append(unpich_Percussion)
                  elif instrument_name == 'Crash Cymbals':
                    notes.append(unpich_CrashCymbals)
                  elif instrument_name == 'Tom-Tom':
                    notes.append(unpich_TomTom)
                  elif instrument_name == 'Bass Drum':
                    notes.append(unpich_BassDrum)
                  elif instrument_name != 'D':
                    print(instrument_name)
                new_chord = chord.Chord(notes)
                new_chord.offset = offset
                output_notes.append(new_chord)
            elif ('.' in pattern) or pattern.isdigit():
                notes_in_chord = pattern.split('.')
                notes = []
                for current_note in notes_in_chord:
                    new_note = note.Note(int(current_note))
                    new_note.storedInstrument = instrument.Piano()
                    notes.append(new_note)
                new_chord = chord.Chord(notes)
                new_chord.offset = offset
                output_notes.append(new_chord)
        # pattern is a note
            else:
                new_note = note.Note(pattern,quarterLength = float(off_set[i]))
                new_note.offset = offset
                new_note.storedInstrument = instrument.Piano()
                output_notes.append(new_note)
            i += 1
    midi_stream = stream.Stream(output_notes)
    midi_stream.write('midi', fp='{}.mid'.format(filename))

class GAN():
    def __init__(self, rows):
        self.seq_length = rows
        self.seq_shape = (self.seq_length, 1)
        self.latent_dim = 1000
        self.disc_loss = []
        self.gen_loss =[]
        
        optimizer = Adam(0.0002, 0.5)

        # Build and compile the discriminator
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

        # Build the generator
        self.generator = self.build_generator()

        # The generator takes noise as input and generates note sequences
        z = Input(shape=(self.latent_dim,))
        generated_seq = self.generator(z)

        # For the combined model we will only train the generator
        self.discriminator.trainable = False

        # The discriminator takes generated images as input and determines validity
        validity = self.discriminator(generated_seq)

        # The combined model  (stacked generator and discriminator)
        # Trains the generator to fool the discriminator
        self.combined = Model(z, validity)
        self.combined.compile(loss='binary_crossentropy', optimizer=optimizer)

    def build_discriminator(self):
        model = Sequential()
        model.add(LSTM(512, input_shape=self.seq_shape, return_sequences=True))
        model.add(Bidirectional(LSTM(512)))
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        
        # Adding Minibatch Discrimination
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.5))
        model.add(Dense(1, activation='sigmoid'))
        model.summary()

        seq = Input(shape=self.seq_shape)
        validity = model(seq)

        return Model(seq, validity)
      
    def build_generator(self):

        model = Sequential()
        model.add(Dense(512, input_dim=self.latent_dim))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(np.prod(self.seq_shape), activation='tanh'))
        model.add(Reshape(self.seq_shape))
        model.summary()
        
        noise = Input(shape=(self.latent_dim,))
        seq = model(noise)

        return Model(noise, seq)

    def train(self, epochs, batch_size=128, sample_interval=50):

        # Load and convert the data
        # get_notes()
        notes = get_notes_from_file()
        n_vocab = len(set(notes))
        X_train, y_train = prepare_sequences(notes, n_vocab)

        # Adversarial ground truths
        real = np.ones((batch_size, 1))
        fake = np.zeros((batch_size, 1))
        
        # Training the model
        for epoch in range(epochs):

            # Training the discriminator
            # Select a random batch of note sequences
            idx = np.random.randint(0, X_train.shape[0], batch_size)
            real_seqs = X_train[idx]

            #noise = np.random.choice(range(484), (batch_size, self.latent_dim))
            #noise = (noise-242)/242
            noise = np.random.normal(0, 1, (batch_size, self.latent_dim))

            # Generate a batch of new note sequences
            gen_seqs = self.generator.predict(noise)

            # Train the discriminator
            d_loss_real = self.discriminator.train_on_batch(real_seqs, real)
            d_loss_fake = self.discriminator.train_on_batch(gen_seqs, fake)
            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)


            #  Training the Generator
            noise = np.random.normal(0, 1, (batch_size, self.latent_dim))

            # Train the generator (to have the discriminator label samples as real)
            g_loss = self.combined.train_on_batch(noise, real)

            # Print the progress and save into loss lists
            if epoch % sample_interval == 0:
                print ("%d [D loss: %f, acc.: %.2f%%] [G loss: %f]" % (epoch, d_loss[0], 100*d_loss[1], g_loss))
                self.disc_loss.append(d_loss[0])
                self.gen_loss.append(g_loss)
        
        self.generate(notes)
        self.plot_loss()
        
    def generate(self, input_notes):
        # Get pitch names and store in a dictionary
        notes = input_notes
        pitchnames = sorted(set(item for item in notes))
        int_to_note = dict((number, note) for number, note in enumerate(pitchnames))
        
        # Use random noise to generate sequences
        noise = np.random.normal(0, 1, (1, self.latent_dim))
        predictions = self.generator.predict(noise)
        
        pred_notes = [x*242+242 for x in predictions[0]]
        
        # Map generated integer indices to note names, with error handling
        pred_notes_mapped = []
        for x in pred_notes:
            index = int(x)
            if index in int_to_note:
                pred_notes_mapped.append(int_to_note[index])
            else:
                # Fallback mechanism: Choose a default note when the index is out of range
                pred_notes_mapped.append('R')  # You can choose any default note here
        create_midi(pred_notes_mapped, 'gan_final-5M-512-adams')

        
    def plot_loss(self):
        plt.plot(self.disc_loss, c='red')
        plt.plot(self.gen_loss, c='blue')
        plt.title("GAN Loss per Epoch")
        plt.legend(['Discriminator', 'Generator'])
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.savefig('GAN_Loss_per_Epoch_final-5M-512-adam.png', transparent=True)
        plt.close()

if __name__ == '__main__':
    gan = GAN(rows=SEQUENCE_LENGTH)    
    gan.train(epochs=EPOCHS, batch_size=BATCH_SIZE, sample_interval=SAMPLE_INTERVAL)

    # Save the generator and discriminator models
    gan.generator.save("generator_model-5M-512-adam.h5")
    gan.discriminator.save("discriminator_model-5M-512-adam.h5")