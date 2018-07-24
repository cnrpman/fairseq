python generate.py data-bin/lemans-wmt14_en_fr  \
  --path checkpoints/bahdanau_lemans_wmt_en_fr/checkpoint_best.pt \
  --skip-invalid-size-inputs-valid-test \
  --beam 12 --batch-size 128 | tee /tmp/gen.out