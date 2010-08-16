from csc.nl import get_nl
from csc.conceptnet.models import Event
from csc.corpus.models import Sentence
import conceptdb
from conceptdb import assertion
from conceptdb.metadata import Dataset, ExternalReason

import logging
log = logging.getLogger('build.sentences')
logging.basicConfig(level=logging.DEBUG)

CONCEPT_ROOT = '/concept/lemma/en/conceptnet/4/'
CONTRIBUTOR_ROOT = '/contributor/omcs/'
RELATION_ROOT = '/rel/conceptnet/'
ACTIVITY_ROOT = '/activity/old/'
DATASET_ROOT = '/data/conceptnet/5/'

BAD_ACTIVITIES = ['unknown', 'nosetests', 'junk', 'commons2_reject', 'is-a cleanup']

def import_sentence(sent):
    dataset = Dataset.make(DATASET_ROOT+sent.language.id,
                           sent.language.id)
    activity = sent.activity.name
    root = dataset.get_root_reason()
    site = root.derived_reason('/site/omcs')
    act_reason = site.derived_reason(ACTIVITY_ROOT+activity.replace(' ', '_'))
    contrib_reason = site.derived_reason(CONTRIBUTOR_ROOT+sent.creator.username)
    justification = [act_reason, contrib_reason]
    newsent = assertion.Sentence.make(dataset, sent.text, justification)
    log.info(str(newsent))

def import_sentences():
    print "importing sentences."
    sentences = Sentence.objects.filter(score__gt=0, language__id='en')
    print len(sentences)
    for sent in sentences:
        activity = sent.activity.name
        if activity in BAD_ACTIVITIES: continue
        import_sentence(sent)

if __name__ == '__main__':
    conceptdb.connect_to_mongodb('conceptdb')
    import_sentences()

