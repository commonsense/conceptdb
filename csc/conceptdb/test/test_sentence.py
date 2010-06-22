from csc.conceptdb.metadata import Dataset
from csc import conceptdb
from csc.conceptdb.assertions import Sentence

conceptdb.connect_to_mongodb('test')

def test_sentence():

    dataset = Dataset.create(language='en', name='test/dataset test')
    
    #create test sentence with dataset
    sentence1 = Sentence.make('test/dataset test', "This is a test sentence.")

    #check it was saved to the database
    assert sentence1.id is not None

    #make sure its attributes are readable
    sentence1.text
    sentence1.words
    sentence1.dataset
    sentence1.justification
    sentence1.derived_assertions

    #make the same sentence, this time using dataset object instead of string
    sentence2 = Sentence.make(dataset, "This is a test sentence.")

    #check that it was saved to the database
    assert sentence2.id is not None

    #check that sentence1 and sentence2 have the same ID
    assert (sentence1.id == sentence2.id)
    
    #check that its attributes are readable
    sentence2.text
    sentence2.words
    sentence2.dataset
    sentence2.justification
    sentence2.derived_assertions

    #make a different sentence
    sentence3 = Sentence.make('test/dataset test', "This is a different test sentence.");
    
    #make sure it exists in the database and is different
    assert sentence3.id is not None
    assert sentence3.id is not sentence1.id
    assert sentence3.id is not sentence2.id

    #make sure its attributes are readable
    sentence3.text
    sentence3.words
    sentence3.dataset
    sentence3.justification
    sentence3.derived_assertions

    #clean up by dropping collections
    Dataset.drop_collection()
    Sentence.drop_collection()


