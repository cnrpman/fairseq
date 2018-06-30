TEXT=data/lemans_wmt14_en_fr
python preprocess.py --source-lang en --target-lang fr \
  --trainpref $TEXT/train --validpref $TEXT/valid --testpref $TEXT/test \
  --destdir data-bin/lemans-wmt14_en_fr --nwordssrc 30004 --nwordstgt 30004