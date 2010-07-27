from csc.nl import get_nl
from csc.conceptnet.models import Assertion as OldAssertion, RawAssertion, Vote

import conceptdb
from conceptdb.assertion import Assertion
from conceptdb.expression import Expression
from conceptdb.metadata import Dataset, ExternalReason

import logging
log = logging.getLogger('build.conceptnet')
logging.basicConfig(level=logging.DEBUG)

CONCEPT_ROOT = '/concept/lemma/en/conceptnet/4/'
CONTRIBUTOR_ROOT = '/contributor/omcs/'
RELATION_ROOT = '/rel/conceptnet/'
ACTIVITY_ROOT = '/activity/old/'
DATASET_ROOT = '/data/conceptnet/4/'

def import_assertions(lang):
    assertions = OldAssertion.objects.filter(score__gt=0, language__id=lang)[:20]
    for assertion in assertions:
        dataset = Dataset.make(DATASET_ROOT+assertion.language.id,
                               assertion.language.id)
        relation = RELATION_ROOT + assertion.relation.name
        concept_names = [assertion.concept1.text, assertion.concept2.text]
        concepts = [CONCEPT_ROOT+c for c in concept_names]
        votes = Vote.objects.filter(object_id=assertion.id)
        context = None
        if -5 < assertion.frequency < 5:
            context = '/concept/frequency/en/sometimes'
        newassertion = Assertion.make(dataset, relation, concepts,
                                         polarity = assertion.polarity,
                                         context=context)
        
        root = dataset.get_root_reason()
        site = root.derived_reason('/site/omcs')
        raws = assertion.rawassertion_set.all()

        sent_contributors = set()
        for raw in raws:
            if raw.score > 0:
                frametext = raw.frame.text.replace('{1}','{0}').replace('{2}','{1}').replace('{%}','')
                expr = Expression.make(frametext, [raw.surface1.text, raw.surface2.text], assertion.language.id)
                support_votes = raw.votes.filter(vote=1)
                oppose_votes = raw.votes.filter(vote=-1)
                for vote in support_votes:
                    voter = site.derived_reason(CONTRIBUTOR_ROOT+vote.user.username)
                    expr.add_support([voter])
                for vote in oppose_votes:
                    voter = site.derived_reason(CONTRIBUTOR_ROOT+vote.user.username)
                    expr.add_oppose([voter])
                newassertion.add_expression(expr)

                sent = raw.sentence
                if sent.score > 0:
                    activity = sent.activity.name
                    act_reason = site.derived_reason(ACTIVITY_ROOT+activity.replace(' ', '_'))
                    contrib_reason = site.derived_reason(CONTRIBUTOR_ROOT+sent.creator.username)
                    sent_contributors.add(contrib_reason)
                    justification = [act_reason, contrib_reason]
                    newassertion.connect_to_sentence(dataset, sent.text, justification)

        support_votes = assertion.votes.filter(vote=1)
        oppose_votes = assertion.votes.filter(vote=-1)
        for vote in support_votes:
            voter = site.derived_reason(CONTRIBUTOR_ROOT+vote.user.username)
            if voter not in sent_contributors:
                newassertion.add_support([voter])
        for vote in oppose_votes:
            voter = site.derived_reason(CONTRIBUTOR_ROOT+vote.user.username)
            newassertion.add_oppose([voter])
        newassertion.save()
        log.info(newassertion)


def main():
    conceptdb.connect_to_mongodb('conceptdb')
    import_assertions('en')

if __name__ == '__main__':
    import profile, pstats
    profile.run('main()', 'assertions.profile')
    p = pstats.Stats('assertions.profile')
    p.sort_stats('time').print_stats(50)
