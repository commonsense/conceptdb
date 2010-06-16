from csc import conceptdb
from csc.conceptdb.metadata import Dataset

conceptdb.connect_to_mongodb('test')

def test_dataset():
    dataset = Dataset.create(language='en', name='test/dataset test')
    
    # Make sure it was saved to the database
    assert dataset.id is not None

    # Make sure its attributes are readable
    dataset.language
    dataset.name

    # Clean up by dropping the Dataset collection
    Dataset.drop_collection()

