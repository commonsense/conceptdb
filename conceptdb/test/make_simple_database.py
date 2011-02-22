import conceptdb
from conceptdb.assertion import Assertion, Expression, Sentence
from conceptdb.metadata import Dataset
from conceptdb.justify import Reason

conceptdb.connect_to_mongodb('test')

#clean out whatever was in test before
Assertion.drop_collection()
Dataset.drop_collection()
Expression.drop_collection()
Reason.drop_collection()
Sentence.drop_collection()

#make a new dataset
d = Dataset.make('/data/test', 'en')

#make a couple of assertions
a1 = Assertion.make(d, '/rel/IsA', ['/concept/assertion', '/concept/test'])
a2 = Assertion.make(d, '/rel/IsA', ['/concept/database', '/concept/test'])

#add expressions to them
e1 = a1.make_expression('{0} is a {1}', a1.arguments, d.language)
e2 = a2.make_expression('{0} is a {1}', a2.arguments, d.language)

#connect them to sentences
a1.connect_to_sentence(d, 'This assertion is a test.')
a2.connect_to_sentence(d, 'This database is a test.')

#make a reason for myself
r = Reason.make('/data/test/contributor/elhawk', ['user_factor'], 0.75, True)

#use the reason to vote for assertion a1
ra1 = a1.add_support(['/data/test/contributor/elhawk'])
conf1 = a1.update_confidence()

#use the reason to vote against assertion a2
ra2 = a2.add_oppose(['/data/test/contributor/elhawk'])
conf2 = a2.update_confidence()
