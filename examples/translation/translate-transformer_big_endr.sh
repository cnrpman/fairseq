python generate.py data-bin/wmt14.en-fr.joined-dict.newstest2014 \
  --path checkpoints/wmt14.en-fr.joined-dict.transformer/model.pt \
  --batch-size 128 --quiet --beam 5 --remove-bpe --lenpen 0.6