from csc.nl import get_nl
from csc.conceptnet.models import Assertion as OldAssertion, RawAssertion, Vote, User, Activity

import conceptdb
from conceptdb.assertion import Assertion
from conceptdb.expression import Expression
from conceptdb.metadata import Dataset, ExternalReason

import time
import logging
log = logging.getLogger('build.conceptnet')
logging.basicConfig(level=logging.DEBUG)

CONCEPT_ROOT = '/concept/lemma/en/conceptnet/4/'
CONTRIBUTOR_ROOT = '/contributor/omcs/'
RELATION_ROOT = '/rel/conceptnet/'
ACTIVITY_ROOT = '/activity/old/'
DATASET_ROOT = '/data/conceptnet/4/'

def import_contributors(lang):
    dataset = Dataset.make(DATASET_ROOT+lang, lang)
    root = dataset.get_root_reason()
    site = root.derived_reason('/site/omcs', weight=1.0)
    for user in User.objects.iterator():
        voter = site.derived_reason(CONTRIBUTOR_ROOT+user.username, weight=0.5)
        voter.save()
        log.info(voter)

def import_activities(lang):
    dataset = Dataset.make(DATASET_ROOT+lang, lang)
    root = dataset.get_root_reason()
    site = root.derived_reason('/site/omcs', weight=1.0)
    for act in Activity.objects.iterator():
        newact = site.derived_reason(ACTIVITY_ROOT+act.name.replace(' ', '_'), weight=1.0)
        newact.save()
        log.info(newact)

def import_assertions(lang):
    dataset = Dataset.make(DATASET_ROOT+lang, lang)
    root = dataset.get_root_reason()
    site = root.derived_reason('/site/omcs', weight=1.0)
    generalize_reason = root.derived_reason('/rule/generalize', weight=0.1)
    assertions = OldAssertion.objects.filter(score__gt=0, language__id=lang)\
      .select_related('concept1', 'concept2', 'relation', 'language')[27720:]
    for assertion in assertions:
        relation = RELATION_ROOT + assertion.relation.name
        concept_names = [assertion.concept1.text, assertion.concept2.text]
        concepts = [CONCEPT_ROOT+c for c in concept_names]
        votes = Vote.objects.filter(object_id=assertion.id)
        context = None
        if -5 < assertion.frequency < 5:
            context = '/concept/frequency/en/sometimes'
        raws = assertion.rawassertion_set.all().select_related('surface1', 'surface2', 'frame', 'sentence', 'sentence__creator', 'sentence__activity')

        newassertion = Assertion.make(dataset, relation, concepts,
                                         polarity = assertion.polarity,
                                         context=context)
        sent_contributors = set()

        for raw in raws:
            if raw.score > 0:
                frametext = raw.frame.text.replace('{1}','{0}').replace('{2}','{1}').replace('{%}','')
                expr = Expression.make(frametext, [raw.surface1.text, raw.surface2.text], assertion.language.id)
                support_votes = raw.votes.filter(vote=1).select_related('user')
                oppose_votes = raw.votes.filter(vote=-1).select_related('user')
                for vote in support_votes:
                    voter = dataset.get_reason_name(CONTRIBUTOR_ROOT+vote.user.username)
                    expr.add_support([voter])
                for vote in oppose_votes:
                    voter = dataset.get_reason_name(CONTRIBUTOR_ROOT+vote.user.username)
                    expr.add_oppose([voter])
                expr.update_confidence()
                newassertion.add_expression(expr)

                sent = raw.sentence
                if sent.score > 0:
                    activity = sent.activity.name
                    act_reason = dataset.get_reason_name(ACTIVITY_ROOT+activity.replace(' ', '_'))
                    voter = dataset.get_reason_name(CONTRIBUTOR_ROOT+vote.user.username)

                    sent_contributors.add(voter)
                    justification = [act_reason, voter]
                    newassertion.connect_to_sentence(dataset, sent.text, justification)

        support_votes = assertion.votes.filter(vote=1)
        oppose_votes = assertion.votes.filter(vote=-1)
        for vote in support_votes:
            voter = dataset.get_reason_name(CONTRIBUTOR_ROOT+vote.user.username)
            if voter not in sent_contributors:
                newassertion.add_support([voter])
        for vote in oppose_votes:
            voter = dataset.get_reason_name(CONTRIBUTOR_ROOT+vote.user.username)
            newassertion.add_oppose([voter])
        newassertion.update_confidence()
        newassertion.save()
        newassertion.make_generalizations(generalize_reason)
        log.info(newassertion)

def main():
    conceptdb.connect_to_mongodb('conceptdb')
    #import_activities('en')
    #import_contributors('en')
    import_assertions('en')

if __name__ == '__main__':
    #import profile, pstats
    #profile.run('main()', 'assertions.profile')
    #p = pstats.Stats('assertions.profile')
    #p.sort_stats('cumulative').print_stats(50)
    main()
