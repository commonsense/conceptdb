ConceptDB aims to be compatible with various Semantic Web resources. This means
its IDs, whenever possible, are URLs (with the domain name unspecified).

In some cases, these URLs help distinguish types of things: for example, root
concepts (/concept), assertions (/assertion), and relations (/rel) can all be
arguments of assertions. A REST API may in fact make the objects available at
the corresponding URLs.

Here's an outline of the namespace as I see it so far:

  /                                 -- root
    activity/
      api/                          -- using the API directly
      game/                         -- playing a game
      old/                          -- an activity we used to track in SQL
        is-a_cleanup                -- example of one of those activities
      web/                          -- using a collaborative website
        
    assertion/                      -- namespace of assertions
      4c3b61b7510f429a60000000      -- a particular assertion, by ID

    concept/                        -- concepts by language
      lemma/                        -- concepts in lemma form
        en/                         -- English concepts
          conceptnet/               -- ConceptNet 4-style lemmas
            4/                      -- ConceptNet 4 lemmas
              dog                   -- the concept "dog"
            5/                      -- ConceptNet 5 lemmas
          wordnet/                  -- WordNet lemmas
            3.0/                    -- WordNet 3.0 lemmas
              dog.n                 -- "dog, as a noun"
        zh-Hant/                    -- Chinese concepts
        ja/                         -- Japanese concepts
      sense/                        -- word senses
        en/                         -- English word senses
          wordnet/                  -- WordNet senses
            3.0/                    -- WordNet 3.0 senses
              dog.n.1               -- "dog, the animal"
    
    data/                           -- namespace of datasets
      conceptnet/
        4/
          4.0                       -- conceptnet 4.0, as released
          master                    -- live database of cnet 4.0
          devel                     -- experimental version
        5/
          master
          devel
      wordnet/
        3.0                         -- import of wordnet 3.0
    
    rel/                            -- namespace of relations
      IsA                           -- {0} is a kind of {1}

