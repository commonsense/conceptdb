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
def import_sentences():
    sentences = Sentence.objects.filter(score__gt=0)[712300:]
    for sent in sentences:
        activity = sent.activity.name
        if activity in BAD_ACTIVITIES: continue
        if sent.language.id == 'pt': continue # our portuguese is broken
        if sent.language.id == 'zh-Hant': continue # start Chinese over
        dataset = Dataset.make(DATASET_ROOT+sent.language.id,
                               sent.language.id)
        root = dataset.get_root_reason()
        site = root.derived_reason('/site/omcs')
        act_reason = site.derived_reason(ACTIVITY_ROOT+activity.replace(' ', '_'))
        contrib_reason = site.derived_reason(CONTRIBUTOR_ROOT+sent.creator.username)
        justification = [act_reason, contrib_reason]
        newsent = assertion.Sentence.make(dataset, sent.text, justification)
        log.info(str(newsent))

if __name__ == '__main__':
    conceptdb.connect_to_mongodb('conceptdb')
    import_sentences()
