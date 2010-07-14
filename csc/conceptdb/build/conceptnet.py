from csc.nl import get_nl
from csc.conceptnet.models import Event
from csc.corpus.models import Sentence
from csc import conceptdb
from csc.conceptdb import assertions

#CONCEPT_ROOT = '/concept/lemma/en/conceptnet/4/'
CONTRIBUTOR_ROOT = '/contributor/omcs/'
RELATION_ROOT = '/rel/conceptnet/'
ACTIVITY_ROOT = '/activity/old/'
DATASET = '/data/conceptnet/5/devel'

# sources that do not lead to sentences we should try to parse
BAD_ACTIVITIES = ['unknown', 'nosetests', 'junk', 'commons2_reject', 'is-a cleanup']

def import_sentences():
    sentences = Sentences.objects.filter(language__id='en')
    for sent in sentences:
        activity = sent.activity.name
        if activity in BAD_ACTIVITIES: continue
        if sent.language.id == 'pt': continue # our portuguese is broken
        if sent.language.id == 'zh-hant': continue # start Chinese over
        
        act_reason = ACTIVITY_ROOT+activity.name.replace(' ', '_')
        contrib_reason = CONTRIBUTOR_ROOT+sent.creator.username
        justification = [(act_reason, 1.0), (contrib_reason, 1.0)]
        newsent = assertions.Sentence.make(DATASET, sent.text)
        newsent.add_support(justification)
        newsent.save()

if __name__ == '__main__':
    conceptdb.connect_to_mongodb('conceptnet')
