import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from music21 import stream, note, chord, instrument,  percussion, converter
from create_generator_model import get_notes, LATENT_DIMENSION, get_off_set,get_notes_from_file
import math
from pathlib import Path
from random import randrange

instr = instrument.Violin()
unpich_SnareDrum = note.Unpitched("B4",instrument=instrument.SnareDrum)
unpich_HiHatCymbal = note.Unpitched("B4",instrument=instrument.HiHatCymbal)
unpich_Percussion = note.Unpitched("B4",instrument=instrument.Percussion)
unpich_CrashCymbals = note.Unpitched("B4",instrument=instrument.CrashCymbals)
unpich_TomTom = note.Unpitched("B4",instrument=instrument.TomTom)
unpich_BassDrum = note.Unpitched("B4",instrument=instrument.BassDrum)

def create_melody(prediction_output,instrumental,off_set,key_index,note_interval = -0):
    offset = 0
    output_notes = []
    for item in prediction_output:
        pattern = item
        if pattern.startswith("Q"):
           offset += float(pattern.replace("Q",""))
        else:
        # pattern is a chord
            offset += max(float(off_set[key_index]) + note_interval,0)
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
                new_chord = percussion.PercussionChord(notes)
                new_chord.offset = offset
                output_notes.append(new_chord)
            elif ('.' in pattern) or pattern.isdigit():
                notes_in_chord = pattern.split('.')
                notes = []
                for current_note in notes_in_chord:
                    new_note = note.Note(int(current_note))
                    new_note.storedInstrument = instrumental
                    notes.append(new_note)
                new_chord = chord.Chord(notes)
                new_chord.offset = offset
                output_notes.append(new_chord)
                # offset += 0.5
        # pattern is a note
            else:
                new_note = note.Note(pattern)
                new_note.offset = offset
                new_note.storedInstrument = instrumental
                output_notes.append(new_note)
            key_index += 1
    midi_stream = stream.Part(output_notes)
    midi_stream.insert(instrumental)
    return midi_stream
def create_melody_from_drums(prediction_output,instrumental,drums):
    offset = 0
    output_notes = []
    for item in range(min(len(drums),len(prediction_output))):
        pattern = prediction_output[item]
        if pattern.startswith("Q"):
           offset += float(pattern.replace("Q",""))
        else:
        # pattern is a chord
            offset = drums[item].offset
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
                new_chord = percussion.PercussionChord(notes)
                new_chord.offset = offset
                output_notes.append(new_chord)
            elif ('.' in pattern) or pattern.isdigit():
                notes_in_chord = pattern.split('.')
                notes = []
                for current_note in notes_in_chord:
                    new_note = note.Note(int(current_note))
                    new_note.storedInstrument = instrumental
                    notes.append(new_note)
                new_chord = chord.Chord(notes)
                new_chord.offset = offset
                output_notes.append(new_chord)
                # offset += 0.5
        # pattern is a note
            else:
                new_note = note.Note(pattern)
                new_note.offset = offset
                new_note.storedInstrument = instrumental
                output_notes.append(new_note)
    midi_stream = stream.Part(output_notes)
    midi_stream.insert(instrumental)
    return midi_stream
def read_drum(drums,index):
    midi = converter.parse(drums[index])
    # offset = 0.0
    notes_to_parse = midi.flat.notes
    # off_set = []
    # for element in notes_to_parse:
    #   off_set.append(f"{float(element.offset-offset)}")
    #   offset = element.offset
    return notes_to_parse
def create_multi_midi(drums,filename):
        # Load the trained generator model
    generator_model = load_model("generator_model-20M-1024.h5")
    
    # Load the processed notes and get the number of unique pitches
    notes = get_notes_from_file()
    n_vocab = len(set(notes))
    # Generate new music sequence
    # length_music = len(drums)
    # print(length_music)
    piano_music = generate_music(generator_model, LATENT_DIMENSION, n_vocab,notes)
    # drum_music = generate_music(generator_model, LATENT_DIMENSION, n_vocab,notes)
    # guitar_music = generate_music(generator_model, LATENT_DIMENSION, n_vocab,notes)
    # bass_music = generate_music(generator_model, LATENT_DIMENSION, n_vocab,notes)
    # violin_music = generate_music(generator_model, LATENT_DIMENSION, n_vocab,notes)

    """ convert the output from the prediction to notes and create a midi file
        from the notes """
    off_set = get_off_set()
    music_range = len(piano_music)
    # create note and chord objects based on the values generated by the model
    i = randrange(len(off_set)-music_range)
    midi_stream = stream.Score()
    midi_stream.insert(create_melody_from_drums(piano_music,instrument.Piano(),drums))
    midi_stream.insert(stream.Part(drums))
    # midi_stream.insert(create_melody(piano_music,instrument.BassDrum(),off_set,i))
    # midi_stream.insert(create_melody(guitar_music,instrument.Guitar(),off_set,i))
    # midi_stream.insert(create_melody(bass_music,instrument.Bass(),off_set,i))
    # midi_stream.insert(create_melody(piano_music,instrument.Guitar(),off_set,i))
    midi_stream.write('midi', fp='{}.mid'.format(filename))
    return True


def generate_music(generator_model, latent_dim, n_vocab, notes, length=500):
    """ Generate new music using the trained generator model """
    # Create random noise as input to the generator
    noise = np.random.normal(0, 1, (1, latent_dim))
    predictions = generator_model.predict(noise)
    
    # Scale back the predictions to the original range
    pred_notes = [x * (n_vocab / 2) + (n_vocab / 2) for x in predictions[0]]
    
    # Map generated integer indices to note names
    pitchnames = sorted(set(item for item in notes))
    int_to_note = dict((number, note) for number, note in enumerate(pitchnames))
    pred_notes_mapped = [int_to_note[int(x)] for x in pred_notes]
    
    return pred_notes_mapped[:length]

if __name__ == '__main__':
    drums = []
    for file in Path("drum").glob("*.mid"):
      drums.append(file)
    drum_midi = read_drum(drums,0)
    # Create a MIDI file from the generated music
    create_multi_midi(drum_midi,"generator-20M-1024-xx")
