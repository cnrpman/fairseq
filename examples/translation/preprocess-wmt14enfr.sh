TEXT=data/wmt14_en_fr
python preprocess.py --source-lang en --target-lang fr \
  --trainpref $TEXT/train --validpref $TEXT/valid --testpref $TEXT/test \
  --destdir data-bin/wmt14_en_fr \
  --joined-dictionary