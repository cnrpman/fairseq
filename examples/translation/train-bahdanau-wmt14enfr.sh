mkdir -p checkpoints/bahdanau_lemans_wmt_en_fr
CUDA_VISIBLE_DEVICES=0 python train.py data-bin/lemans-wmt14_en_fr \
  --lr 1.0 --clip-norm 1.0 --optimizer adadelta --batch-size 80 \
  --encoder-max-src-length 52 --decoder-max-tgt-length 52 --skip-invalid-size-inputs-valid-test\
  --criterion cross_entropy \
  --lr-scheduler fixed \
  --arch lstm_bahdanau_wmt_en_fr --save-dir checkpoints/bahdanau_lemans_wmt_en_fr